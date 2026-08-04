from flask import Flask, jsonify

from database import db
from models.crime import Crime

from routes.crime_routes import crime_bp
from routes.alert_routes import alert_bp


app = Flask(__name__)


# SQLite database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///crimesense.db"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# Connect SQLAlchemy with the Flask application
db.init_app(app)


# Create database tables automatically
with app.app_context():
    db.create_all()


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
        "service": "CrimeSense Backend"
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


if __name__ == "__main__":
    app.run(debug=True)