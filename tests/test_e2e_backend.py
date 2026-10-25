"""
End-to-end backend integration test for Task 7E.

Demonstrates the complete flow:
1. Insert controlled test crime records into an isolated temporary database.
2. Run hotspot analysis.
3. Submit user coordinates.
4. Calculate proximity.
5. Detect nearby hotspot/crime.
6. Generate alert response.
7. Verify the complete response.

Uses ONLY synthetic test records inside the temporary test database.
Does NOT modify the real CrimeSense database.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from flask import Flask  # noqa: E402
from database import db  # noqa: E402
from backend.app import app as real_app  # noqa: E402
from routes.alert_routes import alert_bp  # noqa: E402
from routes.crime_routes import crime_bp  # noqa: E402
from services import crime_service  # noqa: E402
from services.hotspot_service import analyze_hotspots  # noqa: E402
from services.proximity_service import find_nearby_crimes, find_nearby_hotspots  # noqa: E402
from services.ml_prediction_service import MLAnalyticsService  # noqa: E402


# ------------------------------------------------------------------ #
# Isolated database fixture
# ------------------------------------------------------------------ #


@pytest.fixture(autouse=True)
def isolated_db(tmp_path):
    db_path = tmp_path / "test_e2e.db"
    db_uri = "sqlite:///" + str(db_path)

    test_app = Flask(__name__)
    test_app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    test_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(test_app)

    test_app.register_blueprint(crime_bp)
    test_app.register_blueprint(alert_bp)

    with test_app.app_context():
        db.create_all()
        yield test_app

    with test_app.app_context():
        db.session.remove()
        engines = db._app_engines.get(test_app, {})
        for engine in engines.values():
            engine.dispose()
        db._app_engines.pop(test_app, None)


@pytest.fixture()
def client(isolated_db):
    with isolated_db.test_client() as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clear_crimes(isolated_db):
    with isolated_db.app_context():
        db.session.execute(db.text("DELETE FROM crimes"))
        db.session.commit()
        db.session.remove()
    yield
    with isolated_db.app_context():
        db.session.execute(db.text("DELETE FROM crimes"))
        db.session.commit()
        db.session.remove()


# ------------------------------------------------------------------ #
# End-to-end test
# ------------------------------------------------------------------ #


class TestEndToEndBackend:
    def test_complete_proximity_alert_flow(self, client, isolated_db):
        with isolated_db.app_context():
            crime_service.create_crime({
                "crime_type": "Theft",
                "latitude": 13.043505,
                "longitude": 79.240410,
                "location_name": "Katpadi",
                "district": "Vellore",
                "severity_score": 4,
                "risk_level": "Medium",
                "crime_date": "2025-06-12",
            })
            crime_service.create_crime({
                "crime_type": "Theft",
                "latitude": 13.043506,
                "longitude": 79.240411,
                "location_name": "Katpadi",
                "district": "Vellore",
                "severity_score": 4,
                "risk_level": "Medium",
                "crime_date": "2025-06-12",
            })
            crime_service.create_crime({
                "crime_type": "Theft",
                "latitude": 13.043507,
                "longitude": 79.240412,
                "location_name": "Katpadi",
                "district": "Vellore",
                "severity_score": 4,
                "risk_level": "Medium",
                "crime_date": "2025-06-12",
            })

        with isolated_db.app_context():
            crimes = crime_service.list_crimes()

        geocoded = [
            c for c in crimes
            if c.get("latitude") is not None and c.get("longitude") is not None
        ]
        hotspot_input = [
            {
                "location_name": c.get("location_name") or "Unknown",
                "latitude": c["latitude"],
                "longitude": c["longitude"],
            }
            for c in geocoded
        ]
        hotspots = analyze_hotspots(hotspot_input)

        assert len(hotspots) >= 1

        user_lat = 13.043505
        user_lon = 79.240410

        nearby_crimes = find_nearby_crimes(
            crimes=geocoded,
            latitude=user_lat,
            longitude=user_lon,
            radius_km=1.0,
        )
        assert len(nearby_crimes) == 3
        assert nearby_crimes[0]["distance_km"] == 0.0

        nearby_hotspots = find_nearby_hotspots(
            hotspots=hotspots,
            latitude=user_lat,
            longitude=user_lon,
            radius_km=1.0,
        )
        assert len(nearby_hotspots) >= 1

        resp = client.post(
            "/api/proximity-check",
            json={
                "latitude": user_lat,
                "longitude": user_lon,
                "alert_radius_meters": 1000,
            },
        )
        assert resp.status_code == 200
        body = resp.get_json()

        assert body["success"] is True
        assert "alert" in body
        assert "message" in body
        assert "user_location" in body
        assert "nearby_crimes" in body
        assert "nearby_hotspots" in body
        assert "checked_radius_meters" in body
        assert "limitations" in body

        assert len(body["nearby_crimes"]) == 3
        assert "nearest_hotspot" in body
        assert body["nearest_hotspot"]["crime_count"] == 3

    def test_ml_hotspot_endpoint_integration(self, client, isolated_db):
        with isolated_db.app_context():
            crime_service.create_crime({
                "crime_type": "Theft",
                "latitude": 13.0,
                "longitude": 79.0,
                "location_name": "A",
                "district": "Vellore",
                "crime_date": "2025-01-15",
            })
            crime_service.create_crime({
                "crime_type": "Murder",
                "latitude": 13.01,
                "longitude": 79.01,
                "location_name": "A",
                "district": "Vellore",
                "crime_date": "2025-01-16",
            })

        resp = client.post("/api/ml/hotspots", json={})
        assert resp.status_code == 200
        body = resp.get_json()

        assert body["status"] == "success"
        assert "hotspots" in body
        assert "temporal" in body
        assert "patterns" in body
        assert "unsupervised" in body["analysis_type"]
        assert "no supervised prediction" in body["limitations"].lower()
