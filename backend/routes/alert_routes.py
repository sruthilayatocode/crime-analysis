from flask import Blueprint, jsonify, request

from services.proximity_service import check_proximity


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

    user_latitude = float(
        user_data["latitude"]
    )

    user_longitude = float(
        user_data["longitude"]
    )

    alert_radius = float(
        user_data.get(
            "alert_radius_meters",
            500
        )
    )

    # Temporary hotspot coordinates.
    # These will be replaced by DBSCAN-generated
    # hotspot coordinates after the real dataset is added.

    hotspot_latitude = 12.9716
    hotspot_longitude = 79.1590

    proximity_result = check_proximity(
        user_latitude=user_latitude,
        user_longitude=user_longitude,
        hotspot_latitude=hotspot_latitude,
        hotspot_longitude=hotspot_longitude,
        alert_radius=alert_radius
    )

    if proximity_result["is_nearby"]:

        message = (
            "Warning: You are near a "
            "crime hotspot."
        )

    else:

        message = (
            "You are outside the "
            "crime hotspot alert radius."
        )

    return jsonify({
        "success": True,
        "alert": proximity_result[
            "is_nearby"
        ],
        "message": message,
        "user_location": {
            "latitude": user_latitude,
            "longitude": user_longitude
        },
        "hotspot_location": {
            "latitude": hotspot_latitude,
            "longitude": hotspot_longitude
        },
        "distance_meters": proximity_result[
            "distance_meters"
        ],
        "alert_radius_meters": proximity_result[
            "alert_radius_meters"
        ]
    })