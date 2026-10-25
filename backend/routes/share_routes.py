"""
share_routes.py
===============
Endpoints for generating and viewing shareable CrimeSense location links:
- POST /api/share: Create unguessable, revocable token link with expiry (1h / 8h / 24h) and live/static mode
- GET /api/share/<token>: Public read-only endpoint (no login required) revealing only the shared location & live zone
- POST /api/share/<token>/update-live: Push live GPS coordinate updates for active live shares
- POST /api/share/<token>/revoke: Stop sharing / revoke token
"""

from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from database import db
from models.shared_link import SharedLink
from models.user import User
from services.auth_service import decode_token
from services.zone_service import calculate_zone_risk

share_bp = Blueprint("share", __name__, url_prefix="/api/share")


def get_optional_user():
    """Extract authenticated user if token provided, else None."""
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


@share_bp.route("", methods=["POST"])
def create_shared_link():
    """
    POST /api/share
    Creates a shareable link token URL (/s/<token>).
    Options:
    - is_live: True (live updating coordinates) or False (static place)
    - expiry_hours: 1, 8, or 24 (default 1)
    """
    user = get_optional_user()
    data = request.get_json() or {}

    lat = data.get("latitude") or data.get("lat")
    lng = data.get("longitude") or data.get("lng")
    accuracy = data.get("accuracy")
    label = (data.get("label") or "Shared Location").strip()
    address = (data.get("address") or "").strip()
    zone = (data.get("zone") or "green").lower()
    is_live = bool(data.get("is_live", False))
    expiry_hours = int(data.get("expiry_hours", 1))

    if expiry_hours not in (1, 8, 24):
        if expiry_hours <= 0 or expiry_hours > 72:
            expiry_hours = 1

    if lat is None or lng is None:
        return jsonify({"success": False, "error": "latitude and longitude required"}), 400

    try:
        lat = float(lat)
        lng = float(lng)
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Invalid coordinates"}), 400

    now = datetime.utcnow()
    expires_at = now + timedelta(hours=expiry_hours)
    token = SharedLink.generate_token()

    # Re-evaluate live zone
    try:
        risk = calculate_zone_risk(lat, lng, radius=1000)
        zone = (risk.get("zone") or "GREEN").lower()
    except Exception:
        pass

    new_link = SharedLink(
        token=token,
        user_id=user.id if user else None,
        label=label,
        address=address or f"{lat:.4f}, {lng:.4f}",
        latitude=lat,
        longitude=lng,
        accuracy=float(accuracy) if accuracy is not None else None,
        zone=zone,
        is_live=is_live,
        is_revoked=False,
        expires_at=expires_at,
        created_at=now,
        updated_at=now,
    )
    db.session.add(new_link)
    db.session.commit()

    return jsonify({
        "success": True,
        "token": token,
        "url": f"/s/{token}",
        "full_url": f"/s/{token}",
        "is_live": is_live,
        "expires_at": expires_at.isoformat(),
        "expiry_hours": expiry_hours,
        "link": new_link.to_owner_dict() if user else new_link.to_public_dict(),
    }), 201


@share_bp.route("/<token>", methods=["GET"])
def get_public_shared_location(token):
    """
    GET /api/share/<token>
    Public read-only endpoint: requires no login.
    Reveals only the shared location on map, safety zone, and updated time.
    """
    link = SharedLink.query.filter_by(token=token).first()
    if not link:
        return jsonify({
            "success": False,
            "error": "Share link not found or invalid token.",
            "is_active": False
        }), 404

    if not link.is_active():
        return jsonify({
            "success": False,
            "error": "This shared location link has expired or was stopped by the sender.",
            "is_expired": link.is_expired(),
            "is_revoked": link.is_revoked,
            "is_active": False,
            "label": link.label
        }), 200

    # Live zone re-evaluation on view
    risk_info = None
    try:
        risk_info = calculate_zone_risk(link.latitude, link.longitude, radius=1000)
        link.zone = (risk_info.get("zone") or "GREEN").lower()
        db.session.commit()
    except Exception:
        pass

    return jsonify({
        "success": True,
        "link": link.to_public_dict(),
        "zone_details": risk_info or {
            "zone": link.zone.upper(),
            "score": 0,
            "incident_count": 0,
            "confidence": "high"
        }
    }), 200


@share_bp.route("/<token>/update-live", methods=["POST"])
def update_live_location(token):
    """
    POST /api/share/<token>/update-live
    Allows continuous updates for active live location shares.
    """
    link = SharedLink.query.filter_by(token=token).first()
    if not link or not link.is_active():
        return jsonify({"success": False, "error": "Active share link not found"}), 404

    if not link.is_live:
        return jsonify({"success": False, "error": "This is a static link and cannot be live-updated"}), 400

    data = request.get_json() or {}
    lat = data.get("latitude") or data.get("lat")
    lng = data.get("longitude") or data.get("lng")
    accuracy = data.get("accuracy")

    if lat is not None and lng is not None:
        link.latitude = float(lat)
        link.longitude = float(lng)
        if accuracy is not None:
            link.accuracy = float(accuracy)
        
        try:
            risk = calculate_zone_risk(link.latitude, link.longitude, radius=1000)
            link.zone = (risk.get("zone") or "GREEN").lower()
        except Exception:
            pass

        link.updated_at = datetime.utcnow()
        db.session.commit()

    return jsonify({
        "success": True,
        "message": "Live location updated.",
        "link": link.to_public_dict()
    }), 200


@share_bp.route("/<token>/revoke", methods=["POST"])
def revoke_shared_link(token):
    """
    POST /api/share/<token>/revoke
    'Stop Sharing' button action: immediately deactivates the share token.
    """
    link = SharedLink.query.filter_by(token=token).first()
    if not link:
        return jsonify({"success": False, "error": "Share link not found"}), 404

    link.is_revoked = True
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Location sharing stopped. The public link is now deactivated.",
        "link": link.to_public_dict()
    }), 200
