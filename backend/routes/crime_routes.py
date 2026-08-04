from flask import Blueprint, jsonify, request

from database import db
from models.crime import Crime
from services.hotspot_service import analyze_hotspots


crime_bp = Blueprint("crime", __name__)


@crime_bp.route("/api/crimes", methods=["GET"])
def get_crimes():

    crimes = Crime.query.all()

    return jsonify({
        "success": True,
        "count": len(crimes),
        "data": [
            crime.to_dict()
            for crime in crimes
        ]
    })


@crime_bp.route("/api/crimes/<int:crime_id>", methods=["GET"])
def get_crime_by_id(crime_id):

    crime = db.session.get(
        Crime,
        crime_id
    )

    if crime is None:
        return jsonify({
            "success": False,
            "message": (
                f"Crime record {crime_id} "
                "was not found"
            )
        }), 404

    return jsonify({
        "success": True,
        "data": crime.to_dict()
    })


@crime_bp.route("/api/crimes", methods=["POST"])
def add_crime():

    crime_data = request.get_json()

    if not crime_data:
        return jsonify({
            "success": False,
            "message": "Request data is missing"
        }), 400

    required_fields = [
        "crime_type",
        "latitude",
        "longitude"
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in crime_data
    ]

    if missing_fields:
        return jsonify({
            "success": False,
            "message": (
                "Required fields are missing"
            ),
            "missing_fields": missing_fields
        }), 400

    try:

        new_crime = Crime(
            crime_type=crime_data[
                "crime_type"
            ],
            description=crime_data.get(
                "description"
            ),
            latitude=float(
                crime_data["latitude"]
            ),
            longitude=float(
                crime_data["longitude"]
            ),
            location_name=crime_data.get(
                "location_name"
            ),
            crime_date=crime_data.get(
                "crime_date"
            ),
            severity=crime_data.get(
                "severity"
            )
        )

        db.session.add(
            new_crime
        )

        db.session.commit()

        return jsonify({
            "success": True,
            "message": (
                "Crime record added "
                "successfully"
            ),
            "data": new_crime.to_dict()
        }), 201

    except (
        TypeError,
        ValueError
    ):

        return jsonify({
            "success": False,
            "message": (
                "Latitude and longitude "
                "must be valid numbers"
            )
        }), 400


@crime_bp.route(
    "/api/crimes/<int:crime_id>",
    methods=["PUT"]
)
def update_crime(crime_id):

    crime = db.session.get(
        Crime,
        crime_id
    )

    if crime is None:
        return jsonify({
            "success": False,
            "message": (
                f"Crime record {crime_id} "
                "was not found"
            )
        }), 404

    crime_data = request.get_json()

    if not crime_data:
        return jsonify({
            "success": False,
            "message": "Request data is missing"
        }), 400

    try:

        if "crime_type" in crime_data:
            crime.crime_type = (
                crime_data["crime_type"]
            )

        if "description" in crime_data:
            crime.description = (
                crime_data["description"]
            )

        if "latitude" in crime_data:
            crime.latitude = float(
                crime_data["latitude"]
            )

        if "longitude" in crime_data:
            crime.longitude = float(
                crime_data["longitude"]
            )

        if "location_name" in crime_data:
            crime.location_name = (
                crime_data["location_name"]
            )

        if "crime_date" in crime_data:
            crime.crime_date = (
                crime_data["crime_date"]
            )

        if "severity" in crime_data:
            crime.severity = (
                crime_data["severity"]
            )

        db.session.commit()

        return jsonify({
            "success": True,
            "message": (
                "Crime record updated "
                "successfully"
            ),
            "data": crime.to_dict()
        })

    except (
        TypeError,
        ValueError
    ):

        return jsonify({
            "success": False,
            "message": (
                "Latitude and longitude "
                "must be valid numbers"
            )
        }), 400


@crime_bp.route(
    "/api/crimes/<int:crime_id>",
    methods=["DELETE"]
)
def delete_crime(crime_id):

    crime = db.session.get(
        Crime,
        crime_id
    )

    if crime is None:
        return jsonify({
            "success": False,
            "message": (
                f"Crime record {crime_id} "
                "was not found"
            )
        }), 404

    db.session.delete(
        crime
    )

    db.session.commit()

    return jsonify({
        "success": True,
        "message": (
            f"Crime record {crime_id} "
            "deleted successfully"
        )
    })


@crime_bp.route(
    "/api/hotspots",
    methods=["GET"]
)
def get_hotspots():

    crimes = Crime.query.all()

   hotspot_input = [
    {
        "location": (
            crime.location_name
            or "Unknown"
        ),
        "latitude": crime.latitude,
        "longitude": crime.longitude
    }
    for crime in crimes
   ]

    hotspots = analyze_hotspots(
        hotspot_input
    )

    return jsonify({
        "success": True,
        "message": (
            "Crime hotspot analysis "
            "completed successfully"
        ),
        "data": hotspots
    })


@crime_bp.route(
    "/api/risk/<string:location>",
    methods=["GET"]
)
def get_location_risk(location):

    crimes = Crime.query.filter(
        db.func.lower(
            Crime.location_name
        ) == location.lower()
    ).all()

    if not crimes:

        return jsonify({
            "success": False,
            "message": (
                "No crime data is "
                f"available for "
                f"{location.title()}"
            )
        }), 404

    crime_count = len(
        crimes
    )

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