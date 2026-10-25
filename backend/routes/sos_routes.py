"""
sos_routes.py
=============
API endpoints for:
1. SOS Contacts Management (Onboarding, CRUD, E.164 validation, primary flag)
2. Emergency SOS Event Triggering (Coordinates capture, Twilio/Mock notification dispatch)
3. Emergency Event Resolution ("I'm Safe", All-clear notifications)
4. Live Location Sharing (1-hour active tracking)
5. Admin Real-Time SOS Monitoring (SSE stream and polling endpoints)
"""

import json
import time
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, g, Response, stream_with_context
from database import db
from models.user import User
from models.sos_contact import SOSContact
from models.sos_event import SOSEvent
from models.user_location import UserLocation
from services.auth_service import login_required, decode_token
from services.notification_service import notification_service, format_e164

sos_bp = Blueprint("sos", __name__, url_prefix="/api")

# In-memory queue for SSE broadcasting of new SOS events to admin
_admin_sse_listeners = []


def get_current_user_from_req():
    """Extract authenticated user from Bearer header or cookie."""
    token = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
    elif "access_token" in request.cookies:
        token = request.cookies.get("access_token")

    if not token:
        return None

    payload = decode_token(token)
    if not payload:
        return None

    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        return None

    return db.session.get(User, user_id)


# =========================================================================== #
# ONBOARDING & CONTACTS MANAGEMENT
# =========================================================================== #

@sos_bp.route("/user/onboarding-status", methods=["GET"])
def get_onboarding_status():
    """
    Check if the authenticated user has completed mandatory SOS onboarding.
    Returns whether at least 1 contact is configured and the contact list.
    """
    user = get_current_user_from_req()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    contacts = SOSContact.query.filter_by(user_id=user.id).order_by(SOSContact.is_primary.desc(), SOSContact.id.asc()).all()
    has_contacts = len(contacts) > 0

    return jsonify({
        "success": True,
        "onboarding_completed": has_contacts,
        "has_sos_contacts": has_contacts,
        "contact_count": len(contacts),
        "contacts": [c.to_dict() for c in contacts],
    }), 200


@sos_bp.route("/user/sos-contacts", methods=["GET"])
def list_contacts():
    """List all SOS emergency contacts for current user."""
    user = get_current_user_from_req()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    contacts = SOSContact.query.filter_by(user_id=user.id).order_by(SOSContact.is_primary.desc(), SOSContact.id.asc()).all()
    return jsonify({
        "success": True,
        "count": len(contacts),
        "contacts": [c.to_dict() for c in contacts]
    }), 200


@sos_bp.route("/user/sos-contacts", methods=["POST"])
def add_contact():
    """
    Add an SOS contact (minimum 1, maximum 5 per user).
    Validates E.164 / Indian phone numbers.
    """
    user = get_current_user_from_req()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    current_count = SOSContact.query.filter_by(user_id=user.id).count()
    if current_count >= 5:
        return jsonify({
            "success": False,
            "error": "Maximum limit reached. You can have a maximum of 5 emergency SOS contacts."
        }), 400

    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip()
    relationship = (data.get("relationship") or data.get("relation") or "Family").strip()
    is_primary = bool(data.get("is_primary", False))

    if not name:
        return jsonify({"success": False, "error": "Contact name is required."}), 400

    is_valid, formatted_phone, err_msg = format_e164(phone)
    if not is_valid:
        return jsonify({"success": False, "error": err_msg or "Invalid phone number format."}), 400

    # If this is the first contact or marked as primary, make it primary
    if current_count == 0:
        is_primary = True

    if is_primary:
        # Clear existing primary flag for user's other contacts
        SOSContact.query.filter_by(user_id=user.id).update({"is_primary": False})

    new_contact = SOSContact(
        user_id=user.id,
        name=name,
        phone=formatted_phone,
        relationship=relationship,
        is_primary=is_primary
    )
    db.session.add(new_contact)
    db.session.commit()

    all_contacts = SOSContact.query.filter_by(user_id=user.id).order_by(SOSContact.is_primary.desc(), SOSContact.id.asc()).all()
    return jsonify({
        "success": True,
        "message": f"Emergency contact '{name}' added successfully.",
        "contact": new_contact.to_dict(),
        "contacts": [c.to_dict() for c in all_contacts]
    }), 201


@sos_bp.route("/user/sos-contacts/bulk", methods=["POST"])
def bulk_save_contacts():
    """
    Bulk save 1-5 contacts at once (typically used during first-time onboarding).
    Replaces or establishes initial contacts.
    """
    user = get_current_user_from_req()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json() or {}
    contact_list = data.get("contacts") or []

    if not isinstance(contact_list, list) or len(contact_list) < 1:
        return jsonify({"success": False, "error": "At least 1 emergency contact is required to complete onboarding."}), 400

    if len(contact_list) > 5:
        return jsonify({"success": False, "error": "You can add a maximum of 5 emergency contacts."}), 400

    # Validate all contacts first
    validated_entries = []
    has_primary = False

    for idx, item in enumerate(contact_list):
        c_name = (item.get("name") or "").strip()
        c_phone = (item.get("phone") or "").strip()
        c_rel = (item.get("relationship") or item.get("relation") or "Family").strip()
        c_primary = bool(item.get("is_primary", False))

        if not c_name:
            return jsonify({"success": False, "error": f"Contact #{idx + 1} name is missing."}), 400

        is_valid, formatted_phone, err_msg = format_e164(c_phone)
        if not is_valid:
            return jsonify({"success": False, "error": f"Contact '{c_name}': {err_msg}"}), 400

        if c_primary and not has_primary:
            has_primary = True
        elif c_primary and has_primary:
            c_primary = False  # Only one primary

        validated_entries.append({
            "name": c_name,
            "phone": formatted_phone,
            "relationship": c_rel,
            "is_primary": c_primary
        })

    # If no primary was explicitly chosen, mark the first one as primary
    if not has_primary and len(validated_entries) > 0:
        validated_entries[0]["is_primary"] = True

    # Clear old contacts and insert fresh list
    SOSContact.query.filter_by(user_id=user.id).delete()

    created_objects = []
    for entry in validated_entries:
        c_obj = SOSContact(
            user_id=user.id,
            name=entry["name"],
            phone=entry["phone"],
            relationship=entry["relationship"],
            is_primary=entry["is_primary"]
        )
        db.session.add(c_obj)
        created_objects.append(c_obj)

    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Successfully configured {len(created_objects)} emergency contacts.",
        "contacts": [c.to_dict() for c in created_objects]
    }), 200


@sos_bp.route("/user/sos-contacts/<int:contact_id>", methods=["PUT"])
def update_contact(contact_id):
    """Update contact details or primary flag."""
    user = get_current_user_from_req()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    contact = SOSContact.query.filter_by(id=contact_id, user_id=user.id).first()
    if not contact:
        return jsonify({"success": False, "error": "Contact not found."}), 404

    data = request.get_json() or {}
    if "name" in data:
        name = (data["name"] or "").strip()
        if not name:
            return jsonify({"success": False, "error": "Name cannot be empty."}), 400
        contact.name = name

    if "phone" in data:
        phone = (data["phone"] or "").strip()
        is_valid, formatted_phone, err_msg = format_e164(phone)
        if not is_valid:
            return jsonify({"success": False, "error": err_msg}), 400
        contact.phone = formatted_phone

    if "relationship" in data:
        contact.relationship = (data["relationship"] or "Family").strip()

    if "is_primary" in data and bool(data["is_primary"]):
        SOSContact.query.filter_by(user_id=user.id).update({"is_primary": False})
        contact.is_primary = True

    db.session.commit()
    all_contacts = SOSContact.query.filter_by(user_id=user.id).order_by(SOSContact.is_primary.desc(), SOSContact.id.asc()).all()

    return jsonify({
        "success": True,
        "message": "Contact updated successfully.",
        "contact": contact.to_dict(),
        "contacts": [c.to_dict() for c in all_contacts]
    }), 200


@sos_bp.route("/user/sos-contacts/<int:contact_id>", methods=["DELETE"])
def delete_contact(contact_id):
    """
    Delete an SOS contact.
    Enforces minimum 1 contact remaining requirement.
    """
    user = get_current_user_from_req()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    contact = SOSContact.query.filter_by(id=contact_id, user_id=user.id).first()
    if not contact:
        return jsonify({"success": False, "error": "Contact not found."}), 404

    total_count = SOSContact.query.filter_by(user_id=user.id).count()
    if total_count <= 1:
        return jsonify({
            "success": False,
            "error": "You must keep at least 1 emergency SOS contact for safety. Add a replacement before deleting this contact."
        }), 400

    was_primary = contact.is_primary
    db.session.delete(contact)
    db.session.commit()

    # If deleted was primary, assign primary to first remaining contact
    if was_primary:
        first_rem = SOSContact.query.filter_by(user_id=user.id).first()
        if first_rem:
            first_rem.is_primary = True
            db.session.commit()

    all_contacts = SOSContact.query.filter_by(user_id=user.id).order_by(SOSContact.is_primary.desc(), SOSContact.id.asc()).all()
    return jsonify({
        "success": True,
        "message": "Contact removed successfully.",
        "contacts": [c.to_dict() for c in all_contacts]
    }), 200


@sos_bp.route("/user/sos-contacts/<int:contact_id>/test", methods=["POST"])
def send_test_contact_message(contact_id):
    """
    POST /api/user/sos-contacts/<id>/test
    Send a test emergency notification message to a specific contact to verify delivery.
    """
    user = get_current_user_from_req()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    contact = SOSContact.query.filter_by(id=contact_id, user_id=user.id).first()
    if not contact:
        return jsonify({"success": False, "error": "Emergency contact not found."}), 404

    user_name = user.name or "CrimeSense User"
    res = notification_service.send_test_message(
        recipient_phone=contact.phone,
        recipient_name=contact.name,
        user_name=user_name,
        channel="sms"
    )

    return jsonify({
        "success": True,
        "message": f"Test message dispatched to {contact.name} ({contact.phone}).",
        "result": res,
        "contact": contact.to_dict()
    }), 200


# =========================================================================== #
# EMERGENCY SOS TRIGGERING & RESOLUTION
# =========================================================================== #

@sos_bp.route("/user/sos-events/trigger", methods=["POST"])
def trigger_sos():
    """
    Trigger emergency SOS distress signal.
    1. Records SOSEvent with coordinates & zone.
    2. Broadcasts notifications to all configured emergency contacts via NotificationService.
    3. Notifies admin monitoring in real time.
    """
    user = get_current_user_from_req()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json() or {}
    lat = data.get("latitude")
    lng = data.get("longitude")
    accuracy = data.get("accuracy")
    zone = (data.get("zone") or "unknown").lower()
    event_type = data.get("type", "manual")

    if lat is None or lng is None:
        return jsonify({
            "success": False,
            "error": "Valid GPS coordinates (latitude and longitude) are required to trigger an SOS alert."
        }), 400

    try:
        lat = float(lat)
        lng = float(lng)
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid coordinates format."}), 400

    # Fetch user emergency contacts
    contacts = SOSContact.query.filter_by(user_id=user.id).all()
    user_name = user.name or "CrimeSense User"
    now = datetime.utcnow()

    # 1. Create SOSEvent record
    sos_event = SOSEvent(
        user_id=user.id,
        type=event_type,
        latitude=lat,
        longitude=lng,
        accuracy=float(accuracy) if accuracy is not None else None,
        zone=zone,
        status="active",
        created_at=now,
        live_tracking_until=now + timedelta(hours=1)
    )
    db.session.add(sos_event)
    db.session.commit()

    # Also log to user_locations for timeline history
    loc_entry = UserLocation(
        user_id=user.id,
        latitude=lat,
        longitude=lng,
        accuracy=float(accuracy) if accuracy is not None else None,
        zone=zone,
        recorded_at=now
    )
    db.session.add(loc_entry)
    db.session.commit()

    # 2. Dispatch notifications to all emergency contacts
    delivery_results = []
    for c in contacts:
        res = notification_service.send_sos_alert(
            recipient_phone=c.phone,
            recipient_name=c.name,
            user_name=user_name,
            latitude=lat,
            longitude=lng,
            zone_name=zone,
            event_time=now,
            channel="sms"
        )
        delivery_results.append({
            "contact_id": c.id,
            "contact_name": c.name,
            "contact_phone": c.phone,
            "relationship": c.relationship,
            "is_primary": c.is_primary,
            "status": res.get("status", "sent"),
            "provider": res.get("provider", "mock"),
            "timestamp": now.isoformat()
        })

    sos_event.contacts_notified = delivery_results
    db.session.commit()

    event_payload = sos_event.to_dict()

    # 3. Broadcast to real-time admin stream
    for listener in list(_admin_sse_listeners):
        try:
            listener(event_payload)
        except Exception:
            pass

    return jsonify({
        "success": True,
        "message": f"SOS Alert Activated! Notified {len(contacts)} emergency contacts.",
        "event": event_payload,
        "contacts_notified": delivery_results,
    }), 201


@sos_bp.route("/user/sos-events/active", methods=["GET"])
def get_active_sos():
    """Retrieve current user's active SOS event if one is underway."""
    user = get_current_user_from_req()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    active_event = SOSEvent.query.filter_by(user_id=user.id, status="active").order_by(SOSEvent.id.desc()).first()
    if not active_event:
        return jsonify({"success": True, "active": False, "event": None}), 200

    return jsonify({
        "success": True,
        "active": True,
        "event": active_event.to_dict()
    }), 200


@sos_bp.route("/user/sos-events/<int:event_id>/resolve", methods=["POST"])
def resolve_sos(event_id):
    """
    Resolve active SOS event ('I am safe').
    1. Sets status to 'resolved' and records resolved_at.
    2. Sends all-clear SMS/WhatsApp to emergency contacts.
    3. Notifies admin monitoring.
    """
    user = get_current_user_from_req()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    event = SOSEvent.query.filter_by(id=event_id, user_id=user.id).first()
    if not event:
        return jsonify({"success": False, "error": "SOS event not found."}), 404

    now = datetime.utcnow()
    event.status = "resolved"
    event.resolved_at = now
    db.session.commit()

    # Send all-clear notification to contacts
    contacts = SOSContact.query.filter_by(user_id=user.id).all()
    user_name = user.name or "CrimeSense User"
    resolved_results = []

    for c in contacts:
        res = notification_service.send_sos_resolved(
            recipient_phone=c.phone,
            recipient_name=c.name,
            user_name=user_name,
            resolved_time=now,
            channel="sms"
        )
        resolved_results.append({
            "contact_name": c.name,
            "contact_phone": c.phone,
            "status": res.get("status", "delivered")
        })

    event_payload = event.to_dict()

    for listener in list(_admin_sse_listeners):
        try:
            listener(event_payload)
        except Exception:
            pass

    return jsonify({
        "success": True,
        "message": "Distress signal resolved. All-clear notification sent to contacts.",
        "event": event_payload,
        "notifications": resolved_results
    }), 200


@sos_bp.route("/user/sos-events/<int:event_id>/live-location", methods=["POST"])
def update_live_sos_location(event_id):
    """
    Receive ongoing GPS tracking pings for an active SOS event.
    Extends live coordinates for up to 1 hour.
    """
    user = get_current_user_from_req()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    event = SOSEvent.query.filter_by(id=event_id, user_id=user.id, status="active").first()
    if not event:
        return jsonify({"success": False, "error": "No active SOS event found."}), 404

    data = request.get_json() or {}
    lat = data.get("latitude")
    lng = data.get("longitude")
    accuracy = data.get("accuracy")
    zone = data.get("zone")

    if lat is not None and lng is not None:
        event.latitude = float(lat)
        event.longitude = float(lng)
        if accuracy is not None:
            event.accuracy = float(accuracy)
        if zone:
            event.zone = str(zone).lower()

        # Record in user locations table
        loc_entry = UserLocation(
            user_id=user.id,
            latitude=float(lat),
            longitude=float(lng),
            accuracy=float(accuracy) if accuracy is not None else None,
            zone=event.zone,
            recorded_at=datetime.utcnow()
        )
        db.session.add(loc_entry)
        db.session.commit()

    return jsonify({
        "success": True,
        "event": event.to_dict()
    }), 200


@sos_bp.route("/user/sos-events/<int:event_id>/extend-tracking", methods=["POST"])
def extend_live_tracking(event_id):
    """Explicitly enable/extend live location sharing for 1 hour."""
    user = get_current_user_from_req()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    event = SOSEvent.query.filter_by(id=event_id, user_id=user.id).first()
    if not event:
        return jsonify({"success": False, "error": "SOS event not found."}), 404

    now = datetime.utcnow()
    event.live_tracking_until = now + timedelta(hours=1)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Live location sharing active for 1 hour.",
        "live_tracking_until": event.live_tracking_until.isoformat()
    }), 200


# =========================================================================== #
# ADMIN SOS MONITORING (REAL-TIME POLLING & SSE)
# =========================================================================== #

@sos_bp.route("/admin/sos-events", methods=["GET"])
def admin_list_sos_events():
    """
    Admin endpoint to view all SOS distress events (active & historical).
    Supports query param ?status=active or ?limit=50.
    """
    status_filter = request.args.get("status")
    limit = int(request.args.get("limit", 50))

    query = SOSEvent.query.order_by(SOSEvent.created_at.desc())
    if status_filter and status_filter.lower() != "all":
        query = query.filter_by(status=status_filter.lower())

    events = query.limit(limit).all()
    active_count = SOSEvent.query.filter_by(status="active").count()

    return jsonify({
        "success": True,
        "count": len(events),
        "active_count": active_count,
        "events": [e.to_dict() for e in events]
    }), 200


# =========================================================================== #
# RED ZONE INACTIVITY MONITORING & HEARTBEAT
# =========================================================================== #

from models.user_red_zone_state import UserRedZoneState
from models.user_settings import UserSettings
from services.red_zone_scheduler import evaluate_user_state, calculate_distance_m


@sos_bp.route("/user/heartbeat", methods=["POST"])
def record_heartbeat():
    """
    POST /api/user/heartbeat
    Client heartbeat sent every 30s while app is open and location sharing is active.
    Payload: { latitude, longitude, accuracy, zone, timestamp, has_interaction }
    """
    user = get_current_user_from_req()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json() or {}
    lat = data.get("latitude")
    lng = data.get("longitude")
    accuracy = data.get("accuracy")
    zone = (data.get("zone") or "green").lower()
    has_interaction = bool(data.get("has_interaction", False))
    now = datetime.utcnow()

    if lat is None or lng is None:
        return jsonify({"success": False, "error": "latitude and longitude required"}), 400

    lat = float(lat)
    lng = float(lng)

    # Fetch or create UserRedZoneState
    rz_state = UserRedZoneState.query.filter_by(user_id=user.id).first()
    if not rz_state:
        rz_state = UserRedZoneState(
            user_id=user.id,
            state="SAFE",
            zone=zone,
            latitude=lat,
            longitude=lng,
            accuracy=float(accuracy) if accuracy is not None else None,
            last_heartbeat_at=now,
            last_interaction_at=now
        )
        db.session.add(rz_state)
        db.session.commit()

    # Check physical movement (> 30 meters)
    distance_moved = 0.0
    if rz_state.latitude is not None and rz_state.longitude is not None:
        distance_moved = calculate_distance_m(rz_state.latitude, rz_state.longitude, lat, lng)

    is_active_movement = distance_moved > 30.0
    if has_interaction or is_active_movement:
        rz_state.last_interaction_at = now

    # Update position and heartbeat
    rz_state.latitude = lat
    rz_state.longitude = lng
    if accuracy is not None:
        rz_state.accuracy = float(accuracy)
    rz_state.zone = zone
    rz_state.last_heartbeat_at = now
    rz_state.is_stale_heartbeat = False

    # Also log to user_locations if user has sharing enabled
    settings = UserSettings.query.filter_by(user_id=user.id).first()
    if settings and settings.location_sharing_enabled:
        loc_entry = UserLocation(
            user_id=user.id,
            latitude=lat,
            longitude=lng,
            accuracy=float(accuracy) if accuracy is not None else None,
            zone=zone,
            recorded_at=now
        )
        db.session.add(loc_entry)

    db.session.commit()

    # Evaluate state machine transition
    eval_res = evaluate_user_state(user.id, now)

    return jsonify({
        "success": True,
        "state": rz_state.state,
        "zone": rz_state.zone,
        "distance_moved_m": round(distance_moved, 1),
        "warning_active": rz_state.state == "WARNING",
        "seconds_remaining": rz_state.to_dict().get("seconds_remaining", 0),
        "eval_result": eval_res,
    }), 200


@sos_bp.route("/user/safety-status", methods=["GET"])
def get_safety_status():
    """
    GET /api/user/safety-status
    Poll current user's Red Zone safety state, warning status, and countdown.
    """
    user = get_current_user_from_req()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    if os.getenv("ENABLE_SIMULATOR", "false").lower() == "true" and user.id in _simulated_user_states:
        sim = _simulated_user_states[user.id]
        return jsonify({
            "success": True,
            "state": sim.get("state", "SAFE"),
            "warning_active": sim.get("warning_active", False),
            "seconds_remaining": sim.get("seconds_remaining", 0),
            "details": sim
        }), 200

    rz_state = UserRedZoneState.query.filter_by(user_id=user.id).first()
    if not rz_state:
        return jsonify({
            "success": True,
            "state": "SAFE",
            "warning_active": False,
            "seconds_remaining": 0,
            "details": None
        }), 200

    # Evaluate tick if in warning state
    if rz_state.state == "WARNING":
        evaluate_user_state(user.id)
        db.session.refresh(rz_state)

    state_dict = rz_state.to_dict()
    return jsonify({
        "success": True,
        "state": rz_state.state,
        "warning_active": rz_state.state == "WARNING",
        "seconds_remaining": state_dict.get("seconds_remaining", 0),
        "details": state_dict
    }), 200


@sos_bp.route("/user/safety-checkin", methods=["POST"])
def user_safety_checkin():
    """
    POST /api/user/safety-checkin
    User responds "I'm Safe" to the inactivity warning prompt.
    Resets state and aborts pending auto SOS trigger.
    """
    user = get_current_user_from_req()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    now = datetime.utcnow()
    rz_state = UserRedZoneState.query.filter_by(user_id=user.id).first()
    if not rz_state:
        return jsonify({"success": True, "message": "Safety acknowledged."}), 200

    rz_state.last_interaction_at = now
    rz_state.warning_prompt_sent_at = None
    rz_state.warning_expires_at = None

    if rz_state.zone == "red":
        rz_state.state = "IN_RED"
    else:
        rz_state.state = "SAFE"

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Safety check-in confirmed! Inactivity timer reset.",
        "state": rz_state.state
    }), 200


@sos_bp.route("/user/push-subscription", methods=["POST"])
def save_push_subscription():
    """
    POST /api/user/push-subscription
    Register Web Push (VAPID) browser subscription for 'Are you safe?' prompts.
    """
    user = get_current_user_from_req()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json() or {}
    sub_data = data.get("subscription")

    rz_state = UserRedZoneState.query.filter_by(user_id=user.id).first()
    if not rz_state:
        rz_state = UserRedZoneState(user_id=user.id)
        db.session.add(rz_state)

    rz_state.push_subscription = sub_data
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Push notification subscription saved."
    }), 200


# =========================================================================== #
# DEV-MODE SIMULATOR ENDPOINTS (Disabled by default; strictly in-memory)
# =========================================================================== #

_simulated_user_states = {}


@sos_bp.route("/dev/simulate-red-zone", methods=["POST"])
def simulate_red_zone():
    """
    POST /api/dev/simulate-red-zone
    Dev-mode simulator endpoint enabled ONLY when ENABLE_SIMULATOR=true.
    Maintains simulated states strictly in-memory to prevent writing fake records
    into production tables.
    """
    if os.getenv("ENABLE_SIMULATOR", "false").lower() != "true":
        return jsonify({
            "success": False,
            "error": "Movement simulator is disabled. Set ENABLE_SIMULATOR=true in backend environment to enable dev simulations."
        }), 403

    user = get_current_user_from_req()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json() or {}
    action = data.get("action", "enter_red")
    threshold_min = int(data.get("threshold_minutes", 1))

    sim_state = _simulated_user_states.get(user.id, {
        "user_id": user.id,
        "state": "SAFE",
        "zone": "green",
        "seconds_remaining": 0,
        "warning_active": False,
        "latitude": None,
        "longitude": None,
    })

    msg = ""

    if action == "enter_red":
        sim_state["zone"] = "red"
        sim_state["state"] = "IN_RED"
        sim_state["latitude"] = 12.9806
        sim_state["longitude"] = 79.1368
        sim_state["warning_active"] = False
        sim_state["seconds_remaining"] = 0
        msg = "Simulated user entering high-risk RED zone (in-memory dev state)."

    elif action == "simulate_inactivity":
        sim_state["zone"] = "red"
        sim_state["state"] = "WARNING"
        sim_state["warning_active"] = True
        sim_state["seconds_remaining"] = 60
        msg = f"Simulated {threshold_min} min of stationary inactivity. State transitioned to WARNING (in-memory)."

    elif action == "trigger_warning":
        sim_state["zone"] = "red"
        sim_state["state"] = "WARNING"
        sim_state["warning_active"] = True
        sim_state["seconds_remaining"] = 60
        msg = "Warning prompt 'Are you safe?' active with 60s countdown (in-memory)."

    elif action == "simulate_timeout":
        sim_state["zone"] = "red"
        sim_state["state"] = "AUTO_ALERT_SENT"
        sim_state["warning_active"] = False
        sim_state["seconds_remaining"] = 0
        msg = "Simulated 60-second timeout. Auto SOS alert simulated (no DB tables modified)."

    elif action == "reset":
        sim_state["zone"] = "green"
        sim_state["state"] = "SAFE"
        sim_state["warning_active"] = False
        sim_state["seconds_remaining"] = 0
        if user.id in _simulated_user_states:
            del _simulated_user_states[user.id]
        msg = "Reset simulated safety state to SAFE."

    if action != "reset":
        _simulated_user_states[user.id] = sim_state

    return jsonify({
        "success": True,
        "action": action,
        "message": msg,
        "state": sim_state
    }), 200

