"""
user_routes.py
==============
Endpoints for user location tracking, live sharing updates, and settings.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify, g
from database import db
from models.user import User
from models.user_location import UserLocation
from models.user_settings import UserSettings
from services.auth_service import decode_token

user_bp = Blueprint("user", __name__, url_prefix="/api/user")


def get_current_user_optional():
    """Extract authenticated user if valid token is provided, else None."""
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


@user_bp.route("/location", methods=["POST"])
def record_location():
    """
    POST /api/user/location
    Record throttled GPS updates (lat, lng, accuracy, zone).
    Saves to user_locations if user is authenticated and location sharing is active.
    """
    data = request.get_json() or {}
    lat = data.get("latitude")
    lng = data.get("longitude")
    accuracy = data.get("accuracy")
    zone = (data.get("zone") or "green").lower()

    if lat is None or lng is None:
        return jsonify({"success": False, "error": "latitude and longitude required"}), 400

    user = get_current_user_optional()
    if not user:
        # Anonymous user tracking (acknowledged without persisting user link)
        return jsonify({
            "success": True,
            "saved": False,
            "message": "Location acknowledged for anonymous session"
        }), 200

    # Check user settings
    settings = UserSettings.query.filter_by(user_id=user.id).first()
    if not settings:
        settings = UserSettings(user_id=user.id, location_sharing_enabled=True)
        db.session.add(settings)
        db.session.commit()

    if settings.location_sharing_enabled:
        location_entry = UserLocation(
            user_id=user.id,
            latitude=float(lat),
            longitude=float(lng),
            accuracy=float(accuracy) if accuracy is not None else None,
            zone=zone,
            recorded_at=datetime.utcnow()
        )
        db.session.add(location_entry)
        db.session.commit()

        # Run 30-day retention cleanup
        UserLocation.cleanup_old_records(days=30)

        return jsonify({
            "success": True,
            "saved": True,
            "data": location_entry.to_dict()
        }), 201

    return jsonify({
        "success": True,
        "saved": False,
        "message": "Location sharing is disabled in user settings"
    }), 200


@user_bp.route("/settings", methods=["GET"])
def get_settings():
    """GET /api/user/settings"""
    user = get_current_user_optional()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    settings = UserSettings.query.filter_by(user_id=user.id).first()
    if not settings:
        settings = UserSettings(user_id=user.id)
        db.session.add(settings)
        db.session.commit()

    return jsonify({"success": True, "settings": settings.to_dict()}), 200


@user_bp.route("/settings", methods=["POST", "PUT"])
def update_settings():
    """POST /api/user/settings"""
    user = get_current_user_optional()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json() or {}
    settings = UserSettings.query.filter_by(user_id=user.id).first()
    if not settings:
        settings = UserSettings(user_id=user.id)
        db.session.add(settings)

    if "location_sharing_enabled" in data:
        settings.location_sharing_enabled = bool(data["location_sharing_enabled"])
    if "red_zone_alert_enabled" in data:
        settings.red_zone_alert_enabled = bool(data["red_zone_alert_enabled"])
    if "alert_radius_m" in data:
        settings.alert_radius_m = int(data["alert_radius_m"])
    if "inactivity_minutes" in data:
        settings.inactivity_minutes = int(data["inactivity_minutes"])
    if "share_live_location_with_admin" in data:
        settings.share_live_location_with_admin = bool(data["share_live_location_with_admin"])

    db.session.commit()
    return jsonify({"success": True, "settings": settings.to_dict()}), 200


@user_bp.route("/profile", methods=["PUT"])
def update_profile():
    """
    PUT /api/user/profile
    Update user name and avatar.
    """
    user = get_current_user_optional()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json() or {}
    if "name" in data:
        name = (data["name"] or "").strip()
        if not name:
            return jsonify({"success": False, "error": "Name cannot be empty"}), 400
        user.name = name

    if "avatar_url" in data:
        user.avatar_url = data["avatar_url"]

    db.session.commit()
    return jsonify({
        "success": True,
        "message": "Profile updated successfully.",
        "user": user.to_dict()
    }), 200


@user_bp.route("/locations", methods=["DELETE"])
def delete_location_history():
    """
    DELETE /api/user/locations
    Delete all stored GPS tracking entries for the authenticated user.
    """
    user = get_current_user_optional()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    deleted_count = UserLocation.query.filter_by(user_id=user.id).delete()
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Successfully deleted {deleted_count} location history records.",
        "deleted_count": deleted_count
    }), 200


@user_bp.route("/account", methods=["DELETE"])
def delete_account():
    """
    DELETE /api/user/account
    Permanently delete the user's account and all associated personal data:
    - User location history
    - SOS contacts
    - SOS events
    - Saved places
    - Shareable token links
    - User settings
    - Red zone state
    - User record
    """
    user = get_current_user_optional()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    # Import related models to ensure clean cascade purge
    from models.sos_contact import SOSContact
    from models.sos_event import SOSEvent
    from models.saved_location import SavedLocation
    from models.shared_link import SharedLink
    from models.user_red_zone_state import UserRedZoneState

    user_id = user.id

    try:
        # Delete dependent entities
        UserLocation.query.filter_by(user_id=user_id).delete()
        UserSettings.query.filter_by(user_id=user_id).delete()
        SOSContact.query.filter_by(user_id=user_id).delete()
        SOSEvent.query.filter_by(user_id=user_id).delete()
        SavedLocation.query.filter_by(user_id=user_id).delete()
        SharedLink.query.filter_by(user_id=user_id).delete()
        UserRedZoneState.query.filter_by(user_id=user_id).delete()

        # Delete user
        db.session.delete(user)
        db.session.commit()

        response = jsonify({
            "success": True,
            "message": "Account and all associated personal data permanently deleted."
        })
        response.delete_cookie("access_token")
        return response, 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": f"Failed to delete account: {str(e)}"
        }), 500


# =========================================================================== #
# SAVED PLACES / DESTINATIONS MANAGEMENT
# =========================================================================== #

from models.saved_location import SavedLocation
from services.zone_service import calculate_zone_risk


@user_bp.route("/saved-locations", methods=["GET"])
def get_saved_locations():
    """
    GET /api/user/saved-locations
    Returns list of saved places. Re-evaluates risk zones live on load.
    Pinned items appear first.
    """
    user = get_current_user_optional()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    re_eval = request.args.get("re_evaluate", "true").lower() != "false"
    saved_list = SavedLocation.query.filter_by(user_id=user.id).order_by(
        SavedLocation.is_pinned.desc(),
        SavedLocation.created_at.desc()
    ).all()

    results = []
    now = datetime.utcnow()

    for item in saved_list:
        if re_eval:
            try:
                risk = calculate_zone_risk(item.latitude, item.longitude, radius=1000)
                item.zone = (risk.get("zone") or "GREEN").lower()
                item.last_checked_at = now
            except Exception:
                pass

        results.append(item.to_dict())

    if re_eval:
        db.session.commit()

    return jsonify({
        "success": True,
        "count": len(results),
        "locations": results
    }), 200


@user_bp.route("/saved-locations", methods=["POST"])
def add_saved_location():
    """
    POST /api/user/saved-locations
    Save a new destination with custom label, address, coords, and optional pin.
    """
    user = get_current_user_optional()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json() or {}
    label = (data.get("label") or "Saved Place").strip()
    address = (data.get("address") or "").strip()
    lat = data.get("latitude") or data.get("lat")
    lng = data.get("longitude") or data.get("lng")
    is_pinned = bool(data.get("is_pinned", False))

    if lat is None or lng is None:
        return jsonify({"success": False, "error": "latitude and longitude required"}), 400

    try:
        lat = float(lat)
        lng = float(lng)
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Invalid coordinates"}), 400

    # Calculate initial zone
    initial_zone = "green"
    try:
        risk = calculate_zone_risk(lat, lng, radius=1000)
        initial_zone = (risk.get("zone") or "GREEN").lower()
    except Exception:
        pass

    new_loc = SavedLocation(
        user_id=user.id,
        label=label,
        address=address or f"{lat:.4f}, {lng:.4f}",
        latitude=lat,
        longitude=lng,
        zone=initial_zone,
        is_pinned=is_pinned,
        last_checked_at=datetime.utcnow()
    )
    db.session.add(new_loc)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"'{label}' saved to your places.",
        "location": new_loc.to_dict()
    }), 201


@user_bp.route("/saved-locations/<int:loc_id>", methods=["PUT"])
def update_saved_location(loc_id):
    """
    PUT /api/user/saved-locations/<id>
    Rename place label, update address, or toggle is_pinned.
    """
    user = get_current_user_optional()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    loc = SavedLocation.query.filter_by(id=loc_id, user_id=user.id).first()
    if not loc:
        return jsonify({"success": False, "error": "Saved place not found"}), 404

    data = request.get_json() or {}
    if "label" in data:
        loc.label = (data["label"] or loc.label).strip()
    if "address" in data:
        loc.address = (data["address"] or loc.address).strip()
    if "is_pinned" in data:
        loc.is_pinned = bool(data["is_pinned"])

    loc.last_checked_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Place updated successfully.",
        "location": loc.to_dict()
    }), 200


@user_bp.route("/saved-locations/<int:loc_id>", methods=["DELETE"])
def delete_saved_location(loc_id):
    """
    DELETE /api/user/saved-locations/<id>
    Remove a saved place.
    """
    user = get_current_user_optional()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    loc = SavedLocation.query.filter_by(id=loc_id, user_id=user.id).first()
    if not loc:
        return jsonify({"success": False, "error": "Saved place not found"}), 404

    db.session.delete(loc)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Place removed from saved destinations."
    }), 200

