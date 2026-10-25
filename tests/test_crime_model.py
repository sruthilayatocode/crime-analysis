"""
Tests for the extended Crime model and new metadata fields.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from flask import Flask  # noqa: E402

from app import app as flask_app  # noqa: E402
from models.crime import Crime  # noqa: E402
from services import crime_service  # noqa: E402
from database import db  # noqa: E402
from routes.crime_routes import crime_bp  # noqa: E402
from routes.alert_routes import alert_bp  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_db(tmp_path):
    db_path = tmp_path / "test_crime_model.db"
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


class TestCrimeModelMetadata:
    """New metadata fields on the Crime model."""

    def test_create_crime_with_metadata(self, client, isolated_db):
        with isolated_db.app_context():
            crime = Crime(
                crime_type="Fraud",
                article_id="test-123",
                title="Test Title",
                source="Test Source",
                url="https://example.com/test",
                district="Test District",
                location_confidence="HIGH",
                location_source="Geocoder",
                severity_score=5,
                risk_level="Medium",
            )
            db.session.add(crime)
            db.session.commit()

            assert crime.article_id == "test-123"
            assert crime.title == "Test Title"
            assert crime.source == "Test Source"
            assert crime.url == "https://example.com/test"
            assert crime.district == "Test District"
            assert crime.location_confidence == "HIGH"
            assert crime.location_source == "Geocoder"
            assert crime.severity_score == 5
            assert crime.risk_level == "Medium"

            result = crime.to_dict()
            assert result["article_id"] == "test-123"
            assert result["title"] == "Test Title"
            assert result["source"] == "Test Source"
            assert result["url"] == "https://example.com/test"
            assert result["district"] == "Test District"
            assert result["location_confidence"] == "HIGH"
            assert result["location_source"] == "Geocoder"
            assert result["severity_score"] == 5
            assert result["risk_level"] == "Medium"

    def test_api_returns_new_fields(self, client, isolated_db):
        with isolated_db.app_context():
            crime_service.create_crime({
                "crime_type": "Fraud",
                "article_id": "api-123",
                "title": "API Title",
                "source": "API Source",
                "url": "https://example.com/api",
                "district": "API District",
                "location_confidence": "LOW",
                "location_source": "Manual",
                "severity_score": 3,
                "risk_level": "Low",
            })

        resp = client.get("/api/crimes/1")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        data = body["data"]
        assert data["article_id"] == "api-123"
        assert data["title"] == "API Title"
        assert data["source"] == "API Source"
        assert data["url"] == "https://example.com/api"
        assert data["district"] == "API District"
        assert data["location_confidence"] == "LOW"
        assert data["location_source"] == "Manual"
        assert data["severity_score"] == 3
        assert data["risk_level"] == "Low"
