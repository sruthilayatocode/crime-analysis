from flask import Blueprint, jsonify, request
from services.hotspot_service import analyze_hotspots
crime_bp = Blueprint("crime", __name__)


@crime_bp.route("/api/crimes", methods=["GET"])
def get_crimes():
    crimes = [
        {
            "id": 1,
            "type": "Theft",
            "location": "Vellore",
            "latitude": 12.9165,
            "longitude": 79.1325,
            "risk_level": "Medium"
        },
        {
            "id": 2,
            "type": "Assault",
            "location": "Katpadi",
            "latitude": 12.9692,
            "longitude": 79.1559,
            "risk_level": "High"
        }
    ]

    return jsonify({
        "success": True,
        "count": len(crimes),
        "data": crimes
    })


@crime_bp.route("/api/crimes/<int:crime_id>", methods=["GET"])
def get_crime_by_id(crime_id):
    return jsonify({
        "success": True,
        "message": f"Crime record {crime_id} retrieved successfully"
    })


@crime_bp.route("/api/crimes", methods=["POST"])
def add_crime():
    crime_data = request.get_json()

    return jsonify({
        "success": True,
        "message": "Crime record received successfully",
        "data": crime_data
    }), 201

@crime_bp.route("/api/hotspots", methods=["GET"])
def get_hotspots():

    crimes = [
        {"location": "Vellore"},
        {"location": "Vellore"},
        {"location": "Vellore"},
        {"location": "Katpadi"},
        {"location": "Katpadi"},
        {"location": "Ranipet"}
    ]

    hotspots = analyze_hotspots(crimes)

    return jsonify({
        "success": True,
        "message": "Crime hotspot analysis completed successfully",
        "data": hotspots
    })
@crime_bp.route("/api/risk/<string:location>", methods=["GET"])
def get_location_risk(location):

    location_risks = {
        "vellore": {
            "risk_level": "Medium",
            "crime_count": 3
        },
        "katpadi": {
            "risk_level": "Low",
            "crime_count": 2
        },
        "ranipet": {
            "risk_level": "Low",
            "crime_count": 1
        }
    }

    location_key = location.lower()

    if location_key not in location_risks:
        return jsonify({
            "success": False,
            "message": f"No crime data is available for {location.title()}"
        }), 404

    risk_data = location_risks[location_key]

    return jsonify({
        "success": True,
        "location": location.title(),
        "risk_level": risk_data["risk_level"],
        "crime_count": risk_data["crime_count"]
    })