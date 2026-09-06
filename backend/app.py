"""
CrimeSense Flask application entry point.

Run from the backend/ directory:

    python app.py

The backend directory is added to sys.path below so the
package imports also work when the server is started from
the repository root (python backend/app.py).
"""

import os
import sys

# Make "database", "models", "routes", "services" and
# "config" importable no matter which directory the
# server is launched from. This fixes the previous
# "ModuleNotFoundError: No module named 'routes.crime_routes'".
BACKEND_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from flask import Flask, jsonify, request
from flask_cors import CORS

from config.config import CORS_ORIGINS, SQLALCHEMY_DATABASE_URI

from database import db

# Importing the models registers them on the SQLAlchemy
# metadata BEFORE db.create_all() runs below.
from models.crime import Crime  # noqa: F401

from routes.alert_routes import alert_bp
from routes.crime_routes import crime_bp

from services.errors import ApiError


app = Flask(__name__)


# SQLite database configuration.
app.config["SQLALCHEMY_DATABASE_URI"] = (
    SQLALCHEMY_DATABASE_URI
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# Connect SQLAlchemy with the Flask application
db.init_app(app)


# Create SQLite tables automatically
with app.app_context():
    db.create_all()


# Allow the local frontend origins to call /api/* endpoints.
CORS(
    app,
    resources={r"/api/*": {"origins": CORS_ORIGINS}}
)


# Register API route blueprints
app.register_blueprint(crime_bp)
app.register_blueprint(alert_bp)


@app.route("/")
def home():
    return jsonify({
        "message": "Welcome to CrimeSense Backend",
        "status": "Backend is running successfully"
    })


@app.route("/api/health")
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "CrimeSense Backend",
        "storage": "sqlite"
    })


@app.route("/api/project-info")
def project_info():
    return jsonify({
        "project_name": "CrimeSense",
        "description": (
            "AI-powered Crime Hotspot Analysis "
            "and Proximity Alert System"
        ),
        "features": [
            "Crime hotspot analysis",
            "Crime prediction",
            "Location-based risk analysis",
            "Proximity alerts",
            "Crime data visualization"
        ]
    })


# ---- Consistent JSON error responses --------------------

@app.errorhandler(ApiError)
def handle_api_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.errorhandler(400)
def handle_bad_request(error):
    return jsonify({
        "success": False,
        "message": (
            error.description
            or "Invalid request"
        )
    }), 400


@app.errorhandler(404)
def handle_not_found(error):
    return jsonify({
        "success": False,
        "message": (
            f"The requested URL "
            f"{request.path} was not found"
        )
    }), 404


@app.errorhandler(405)
def handle_method_not_allowed(error):
    return jsonify({
        "success": False,
        "message": (
            "Method not allowed for this endpoint"
        )
    }), 405


@app.errorhandler(500)
def handle_server_error(error):

    # Roll back any half-finished local DB session.
    try:
        db.session.rollback()
    except Exception:
        pass

    return jsonify({
        "success": False,
        "message": (
            "An unexpected server error occurred"
        )
    }), 500


if __name__ == "__main__":

    debug_mode = os.getenv(
        "FLASK_DEBUG",
        "1"
    ) == "1"

    host = os.getenv("HOST", "127.0.0.1")

    port = int(os.getenv("PORT", "5000"))

    app.run(
        debug=debug_mode,
        use_reloader=debug_mode,
        host=host,
        port=port
    )
