"""
Crime REST API routes.

All endpoints delegate to the service layer and return
consistent JSON responses:

    { "success": true/false, ... }
"""

from flask import Blueprint, jsonify, request

from services import crime_service
from services.errors import ValidationError
from services.hotspot_service import analyze_hotspots
from services.proximity_service import find_nearby_crimes
from services.statistics_service import build_statistics


crime_bp = Blueprint("crime", __name__)


@crime_bp.route("/api/crimes", methods=["GET"])
def get_crimes():
    """Return all crime records."""

    crimes = crime_service.list_crimes()

    return jsonify({
        "success": True,
        "count": len(crimes),
        "data": crimes
    })


@crime_bp.route(
    "/api/crimes/<int:crime_id>",
    methods=["GET"]
)
def get_crime_by_id(crime_id):
    """Return one crime record by ID."""

    crime = crime_service.get_crime(
        crime_id
    )

    return jsonify({
        "success": True,
        "data": crime
    })


@crime_bp.route("/api/crimes", methods=["POST"])
def add_crime():
    """Create a new crime record."""

    crime_data = request.get_json(
        silent=True
    )

    new_crime = crime_service.create_crime(
        crime_data
    )

    return jsonify({
        "success": True,
        "message": (
            "Crime record added successfully"
        ),
        "data": new_crime
    }), 201


@crime_bp.route(
    "/api/crimes/<int:crime_id>",
    methods=["PUT"]
)
def update_crime(crime_id):
    """Update an existing crime record."""

    crime_data = request.get_json(
        silent=True
    )

    updated_crime = (
        crime_service.update_crime(
            crime_id,
            crime_data
        )
    )

    return jsonify({
        "success": True,
        "message": (
            "Crime record updated successfully"
        ),
        "data": updated_crime
    })


@crime_bp.route(
    "/api/crimes/<int:crime_id>",
    methods=["DELETE"]
)
def delete_crime(crime_id):
    """Delete an existing crime record."""

    crime_service.delete_crime(
        crime_id
    )

    return jsonify({
        "success": True,
        "message": (
            f"Crime record {crime_id} "
            "deleted successfully"
        )
    })


@crime_bp.route(
    "/api/crimes/hotspots",
    methods=["GET"]
)
@crime_bp.route(
    "/api/hotspots",
    methods=["GET"]
)
def get_hotspots():
    """
    Crime hotspot analysis based on the real crime
    coordinates stored in the database.

    Optional query parameters:
        risk_level=High|Medium|Low
        limit=<max number of hotspots>
    """

    crimes = crime_service.list_crimes()

    # Hotspot analysis needs coordinates; the dataset
    # contains some records that were not geocoded.
    geocoded_crimes = [
        crime
        for crime in crimes
        if crime.get("latitude") is not None
        and crime.get("longitude") is not None
    ]

    hotspot_input = [
        {
            "location": (
                crime.get("location_name")
                or "Unknown"
            ),
            "latitude": crime["latitude"],
            "longitude": crime["longitude"]
        }
        for crime in geocoded_crimes
    ]

    hotspots = analyze_hotspots(
        hotspot_input
    )

    risk_level_filter = request.args.get(
        "risk_level"
    )

    if risk_level_filter:

        hotspots = [
            hotspot
            for hotspot in hotspots
            if hotspot["risk_level"].lower()
            == risk_level_filter.lower()
        ]

    limit_argument = request.args.get(
        "limit"
    )

    if limit_argument:

        try:

            limit = int(limit_argument)

            if limit >= 0:
                hotspots = hotspots[:limit]

        except ValueError:
            raise ValidationError(
                "limit must be a valid integer"
            )

    return jsonify({
        "success": True,
        "count": len(hotspots),
        "data": hotspots
    })


@crime_bp.route(
    "/api/crimes/nearby",
    methods=["GET"]
)
def get_nearby_crimes():
    """
    Find crime records near a user's location.

    Query parameters:
        latitude  (required, -90..90)
        longitude (required, -180..180)
        radius    (optional, kilometers, default 5)
    """

    arguments = request.args

    missing_parameters = [
        parameter
        for parameter in (
            "latitude",
            "longitude"
        )
        if parameter not in arguments
    ]

    if missing_parameters:
        raise ValidationError(
            "Required query parameters are missing",
            details={
                "missing_parameters": missing_parameters
            }
        )

    try:

        latitude = float(arguments["latitude"])
        longitude = float(arguments["longitude"])

    except ValueError:
        raise ValidationError(
            "latitude and longitude must be "
            "valid numbers"
        )

    radius_km = 5.0

    if "radius" in arguments:

        try:

            radius_km = float(
                arguments["radius"]
            )

        except ValueError:
            raise ValidationError(
                "radius must be a valid number"
            )

        if radius_km <= 0:
            raise ValidationError(
                "radius must be greater than zero"
            )

    if not -90 <= latitude <= 90:
        raise ValidationError(
            "Latitude must be between -90 and 90"
        )

    if not -180 <= longitude <= 180:
        raise ValidationError(
            "Longitude must be between -180 and 180"
        )

    crimes = crime_service.list_crimes()

    nearby_crimes = find_nearby_crimes(
        crimes=crimes,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km
    )

    return jsonify({
        "success": True,
        "count": len(nearby_crimes),
        "search_center": {
            "latitude": latitude,
            "longitude": longitude
        },
        "search_radius_km": radius_km,
        "data": nearby_crimes
    })


@crime_bp.route(
    "/api/crimes/statistics",
    methods=["GET"]
)
def get_statistics():
    """
    Dashboard statistics built from real crime
    records: totals plus counts by type, severity,
    area and month.
    """

    crimes = crime_service.list_crimes()

    statistics = build_statistics(
        crimes
    )

    return jsonify({
        "success": True,
        "data": statistics
    })


@crime_bp.route(
    "/api/risk/<string:location>",
    methods=["GET"]
)
def get_location_risk(location):
    """Risk level for a named location."""

    crimes = crime_service.list_crimes()

    location_crimes = [
        crime
        for crime in crimes
        if (crime.get("location_name") or "").lower()
        == location.lower()
    ]

    if not location_crimes:

        return jsonify({
            "success": False,
            "message": (
                "No crime data is available for "
                f"{location.title()}"
            )
        }), 404

    crime_count = len(location_crimes)

    if crime_count >= 5:
        risk_level = "High"

    elif crime_count >= 3:
        risk_level = "Medium"

    else:
        risk_level = "Low"

    return jsonify({
        "success": True,
        "location": location.title(),
        "risk_level": risk_level,
        "crime_count": crime_count
    })