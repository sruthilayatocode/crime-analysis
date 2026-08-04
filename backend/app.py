from flask import Flask, jsonify

from routes.crime_routes import crime_bp
from routes.alert_routes import alert_bp
app = Flask(__name__)
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
        "description": "AI-powered Crime Hotspot Analysis and Proximity Alert System",
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