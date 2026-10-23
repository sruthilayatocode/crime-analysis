from uuid import uuid4

from flask import Blueprint, jsonify, request

from database import db
from models.crime import Crime
from services.auth_service import login_required, admin_required
from services.zone_service import calculate_zone_risk
from services.hotspot_service import get_hotspots_from_db



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
@admin_required
def add_crime():


    crime_data = request.get_json()

    if not crime_data:
        return jsonify({
            "success": False,
            "message": "Request data is missing"
        }), 400

    required_fields = [
        "crime_type"
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

        # article_id is the pipeline primary identifier; if a
        # manual record is created without one, generate a
        # unique value so the uniqueness constraint holds.
        article_id = (
            crime_data.get("article_id")
            or uuid4().hex[:16]
        )

        if Crime.query.filter_by(
            article_id=article_id
        ).first():
            return jsonify({
                "success": False,
                "message": (
                    f"A crime record with article_id "
                    f"'{article_id}' already exists"
                )
            }), 409

        new_crime = Crime(
            article_id=article_id,
            title=crime_data.get("title"),
            published_date=crime_data.get(
                "published_date"
            ),
            source=crime_data.get("source"),
            url=crime_data.get("url"),
            crime_type=crime_data[
                "crime_type"
            ],
            description=crime_data.get(
                "description"
            ),
            district=crime_data.get("district"),
            locality=crime_data.get("locality"),
            # Coordinates are optional: most validated
            # records genuinely have none.
            latitude=(
                float(crime_data["latitude"])
                if crime_data.get("latitude") not in (None, "")
                else None
            ),
            longitude=(
                float(crime_data["longitude"])
                if crime_data.get("longitude") not in (None, "")
                else None
            ),
            location_confidence=crime_data.get(
                "location_confidence"
            ),
            location_source=crime_data.get(
                "location_source"
            ),
            severity_score=(
                float(crime_data["severity_score"])
                if crime_data.get("severity_score") not in (None, "")
                else None
            ),
            risk_level=crime_data.get("risk_level"),
            # Legacy fields still accepted
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

        # New pipeline fields (updatable)
        for text_field in [
            "title",
            "published_date",
            "source",
            "url",
            "district",
            "locality",
            "location_confidence",
            "location_source",
            "risk_level",
        ]:
            if text_field in crime_data:
                setattr(
                    crime,
                    text_field,
                    crime_data[text_field]
                )

        if "latitude" in crime_data:
            crime.latitude = (
                float(crime_data["latitude"])
                if crime_data["latitude"] not in (None, "")
                else None
            )

        if "longitude" in crime_data:
            crime.longitude = (
                float(crime_data["longitude"])
                if crime_data["longitude"] not in (None, "")
                else None
            )

        if "severity_score" in crime_data:
            crime.severity_score = (
                float(crime_data["severity_score"])
                if crime_data["severity_score"] not in (None, "")
                else None
            )

        # Legacy fields still updatable
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


def _load_hotspots_from_db():
    return get_hotspots_from_db()



@crime_bp.route(
    "/api/hotspots",
    methods=["GET"]
)
def get_hotspots():

    # Serve the VERIFIED hotspot results produced by the offline data-pipeline
    # analysis (coordinates on HIGH-confidence rows only).
    #
    # We deliberately do NOT recalculate hotspots from all database coordinates
    # here: 82 of 89 records have no reliable coordinates and must not be
    # treated as precise incident locations.

    # Query verified HIGH-confidence coordinates directly from the database
    hotspots = _load_hotspots_from_db()
    source = "database (verified HIGH-confidence coordinates)"
    message = (
        "Hotspot results computed from verified HIGH-confidence "
        "coordinates in the database"
    )

    return jsonify({
        "success": True,
        "message": message,
        "source": source,
        "count": len(hotspots),
        "data": hotspots
    })


@crime_bp.route(
    "/api/risk/<string:location>",
    methods=["GET"]
)
def get_location_risk(location):

    # Match on locality first (the field populated by the
    # validated pipeline), then fall back to the legacy
    # location_name field.
    crimes = Crime.query.filter(
        db.func.lower(
            db.func.coalesce(
                Crime.locality,
                Crime.location_name
            )
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

    crime_count = len(crimes)

    # Risk levels come from the COMPLETED data pipeline
    # (incident-level severity_score / risk_level stored in
    # the database). We do NOT invent risk from raw counts
    # such as "5 crimes = High".
    risk_distribution = {}
    for crime in crimes:
        level = crime.risk_level or "Unknown"
        risk_distribution[level] = (
            risk_distribution.get(level, 0) + 1
        )

    # Order levels by pipeline severity so the predominant
    # level is the most severe one present.
    severity_order = [
        "Critical", "High", "Medium", "Low", "Unknown"
    ]
    predominant_risk_level = next(
        (
            level for level in severity_order
            if risk_distribution.get(level)
        ),
        "Unknown"
    )

    severity_scores = [
        crime.severity_score
        for crime in crimes
        if crime.severity_score is not None
    ]

    return jsonify({
        "success": True,
        "location": location.title(),
        "crime_count": crime_count,
        # Aggregated from stored incident-level pipeline risk.
        "predominant_risk_level": predominant_risk_level,
        "risk_level_distribution": risk_distribution,
        "average_severity_score": (
            round(
                sum(severity_scores) / len(severity_scores),
                2
            )
            if severity_scores
            else None
        ),
        "risk_basis": (
            "incident-level severity_score/risk_level from the "
            "CrimeSense scoring pipeline"
        )
    })


@crime_bp.route("/api/zone", methods=["GET", "POST"])
@crime_bp.route("/api/zone/calculate", methods=["GET", "POST"])
def get_zone():
    """
    GET or POST /api/zone or /api/zone/calculate
    Evaluate geographic zone risk level (RED, YELLOW, GREEN) around coordinates.
    """
    data = request.get_json(silent=True) or {}
    lat_str = request.args.get("lat") or data.get("lat") or data.get("latitude")
    lng_str = (
        request.args.get("lng")
        or request.args.get("lon")
        or request.args.get("longitude")
        or data.get("lng")
        or data.get("lon")
        or data.get("longitude")
    )
    radius_str = request.args.get("radius") or request.args.get("radius_m") or data.get("radius") or data.get("radius_m")


    if lat_str is None or lng_str is None:
        return jsonify({
            "success": False,
            "error": "Missing required query parameters: 'lat' and 'lng' are required.",
        }), 400

    try:
        lat = float(lat_str)
        lng = float(lng_str)
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "error": "Parameters 'lat' and 'lng' must be valid floating-point numbers.",
        }), 400

    if not (-90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0):
        return jsonify({
            "success": False,
            "error": "Coordinates out of bounds: lat must be in [-90, 90] and lng in [-180, 180].",
        }), 400

    radius = 1000.0
    if radius_str is not None:
        try:
            radius = float(radius_str)
            if radius <= 0:
                return jsonify({
                    "success": False,
                    "error": "Radius must be a positive number in meters.",
                }), 400
        except (TypeError, ValueError):
            return jsonify({
                "success": False,
                "error": "Parameter 'radius' must be a valid number.",
            }), 400

    zone_data = calculate_zone_risk(lat=lat, lng=lng, radius=radius)
    response = dict(zone_data)
    response["success"] = True
    return jsonify(response), 200