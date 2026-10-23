from flask import Blueprint, jsonify, request

from services.proximity_service import (
    determine_alert_level,
    find_nearby_verified_locations,
)


alert_bp = Blueprint("alert", __name__)


@alert_bp.route("/api/proximity-check", methods=["POST"])
def proximity_check():

    user_data = request.get_json()

    if not user_data:
        return jsonify({
            "success": False,
            "message": "Request data is missing"
        }), 400

    required_fields = [
        "latitude",
        "longitude"
    ]

    for field in required_fields:

        if field not in user_data:
            return jsonify({
                "success": False,
                "message": f"{field} is required"
            }), 400

    try:
        user_latitude = float(
            user_data["latitude"]
        )

        user_longitude = float(
            user_data["longitude"]
        )

        alert_radius_km = float(
            user_data.get("radius_km", 2)
        )

    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": (
                "latitude, longitude and radius_km "
                "must be valid numbers"
            )
        }), 400

    nearby_locations = find_nearby_verified_locations(
        user_latitude=user_latitude,
        user_longitude=user_longitude,
        radius_km=alert_radius_km
    )

    alert_level = determine_alert_level(
        nearby_locations
    )

    if alert_level != "NONE":
        message = (
            f"{len(nearby_locations)} verified crime "
            f"location(s) found within "
            f"{alert_radius_km} km."
        )
    else:
        # Careful wording: no verified data nearby does NOT
        # mean no crime exists nearby.
        message = (
            f"No verified crime locations within "
            f"{alert_radius_km} km. This does NOT mean "
            f"no crime exists nearby - most validated "
            f"records have no reliable coordinates."
        )

    return jsonify({
        "success": True,
        "alert_level": alert_level,
        "message": message,
        "user_location": {
            "latitude": user_latitude,
            "longitude": user_longitude
        },
        "radius_km": alert_radius_km,
        "verified_locations_nearby": len(nearby_locations),
        "nearby_locations": nearby_locations,
        "data_basis": (
            "HIGH-confidence verified coordinates from the "
            "CrimeSense data pipeline only"
        )
    })


@alert_bp.route("/api/verified-locations", methods=["GET"])
def verified_locations():

    from services.proximity_service import (
        load_verified_locations
    )

    locations = load_verified_locations()

    return jsonify({
        "success": True,
        "count": len(locations),
        "data": locations
    })