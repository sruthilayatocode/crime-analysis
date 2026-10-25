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

    missing_fields = [f for f in ["latitude", "longitude"] if f not in user_data]
    if missing_fields:
        return jsonify({
            "success": False,
            "message": "Required fields are missing",
            "details": {"missing_fields": missing_fields}
        }), 400

    try:
        user_latitude = float(user_data["latitude"])
        user_longitude = float(user_data["longitude"])
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

    if "alert_radius_meters" in user_data:
        try:
            alert_radius_m = float(user_data["alert_radius_meters"])
        except (TypeError, ValueError):
            return jsonify({
                "success": False,
                "message": "alert_radius_meters must be a valid number"
            }), 400
        if alert_radius_m <= 0:
            return jsonify({
                "success": False,
                "message": "alert_radius_meters must be greater than zero"
            }), 400
        alert_radius_km = alert_radius_m / 1000.0
    else:
        try:
            alert_radius_km = float(user_data.get("radius_km", 2))
        except (TypeError, ValueError):
            return jsonify({
                "success": False,
                "message": "radius_km must be a valid number"
            }), 400
        if alert_radius_km <= 0:
            return jsonify({
                "success": False,
                "message": "radius_km must be greater than zero"
            }), 400

    nearby_locations = find_nearby_verified_locations(
        user_latitude=user_latitude,
        user_longitude=user_longitude,
        radius_km=alert_radius_km
    )

    from models.crime import Crime
    from services.proximity_service import find_nearby_crimes, find_nearby_hotspots, find_nearest_hotspot
    from services.hotspot_service import analyze_hotspots, get_hotspots_from_db

    all_crimes = [c.to_dict() for c in Crime.query.all()]
    geocoded_crimes = [c for c in all_crimes if c.get("latitude") is not None and c.get("longitude") is not None]
    nearby_crimes = find_nearby_crimes(geocoded_crimes, user_latitude, user_longitude, alert_radius_km)

    hotspots = get_hotspots_from_db()
    if not hotspots and geocoded_crimes:
        hotspot_input = [
            {"location_name": c.get("location_name") or c.get("locality") or "Unknown", "latitude": c["latitude"], "longitude": c["longitude"]}
            for c in geocoded_crimes
        ]
        hotspots = analyze_hotspots(hotspot_input)

    nearest_hotspot = find_nearest_hotspot(hotspots, user_latitude, user_longitude)
    nearby_hotspots = find_nearby_hotspots(hotspots, user_latitude, user_longitude, alert_radius_km)

    alert_level = determine_alert_level(nearby_locations)
    if alert_level == "NONE" and nearby_crimes:
        alert_level = "MODERATE" if len(nearby_crimes) < 3 else "HIGH"

    is_alert = len(nearby_crimes) > 0 or (alert_level != "NONE")

    if is_alert:
        message = f"{len(nearby_crimes) or len(nearby_locations)} crime incident(s) or hotspot(s) found nearby."
    else:
        message = f"No verified crime locations within {alert_radius_km} km."

    return jsonify({
        "success": True,
        "alert": is_alert,
        "alert_level": alert_level,
        "message": message,
        "user_location": {
            "latitude": user_latitude,
            "longitude": user_longitude
        },
        "radius_km": alert_radius_km,
        "checked_radius_meters": alert_radius_km * 1000.0,
        "verified_locations_nearby": len(nearby_locations),
        "nearby_locations": nearby_locations,
        "nearby_crimes": nearby_crimes,
        "nearby_hotspots": nearby_hotspots,
        "nearest_hotspot": nearest_hotspot,
        "limitations": ["Data limited to verified news and reports"],
        "data_basis": "CrimeSense verified data pipeline and SQLite database"
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