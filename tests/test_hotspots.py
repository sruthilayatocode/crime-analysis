"""
Tests for the DBSCAN-based crime hotspot detection.

Covers:
    1. DBSCAN creates a hotspot when enough crimes are geographically close.
    2. Separate geographic groups become separate clusters.
    3. Isolated points are treated as noise.
    4. Records with missing latitude/longitude are ignored.
    5. Invalid coordinates do not crash clustering.
    6. Hotspot API returns HTTP 200 with valid data.
    7. Existing risk_level filtering still works.
    8. Existing limit filtering still works.
    9. Empty dataset / no valid coordinates is handled gracefully.
"""

from __future__ import annotations

import os
import sys

import pytest

# Ensure the backend package is importable when tests
# are run from the repository root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from backend.app import app as flask_app  # noqa: E402
from backend.services.hotspot_service import (  # noqa: E402
    analyze_hotspots,
)


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #

@pytest.fixture()
def client():
    """
    Create a Flask test client using the existing application
    and its configured SQLite database.
    """
    with flask_app.test_client() as test_client:

        yield test_client


def _clear_and_seed(crimes_data):
    """
    Delete all existing crimes and insert fresh records
    using SQLAlchemy's own engine to avoid session caching
    issues.
    """
    from database import db
    from services import crime_service

    with flask_app.app_context():

        db.session.execute(db.text("DELETE FROM crimes"))
        db.session.commit()
        db.session.remove()

        for data in crimes_data:

            crime_service.create_crime(data)


# ------------------------------------------------------------------ #
# Unit tests for analyze_hotspots
# ------------------------------------------------------------------ #

class TestAnalyzeHotspots:
    """Direct tests for the DBSCAN hotspot service."""

    def test_empty_input_returns_empty_list(self):
        assert analyze_hotspots([]) == []

    def test_hotspot_created_when_crimes_are_close(self):
        """
        Five crimes within ~1 metre of each other must form
        a single hotspot.
        """
        crimes = [
            {
                "crime_type": "T1",
                "latitude": 13.043505,
                "longitude": 79.240410,
                "location_name": "Katpadi",
            },
            {
                "crime_type": "T2",
                "latitude": 13.043506,
                "longitude": 79.240411,
                "location_name": "Katpadi",
            },
            {
                "crime_type": "T3",
                "latitude": 13.043504,
                "longitude": 79.240409,
                "location_name": "Katpadi",
            },
            {
                "crime_type": "T4",
                "latitude": 13.043507,
                "longitude": 79.240412,
                "location_name": "Katpadi",
            },
            {
                "crime_type": "T5",
                "latitude": 13.043503,
                "longitude": 79.240408,
                "location_name": "Katpadi",
            },
        ]

        hotspots = analyze_hotspots(crimes)

        assert len(hotspots) == 1

        hotspot = hotspots[0]

        assert hotspot["cluster_id"] == 0
        assert hotspot["crime_count"] == 5
        assert hotspot["risk_level"] == "High"
        assert 12.9 < hotspot["centroid_latitude"] < 13.1
        assert 78.9 < hotspot["centroid_longitude"] < 79.3

    def test_separate_groups_become_separate_clusters(self):
        """
        Two tight groups separated by ~15 km must produce two
        distinct clusters, not one.
        """
        crimes = [
            {
                "crime_type": "T1",
                "latitude": 13.043505,
                "longitude": 79.240410,
                "location_name": "Katpadi",
            },
            {
                "crime_type": "T2",
                "latitude": 13.043506,
                "longitude": 79.240411,
                "location_name": "Katpadi",
            },
            {
                "crime_type": "T3",
                "latitude": 12.905489,
                "longitude": 78.940936,
                "location_name": "Pallikonda",
            },
            {
                "crime_type": "T4",
                "latitude": 12.905490,
                "longitude": 78.940937,
                "location_name": "Pallikonda",
            },
        ]

        hotspots = analyze_hotspots(crimes)

        assert len(hotspots) == 2

        counts = {h["crime_count"] for h in hotspots}
        assert counts == {2, 2}

    def test_isolated_points_are_noise(self):
        """
        A single crime far from every other crime must NOT
        appear as a hotspot.
        """
        crimes = [
            {
                "crime_type": "T1",
                "latitude": 13.043505,
                "longitude": 79.240410,
                "location_name": "Katpadi",
            },
            {
                "crime_type": "T2",
                "latitude": 13.043506,
                "longitude": 79.240411,
                "location_name": "Katpadi",
            },
            {
                "crime_type": "T3",
                "latitude": 11.000000,
                "longitude": 76.000000,
                "location_name": "Coimbatore",
            },
        ]

        hotspots = analyze_hotspots(crimes)

        assert len(hotspots) == 1
        assert hotspots[0]["crime_count"] == 2

    def test_missing_latitude_is_ignored(self):
        crimes = [
            {
                "crime_type": "T1",
                "latitude": None,
                "longitude": 79.240410,
                "location_name": "Unknown",
            },
            {
                "crime_type": "T2",
                "latitude": 13.043505,
                "longitude": 79.240410,
                "location_name": "Katpadi",
            },
        ]

        hotspots = analyze_hotspots(crimes)

        assert len(hotspots) == 0

    def test_missing_longitude_is_ignored(self):
        crimes = [
            {
                "crime_type": "T1",
                "latitude": 13.043505,
                "longitude": None,
                "location_name": "Unknown",
            },
            {
                "crime_type": "T2",
                "latitude": 13.043505,
                "longitude": 79.240410,
                "location_name": "Katpadi",
            },
        ]

        hotspots = analyze_hotspots(crimes)

        assert len(hotspots) == 0

    def test_invalid_latitude_is_ignored(self):
        crimes = [
            {
                "crime_type": "T1",
                "latitude": 999.0,
                "longitude": 79.240410,
                "location_name": "Invalid",
            },
            {
                "crime_type": "T2",
                "latitude": 13.043505,
                "longitude": 79.240410,
                "location_name": "Katpadi",
            },
        ]

        hotspots = analyze_hotspots(crimes)

        assert len(hotspots) == 0

    def test_invalid_longitude_is_ignored(self):
        crimes = [
            {
                "crime_type": "T1",
                "latitude": 13.043505,
                "longitude": 999.0,
                "location_name": "Invalid",
            },
            {
                "crime_type": "T2",
                "latitude": 13.043505,
                "longitude": 79.240410,
                "location_name": "Katpadi",
            },
        ]

        hotspots = analyze_hotspots(crimes)

        assert len(hotspots) == 0

    def test_non_numeric_coordinates_are_ignored(self):
        crimes = [
            {
                "crime_type": "T1",
                "latitude": "not-a-number",
                "longitude": 79.240410,
                "location_name": "Invalid",
            },
            {
                "crime_type": "T2",
                "latitude": 13.043505,
                "longitude": 79.240410,
                "location_name": "Katpadi",
            },
        ]

        hotspots = analyze_hotspots(crimes)

        assert len(hotspots) == 0

    def test_all_invalid_coordinates_returns_empty(self):
        crimes = [
            {
                "crime_type": "T1",
                "latitude": None,
                "longitude": None,
                "location_name": "Unknown",
            },
            {
                "crime_type": "T2",
                "latitude": "abc",
                "longitude": "def",
                "location_name": "Invalid",
            },
        ]

        hotspots = analyze_hotspots(crimes)

        assert hotspots == []

    def test_no_valid_coordinates_returns_empty(self):
        assert analyze_hotspots([{}]) == []

    def test_risk_level_mapping(self):
        crimes = [
            {
                "crime_type": f"T{i}",
                "latitude": 13.0,
                "longitude": 79.0 + i * 0.00001,
                "location_name": "Area",
            }
            for i in range(7)
        ]

        hotspots = analyze_hotspots(crimes)

        assert len(hotspots) == 1
        assert hotspots[0]["risk_level"] == "High"

    def test_medium_risk_level(self):
        crimes = [
            {
                "crime_type": f"T{i}",
                "latitude": 13.0,
                "longitude": 79.0 + i * 0.00001,
                "location_name": "Area",
            }
            for i in range(4)
        ]

        hotspots = analyze_hotspots(crimes)

        assert len(hotspots) == 1
        assert hotspots[0]["risk_level"] == "Medium"

    def test_low_risk_level(self):
        crimes = [
            {
                "crime_type": f"T{i}",
                "latitude": 13.0,
                "longitude": 79.0 + i * 0.00001,
                "location_name": "Area",
            }
            for i in range(2)
        ]

        hotspots = analyze_hotspots(crimes)

        assert len(hotspots) == 1
        assert hotspots[0]["risk_level"] == "Low"


# ------------------------------------------------------------------ #
# Integration tests for the API
# ------------------------------------------------------------------ #

class TestHotspotAPI:
    """Tests for GET /api/crimes/hotspots."""

    def test_hotspots_endpoint_returns_200(self, client):
        resp = client.get("/api/crimes/hotspots")
        assert resp.status_code == 200

    def test_hotspots_response_schema(self, client):
        resp = client.get("/api/crimes/hotspots")
        body = resp.get_json()

        assert body["success"] is True
        assert "count" in body
        assert "data" in body

        for hotspot in body["data"]:

            assert "cluster_id" in hotspot
            assert "crime_count" in hotspot
            assert "centroid_latitude" in hotspot
            assert "centroid_longitude" in hotspot
            assert "risk_level" in hotspot

    def test_hotspots_with_empty_database(self, client):
        _clear_and_seed([])

        resp = client.get("/api/crimes/hotspots")
        body = resp.get_json()

        assert body["count"] == 0
        assert body["data"] == []

    def test_risk_level_filter(self, client):
        _clear_and_seed([
            {
                "crime_type": "Test1",
                "latitude": 13.043505,
                "longitude": 79.240410,
                "location_name": "Katpadi",
            },
            {
                "crime_type": "Test2",
                "latitude": 13.043506,
                "longitude": 79.240411,
                "location_name": "Katpadi",
            },
            {
                "crime_type": "Test3",
                "latitude": 12.905489,
                "longitude": 78.940936,
                "location_name": "Pallikonda",
            },
        ])

        resp = client.get("/api/crimes/hotspots?risk_level=Low")
        body = resp.get_json()

        assert resp.status_code == 200
        assert body["success"] is True
        for hotspot in body["data"]:
            assert hotspot["risk_level"] == "Low"

    def test_limit_filter(self, client):
        _clear_and_seed([
            {
                "crime_type": "Test1",
                "latitude": 13.043505,
                "longitude": 79.240410,
                "location_name": "Katpadi",
            },
            {
                "crime_type": "Test2",
                "latitude": 13.043506,
                "longitude": 79.240411,
                "location_name": "Katpadi",
            },
            {
                "crime_type": "Test3",
                "latitude": 13.043507,
                "longitude": 79.240412,
                "location_name": "Katpadi",
            },
            {
                "crime_type": "Test4",
                "latitude": 13.043508,
                "longitude": 79.240413,
                "location_name": "Katpadi",
            },
            {
                "crime_type": "Test5",
                "latitude": 13.043509,
                "longitude": 79.240414,
                "location_name": "Katpadi",
            },
            {
                "crime_type": "Test6",
                "latitude": 12.905489,
                "longitude": 78.940936,
                "location_name": "Pallikonda",
            },
        ])

        resp = client.get("/api/crimes/hotspots?limit=1")
        body = resp.get_json()

        assert resp.status_code == 200
        assert len(body["data"]) == 1

    def test_alt_hotspots_alias(self, client):
        resp = client.get("/api/hotspots")
        assert resp.status_code == 200

    def test_records_without_coordinates_dont_crash(self, client):
        _clear_and_seed([
            {
                "crime_type": "NoCoords",
                "location_name": "Unknown",
            },
            {
                "crime_type": "AlsoNoCoords",
                "location_name": "Somewhere",
            },
        ])

        resp = client.get("/api/crimes/hotspots")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["count"] == 0


# ------------------------------------------------------------------ #
# Integration tests for existing CRUD endpoints
# ------------------------------------------------------------------ #

class TestCrimesCRUD:
    """Verify existing CRUD endpoints still work."""

    def test_get_crimes(self, client):
        resp = client.get("/api/crimes")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert "count" in body

    def test_get_crime_by_id(self, client):
        _clear_and_seed([
            {
                "crime_type": "Test",
                "latitude": 13.0,
                "longitude": 79.0,
            }
        ])

        resp = client.get("/api/crimes/1")
        assert resp.status_code == 200

    def test_post_crime(self, client):
        resp = client.post(
            "/api/crimes",
            json={
                "crime_type": "Test",
                "latitude": 13.0,
                "longitude": 79.0,
            },
        )
        assert resp.status_code == 201
        assert resp.get_json()["success"] is True

    def test_put_crime(self, client):
        _clear_and_seed([
            {
                "crime_type": "Original",
                "latitude": 13.0,
                "longitude": 79.0,
            }
        ])

        resp = client.put(
            "/api/crimes/1",
            json={"crime_type": "Updated"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_delete_crime(self, client):
        _clear_and_seed([
            {
                "crime_type": "ToDelete",
                "latitude": 13.0,
                "longitude": 79.0,
            }
        ])

        resp = client.delete("/api/crimes/1")
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True


# ------------------------------------------------------------------ #
# Integration tests for the proximity-check endpoint
# ------------------------------------------------------------------ #

class TestProximityCheck:
    """Verify the alert endpoint works with DBSCAN hotspots."""

    def test_proximity_check_returns_200(self, client):
        _clear_and_seed([
            {
                "crime_type": "Test",
                "latitude": 13.043505,
                "longitude": 79.240410,
                "location_name": "Katpadi",
            },
            {
                "crime_type": "Test2",
                "latitude": 13.043506,
                "longitude": 79.240411,
                "location_name": "Katpadi",
            },
            {
                "crime_type": "Test3",
                "latitude": 13.043507,
                "longitude": 79.240412,
                "location_name": "Katpadi",
            },
        ])

        resp = client.post(
            "/api/proximity-check",
            json={
                "latitude": 13.05,
                "longitude": 79.24,
                "alert_radius_meters": 500,
            },
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert "nearest_hotspot" in body
        assert body["nearest_hotspot"]["crime_count"] == 3
