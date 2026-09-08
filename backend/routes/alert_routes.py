"""
Proximity alert routes.

The alert is computed against real crime hotspot
centers derived from the crimes stored in the
database (no hard-coded hotspot coordinates).
"""

from flask import Blueprint, jsonify, request

from services import crime_service
from services.alert_service import AlertService
from services.errors import ValidationError
from services.hotspot_service import analyze_hotspots
from services.proximity_service import (
    check_proximity,
    find_nearest_hotspot,
)

try:
    from config.config import (
        PROXIMITY_ALERT_MAX_RADIUS_METERS,
        PROXIMITY_ALERT_MIN_RADIUS_METERS,
        PROXIMITY_ALERT_RADIUS_METERS,
        PROXIMITY_MAX_RESULTS,
    )
except Exception:
    PROXIMITY_ALERT_RADIUS_METERS = 500.0
    PROXIMITY_ALERT_MIN_RADIUS_METERS = 10.0
    PROXIMITY_ALERT_MAX_RADIUS_METERS = 50000.0
    PROXIMITY_MAX_RESULTS = 50


alert_bp = Blueprint("alert", __name__)


def _get_ml_analytics_service():
    """Lazily import and return the ML analytics service."""
    try:
        from services.ml_prediction_service import MLAnalyticsService
        return MLAnalyticsService()
    except Exception:
        return None


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
        return jsonify({
            "success": False,
            "message": "Request body must contain JSON"
        }), 400

    if not isinstance(user_data, dict):
        return jsonify({
            "success": False,
            "message": "Request body must be a JSON object"
        }), 400

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
        return jsonify({
            "success": False,
            "message": "Required fields are missing",
            "details": {
                "missing_fields": missing_fields
            }
        }), 400

    try:
        user_latitude = float(
            user_data["latitude"]
        )
        user_longitude = float(
            user_data["longitude"]
        )
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Latitude and longitude must be valid numbers"
        }), 400

    if not -90 <= user_latitude <= 90:
        return jsonify({
            "success": False,
            "message": "Latitude must be between -90 and 90"
        }), 400

    if not -180 <= user_longitude <= 180:
        return jsonify({
            "success": False,
            "message": "Longitude must be between -180 and 180"
        }), 400

    try:
        alert_radius = float(
            user_data.get(
                "alert_radius_meters",
                PROXIMITY_ALERT_RADIUS_METERS
            )
        )
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "alert_radius_meters must be a valid number"
        }), 400

    if alert_radius <= 0:
        return jsonify({
            "success": False,
            "message": "alert_radius_meters must be greater than zero"
        }), 400

    if alert_radius < PROXIMITY_ALERT_MIN_RADIUS_METERS:
        return jsonify({
            "success": False,
            "message": (
                f"alert_radius_meters must be at least "
                f"{PROXIMITY_ALERT_MIN_RADIUS_METERS}"
            )
        }), 400

    if alert_radius > PROXIMITY_ALERT_MAX_RADIUS_METERS:
        return jsonify({
            "success": False,
            "message": (
                f"alert_radius_meters must be at most "
                f"{PROXIMITY_ALERT_MAX_RADIUS_METERS}"
            )
        }), 400

    try:
        crimes = crime_service.list_crimes()
    except Exception:
        return jsonify({
            "success": False,
            "message": "Failed to load crime records"
        }), 500

    geocoded_crimes = [
        crime
        for crime in crimes
        if crime.get("latitude") is not None
        and crime.get("longitude") is not None
    ]

    if not geocoded_crimes:
        return jsonify({
            "success": True,
            "alert": False,
            "message": (
                "No geocoded crime data is available "
                "yet, so no proximity alert can be "
                "calculated."
            ),
            "user_location": {
                "latitude": user_latitude,
                "longitude": user_longitude
            },
            "nearby_crimes": [],
            "nearby_hotspots": [],
            "checked_radius_meters": alert_radius,
        })

    hotspot_input = [
        {
            "location_name": crime.get(
                "location_name"
            ) or "Unknown",
            "latitude": crime["latitude"],
            "longitude": crime["longitude"]
        }
        for crime in geocoded_crimes
    ]

    hotspots = analyze_hotspots(
        hotspot_input
    )

    nearest_hotspot = find_nearest_hotspot(
        hotspots,
        user_latitude,
        user_longitude
    )

    alert_service = AlertService(
        proximity_service=__import__(
            "services.proximity_service",
            fromlist=["find_nearby_crimes", "find_nearby_hotspots"]
        ),
        ml_analytics_service=_get_ml_analytics_service(),
    )

    result = alert_service.check_alert(
        user_latitude=user_latitude,
        user_longitude=user_longitude,
        crimes=geocoded_crimes,
        hotspots=hotspots,
        alert_radius_meters=alert_radius,
        max_results=PROXIMITY_MAX_RESULTS,
    )

    response = {
        "success": True,
        "alert": result["alert"],
        "message": result["message"],
        "user_location": {
            "latitude": user_latitude,
            "longitude": user_longitude
        },
        "nearby_crimes": result["nearby_crimes"],
        "nearby_hotspots": result["nearby_hotspots"],
        "checked_radius_meters": result["checked_radius_meters"],
        "limitations": result["limitations"],
    }

    if nearest_hotspot is not None:
        response["nearest_hotspot"] = {
            "location": nearest_hotspot.get("location", "Unknown"),
            "latitude": nearest_hotspot.get("centroid_latitude"),
            "longitude": nearest_hotspot.get("centroid_longitude"),
            "crime_count": nearest_hotspot.get("crime_count"),
            "risk_level": nearest_hotspot.get("risk_level"),
        }

    return jsonify(response)