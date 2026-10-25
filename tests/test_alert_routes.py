"""
Tests for backend/routes/alert_routes.py.

Uses isolated temporary databases where database access is required.
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


# ------------------------------------------------------------------ #
# Isolated database fixture
# ------------------------------------------------------------------ #


@pytest.fixture(autouse=True)
def isolated_db(tmp_path):
    db_path = tmp_path / "test_alert_routes.db"
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
# Helpers
# ------------------------------------------------------------------ #


def _seed_crimes(isolated_db, crimes_data):
    with isolated_db.app_context():
        for data in crimes_data:
            crime_service.create_crime(data)


# ------------------------------------------------------------------ #
# Unit tests for /api/proximity-check route
# ------------------------------------------------------------------ #


class TestProximityCheckRoute:
    def test_missing_json_returns_400(self, client):
        resp = client.post(
            "/api/proximity-check",
            data="not-json",
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_missing_latitude_returns_400(self, client):
        resp = client.post(
            "/api/proximity-check",
            json={"longitude": 79.0},
        )
        assert resp.status_code == 400
        body = resp.get_json()
        assert "missing_fields" in body.get("details", {})

    def test_missing_longitude_returns_400(self, client):
        resp = client.post(
            "/api/proximity-check",
            json={"latitude": 13.0},
        )
        assert resp.status_code == 400

    def test_invalid_latitude_returns_400(self, client):
        resp = client.post(
            "/api/proximity-check",
            json={"latitude": 999.0, "longitude": 79.0},
        )
        assert resp.status_code == 400

    def test_invalid_longitude_returns_400(self, client):
        resp = client.post(
            "/api/proximity-check",
            json={"latitude": 13.0, "longitude": -999.0},
        )
        assert resp.status_code == 400

    def test_non_numeric_coordinates_returns_400(self, client):
        resp = client.post(
            "/api/proximity-check",
            json={"latitude": "abc", "longitude": "xyz"},
        )
        assert resp.status_code == 400

    def test_negative_radius_returns_400(self, client):
        resp = client.post(
            "/api/proximity-check",
            json={"latitude": 13.0, "longitude": 79.0, "alert_radius_meters": -1},
        )
        assert resp.status_code == 400

    def test_zero_radius_returns_400(self, client):
        resp = client.post(
            "/api/proximity-check",
            json={"latitude": 13.0, "longitude": 79.0, "alert_radius_meters": 0},
        )
        assert resp.status_code == 400

    def test_empty_database_returns_no_alert(self, client):
        resp = client.post(
            "/api/proximity-check",
            json={"latitude": 13.0, "longitude": 79.0},
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert body["alert"] is False
        assert body["nearby_crimes"] == []
        assert body["nearby_hotspots"] == []

    def test_nearby_crime_triggers_alert(self, client, isolated_db):
        _seed_crimes(isolated_db, [
            {
                "crime_type": "Theft",
                "latitude": 13.0,
                "longitude": 79.0,
                "location_name": "A",
                "district": "Vellore",
            },
        ])

        resp = client.post(
            "/api/proximity-check",
            json={"latitude": 13.001, "longitude": 79.001, "alert_radius_meters": 5000},
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert body["alert"] is True
        assert len(body["nearby_crimes"]) == 1
        assert body["nearby_crimes"][0]["crime_type"] == "Theft"

    def test_no_nearby_crimes_no_alert(self, client, isolated_db):
        _seed_crimes(isolated_db, [
            {
                "crime_type": "Theft",
                "latitude": 14.0,
                "longitude": 80.0,
                "location_name": "B",
                "district": "Vellore",
            },
        ])

        resp = client.post(
            "/api/proximity-check",
            json={"latitude": 13.0, "longitude": 79.0, "alert_radius_meters": 100},
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["alert"] is False

    def test_response_contains_nearest_hotspot(self, client, isolated_db):
        _seed_crimes(isolated_db, [
            {
                "crime_type": "Theft",
                "latitude": 13.043505,
                "longitude": 79.240410,
                "location_name": "Katpadi",
                "district": "Vellore",
            },
            {
                "crime_type": "Theft",
                "latitude": 13.043506,
                "longitude": 79.240411,
                "location_name": "Katpadi",
                "district": "Vellore",
            },
            {
                "crime_type": "Theft",
                "latitude": 13.043507,
                "longitude": 79.240412,
                "location_name": "Katpadi",
                "district": "Vellore",
            },
        ])

        resp = client.post(
            "/api/proximity-check",
            json={"latitude": 13.043505, "longitude": 79.240410, "alert_radius_meters": 5000},
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert "nearest_hotspot" in body
        assert body["nearest_hotspot"]["crime_count"] == 3

    def test_response_structure(self, client, isolated_db):
        _seed_crimes(isolated_db, [
            {
                "crime_type": "Theft",
                "latitude": 13.0,
                "longitude": 79.0,
                "location_name": "A",
                "district": "Vellore",
            },
        ])

        resp = client.post(
            "/api/proximity-check",
            json={"latitude": 13.001, "longitude": 79.001, "alert_radius_meters": 5000},
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert "success" in body
        assert "alert" in body
        assert "message" in body
        assert "user_location" in body
        assert "nearby_crimes" in body
        assert "nearby_hotspots" in body
        assert "checked_radius_meters" in body
        assert "limitations" in body

    def test_no_traceback_in_response(self, client, isolated_db):
        _seed_crimes(isolated_db, [
            {
                "crime_type": "Theft",
                "latitude": 13.0,
                "longitude": 79.0,
                "location_name": "A",
                "district": "Vellore",
            },
        ])

        resp = client.post(
            "/api/proximity-check",
            json={"latitude": 13.0, "longitude": 79.0, "alert_radius_meters": 500},
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert "Traceback" not in str(body)
        assert "sqlite3" not in str(body).lower()
        assert "OperationalError" not in str(body)
