"""
Tests for backend/services/ml_prediction_service.py.

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
from services.ml_prediction_service import MLAnalyticsService  # noqa: E402
from services import crime_service  # noqa: E402


# ------------------------------------------------------------------ #
# Isolated database fixture
# ------------------------------------------------------------------ #


@pytest.fixture(autouse=True)
def isolated_db(tmp_path):
    db_path = tmp_path / "test_ml_service.db"
    db_uri = "sqlite:///" + str(db_path)

    test_app = Flask(__name__)
    test_app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    test_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(test_app)

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
# Unit tests for MLAnalyticsService
# ------------------------------------------------------------------ #


class TestMLAnalyticsService:
    def test_empty_database(self, isolated_db):
        with isolated_db.app_context():
            records = crime_service.list_crimes()

        service = MLAnalyticsService()
        result = service.get_full_analysis(records)

        assert result["status"] == "success"
        assert result["hotspots"]["metrics"]["valid_coordinates"] == 0
        assert result["temporal"]["data"]["valid_dates"] == 0

    def test_hotspot_analysis_with_records(self, isolated_db):
        _seed_crimes(isolated_db, [
            {
                "crime_type": "Theft",
                "latitude": 13.0,
                "longitude": 79.0,
                "location_name": "A",
                "district": "Vellore",
                "severity_score": 5,
                "risk_level": "Medium",
            },
            {
                "crime_type": "Theft",
                "latitude": 13.01,
                "longitude": 79.01,
                "location_name": "A",
                "district": "Vellore",
                "severity_score": 4,
                "risk_level": "Medium",
            },
        ])

        with isolated_db.app_context():
            records = crime_service.list_crimes()

        service = MLAnalyticsService()
        result = service.get_hotspot_analysis(records)

        assert result["status"] == "success"
        assert result["analysis_type"] == "unsupervised_hotspot_detection"
        assert result["method"] == "DBSCAN"

    def test_temporal_analysis_with_records(self, isolated_db):
        _seed_crimes(isolated_db, [
            {
                "crime_type": "Theft",
                "crime_date": "2025-01-15",
                "location_name": "A",
                "district": "Vellore",
            },
            {
                "crime_type": "Murder",
                "crime_date": "2025-01-20",
                "location_name": "B",
                "district": "Vellore",
            },
        ])

        with isolated_db.app_context():
            records = crime_service.list_crimes()

        service = MLAnalyticsService()
        result = service.get_temporal_analysis(records)

        assert result["status"] == "success"
        assert result["analysis_type"] == "descriptive_publication_date_analysis"
        assert result["data"]["monthly_counts"]["2025-01"] == 2

    def test_pattern_analysis_with_records(self, isolated_db):
        _seed_crimes(isolated_db, [
            {
                "crime_type": "Murder",
                "severity_score": 10,
                "risk_level": "Critical",
                "location_name": "A",
                "district": "Vellore",
            },
            {
                "crime_type": "Theft",
                "severity_score": 4,
                "risk_level": "Medium",
                "location_name": "B",
                "district": "Vellore",
            },
        ])

        with isolated_db.app_context():
            records = crime_service.list_crimes()

        service = MLAnalyticsService()
        result = service.get_pattern_analysis(records)

        assert result["status"] == "success"
        assert result["data"]["crime_type_distribution"]["Murder"] == 1
        assert result["data"]["crime_type_distribution"]["Theft"] == 1

    def test_full_analysis_returns_all_sections(self, isolated_db):
        _seed_crimes(isolated_db, [
            {
                "crime_type": "Theft",
                "latitude": 13.0,
                "longitude": 79.0,
                "crime_date": "2025-01-15",
                "location_name": "A",
                "district": "Vellore",
                "severity_score": 5,
                "risk_level": "Medium",
            },
        ])

        with isolated_db.app_context():
            records = crime_service.list_crimes()

        service = MLAnalyticsService()
        result = service.get_full_analysis(records)

        assert "hotspots" in result
        assert "temporal" in result
        assert "patterns" in result

    def test_custom_dbscan_parameters(self, isolated_db):
        _seed_crimes(isolated_db, [
            {
                "crime_type": "Theft",
                "latitude": 13.0,
                "longitude": 79.0,
                "location_name": "A",
                "district": "Vellore",
            },
            {
                "crime_type": "Theft",
                "latitude": 13.5,
                "longitude": 79.5,
                "location_name": "B",
                "district": "Vellore",
            },
        ])

        with isolated_db.app_context():
            records = crime_service.list_crimes()

        service = MLAnalyticsService()
        result = service.get_hotspot_analysis(records, eps_km=100.0, min_samples=1)

        assert result["parameters"]["eps_km"] == 100.0
        assert result["parameters"]["min_samples"] == 1

    def test_no_fabricated_predictions(self, isolated_db):
        _seed_crimes(isolated_db, [
            {
                "crime_type": "Theft",
                "latitude": 13.0,
                "longitude": 79.0,
                "crime_date": "2025-01-15",
                "location_name": "A",
                "district": "Vellore",
                "severity_score": 5,
                "risk_level": "Medium",
            },
        ])

        with isolated_db.app_context():
            records = crime_service.list_crimes()

        service = MLAnalyticsService()
        result = service.get_full_analysis(records)

        result_str = str(result).lower()
        assert "prediction" not in result_str or "does not predict" in result_str
