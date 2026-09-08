"""
Tests for backend/services/alert_service.py.

Uses the real proximity_service module and synthetic data.
Does not touch the production database.
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest

from services.alert_service import AlertService


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #


def _make_alert_service():
    import services.proximity_service as proximity_service
    return AlertService(
        proximity_service=proximity_service,
        ml_analytics_service=None,
    )


def _crime(latitude, longitude, crime_type="Theft"):
    return {
        "id": 1,
        "crime_type": crime_type,
        "latitude": latitude,
        "longitude": longitude,
        "location_name": "A",
    }


# ------------------------------------------------------------------ #
# Unit tests for AlertService
# ------------------------------------------------------------------ #


class TestAlertService:
    def test_alert_when_nearby_crime(self):
        service = _make_alert_service()
        crimes = [_crime(13.0, 79.0)]

        result = service.check_alert(
            user_latitude=13.001,
            user_longitude=79.001,
            crimes=crimes,
            alert_radius_meters=500.0,
        )

        assert result["alert"] is True
        assert len(result["nearby_crimes"]) == 1
        assert result["status"] == "success"

    def test_no_alert_when_far(self):
        service = _make_alert_service()
        crimes = [_crime(13.0, 79.0)]

        result = service.check_alert(
            user_latitude=14.0,
            user_longitude=80.0,
            crimes=crimes,
            alert_radius_meters=500.0,
        )

        assert result["alert"] is False
        assert result["nearby_crimes"] == []

    def test_empty_crimes_no_alert(self):
        service = _make_alert_service()
        result = service.check_alert(
            user_latitude=13.0,
            user_longitude=79.0,
            crimes=[],
            alert_radius_meters=500.0,
        )

        assert result["alert"] is False
        assert result["nearby_crimes"] == []

    def test_nearby_hotspots_included(self):
        import services.proximity_service as proximity_service
        from ml.hotspot_model import HotspotModel

        model = HotspotModel(eps_km=10.0, min_samples=2)
        coords = [(13.0, 79.0), (13.01, 79.01)]
        model.fit(coords)
        hotspots = model.get_cluster_summary()

        service = AlertService(
            proximity_service=proximity_service,
            ml_analytics_service=None,
        )

        crimes = [_crime(13.0, 79.0)]

        result = service.check_alert(
            user_latitude=13.001,
            user_longitude=79.001,
            crimes=crimes,
            hotspots=hotspots,
            alert_radius_meters=5000.0,
        )

        assert result["nearby_hotspots"] is not None
        assert result["status"] == "success"

    def test_response_structure(self):
        service = _make_alert_service()
        crimes = [_crime(13.0, 79.0)]

        result = service.check_alert(
            user_latitude=13.0,
            user_longitude=79.0,
            crimes=crimes,
            alert_radius_meters=500.0,
        )

        assert "status" in result
        assert "alert" in result
        assert "message" in result
        assert "nearby_crimes" in result
        assert "nearby_hotspots" in result
        assert "checked_radius_km" in result
        assert "checked_radius_meters" in result
        assert "limitations" in result

    def test_no_fabricated_probabilities(self):
        service = _make_alert_service()
        crimes = [_crime(13.0, 79.0)]

        result = service.check_alert(
            user_latitude=13.001,
            user_longitude=79.001,
            crimes=crimes,
            alert_radius_meters=500.0,
        )

        result_str = str(result).lower()
        assert "probability" not in result_str
        assert "confidence" not in result_str
        assert "prediction" not in result_str

    def test_custom_max_results(self):
        service = _make_alert_service()
        crimes = [
            _crime(13.0 + i * 0.001, 79.0 + i * 0.001)
            for i in range(10)
        ]

        result = service.check_alert(
            user_latitude=13.0,
            user_longitude=79.0,
            crimes=crimes,
            alert_radius_meters=50000.0,
            max_results=3,
        )

        assert len(result["nearby_crimes"]) <= 3
