"""
Proximity alert routes.

The alert is computed against real crime hotspot
centers derived from the crimes stored in the
database (no hard-coded hotspot coordinates).
"""

from flask import Blueprint, jsonify, request

from services import crime_service
from services.errors import ValidationError
from services.hotspot_service import analyze_hotspots
from services.proximity_service import (
    check_proximity,
    find_nearest_hotspot,
)


alert_bp = Blueprint("alert", __name__)


@alert_bp.route(
    "/api/proximity-check",
    methods=["POST"]
)
def proximity_check():
    """
    Check whether a user's location falls inside the
    alert radius of the nearest real crime hotspot.
    """

    user_data = request.get_json(
        silent=True
    )

    if not user_data:
        raise ValidationError(
            "Request body must contain "
            "location data as JSON"
        )

    required_fields = [
        "latitude",
        "longitude"
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in user_data
    ]

    if missing_fields:
        raise ValidationError(
            "Required fields are missing",
            details={
                "missing_fields": missing_fields
            }
        )

    try:

        user_latitude = float(
            user_data["latitude"]
        )

        user_longitude = float(
            user_data["longitude"]
        )

    except (
        TypeError,
        ValueError
    ):
        raise ValidationError(
            "Latitude and longitude must be "
            "valid numbers"
        )

    if not -90 <= user_latitude <= 90:
        raise ValidationError(
            "Latitude must be between -90 and 90"
        )

    if not -180 <= user_longitude <= 180:
        raise ValidationError(
            "Longitude must be between -180 and 180"
        )

    try:

        alert_radius = float(
            user_data.get(
                "alert_radius_meters",
                500
            )
        )

    except (
        TypeError,
        ValueError
    ):
        raise ValidationError(
            "alert_radius_meters must be a "
            "valid number"
        )

    if alert_radius <= 0:
        raise ValidationError(
            "alert_radius_meters must be "
            "greater than zero"
        )

    # Build hotspots from the actual crime records.
    crimes = crime_service.list_crimes()

    if not crimes:

        return jsonify({
            "success": True,
            "alert": False,
            "message": (
                "No crime data is available yet, "
                "so no proximity alert can be "
                "calculated."
            ),
            "user_location": {
                "latitude": user_latitude,
                "longitude": user_longitude
            }
        })

    hotspot_input = [
        {
            "location": (
                crime.get("location_name")
                or "Unknown"
            ),
            "latitude": crime["latitude"],
            "longitude": crime["longitude"]
        }
        for crime in crimes
    ]

    hotspots = analyze_hotspots(
        hotspot_input
    )

    nearest_hotspot = find_nearest_hotspot(
        hotspots,
        user_latitude,
        user_longitude
    )

    proximity_result = check_proximity(
        user_latitude=user_latitude,
        user_longitude=user_longitude,
        hotspot_latitude=nearest_hotspot[
            "average_latitude"
        ],
        hotspot_longitude=nearest_hotspot[
            "average_longitude"
        ],
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
        "nearest_hotspot": {
            "location": nearest_hotspot[
                "location"
            ],
            "latitude": nearest_hotspot[
                "average_latitude"
            ],
            "longitude": nearest_hotspot[
                "average_longitude"
            ],
            "crime_count": nearest_hotspot[
                "crime_count"
            ],
            "risk_level": nearest_hotspot[
                "risk_level"
            ]
        },
        "distance_meters": proximity_result[
            "distance_meters"
        ],
        "alert_radius_meters": proximity_result[
            "alert_radius_meters"
        ]
    })