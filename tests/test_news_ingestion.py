"""
Tests for the news-to-database ingestion service.

These tests run against a freshly created, isolated temporary SQLite
database. They NEVER touch the real development database at
``backend/instance/crimesense.db`` and never execute destructive
statements (DELETE/DROP/TRUNCATE) against it.
"""

from __future__ import annotations

import os
import sys

import pytest

# Make "database", "models", "services", "app" and "config"
# (top-level backend modules) importable, like the existing
# tests in this directory. ``backend`` itself resolves through
# pytest's rootdir insertion so ``from backend.app import app``
# keeps working without us adding the repository root.
BACKEND_DIR = os.path.join(
    os.path.dirname(__file__), "..", "backend"
)
sys.path.insert(0, BACKEND_DIR)

from flask import Flask  # noqa: E402

from database import db  # noqa: E402
from models.crime import Crime  # noqa: E402
from backend.app import app as real_app  # noqa: E402
import services.news_ingestion_service as ingestion_service  # noqa: E402
from services.news_ingestion_service import normalize_record  # noqa: E402


# ---------------------------------------------------------------------------
# Isolated database fixture
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def isolated_db(tmp_path):
    """
    Provide a per-test isolated SQLite database.

    A throwaway Flask app is registered on the shared ``db``
    extension and pointed at a temp file. The ingestion service's
    module-level ``app`` reference is rebound to this app so that
    ``ingest_records`` / ``ingest_csv`` write only to the temp DB.

    On teardown the temp engine is disposed and removed, leaving the
    real application (and its development database) untouched.
    No DELETE/DROP/TRUNCATE is ever issued against the real DB.
    """

    db_path = tmp_path / "test_news_ingestion.db"
    db_uri = "sqlite:///" + str(db_path)

    test_app = Flask(__name__)
    test_app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    test_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Register the shared SQLAlchemy extension on the temp app.
    db.init_app(test_app)

    # Redirect the service's app reference to the temp app so its
    # ``with app.app_context():`` blocks hit the isolated DB.
    original_app = ingestion_service.app
    ingestion_service.app = test_app

    with test_app.app_context():
        db.create_all()
        yield test_app

    # --- teardown ---------------------------------------------------------
    ingestion_service.app = original_app

    with test_app.app_context():
        db.session.remove()
        engines = db._app_engines.get(test_app, {})
        for engine in engines.values():
            engine.dispose()
        db._app_engines.pop(test_app, None)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _base_record(**overrides):
    """A complete, valid news-pipeline record."""

    record = {
        "article_id": "ART-001",
        "title": "Test Crime",
        "published_date": "Thu, 30 Jan 2025 08:00:00 GMT",
        "source": "TestSource",
        "url": "https://example.com/art-001",
        "crime_type": "Murder",
        "description": "A test crime occurred here.",
        "district": "District One",
        "locality": "Locality A",
        "latitude": "10.0",
        "longitude": "20.0",
        "location_confidence": "high",
        "location_source": "geocoder",
        "severity_score": "5",
        "risk_level": "HIGH",
    }
    record.update(overrides)
    return record


def _crimes():
    """Return all crimes ordered by id (within an active context)."""

    return (
        Crime.query
        .order_by(Crime.id)
        .all()
    )


def _count():
    """Return the number of crimes (within an active context)."""

    return Crime.query.count()


# ---------------------------------------------------------------------------
# Ingestion behaviour
# ---------------------------------------------------------------------------


class TestIngestion:
    def test_new_article_is_inserted(self):
        stats = ingestion_service.ingest_records(
            [_base_record()]
        )

        assert stats["total"] == 1
        assert stats["inserted"] == 1
        assert stats["updated"] == 0
        assert _count() == 1

    def test_existing_updated_when_article_id_matches(self):
        ingestion_service.ingest_records(
            [_base_record(title="Original")]
        )

        stats = ingestion_service.ingest_records(
            [_base_record(title="Updated")]
        )

        assert stats["updated"] == 1
        assert stats["inserted"] == 0
        assert _count() == 1
        assert _crimes()[0].title == "Updated"

    def test_existing_updated_when_url_matches(self):
        ingestion_service.ingest_records(
            [
                _base_record(
                    article_id="ART-001",
                    url="https://example.com/abc",
                )
            ]
        )

        stats = ingestion_service.ingest_records(
            [
                _base_record(
                    article_id="ART-002",
                    url="https://example.com/abc",
                    title="Via URL",
                )
            ]
        )

        assert stats["updated"] == 1
        assert _count() == 1
        assert _crimes()[0].title == "Via URL"

    def test_duplicate_within_batch_prevented(self):
        record = _base_record()

        stats = ingestion_service.ingest_records(
            [record, dict(record)]
        )

        assert stats["inserted"] == 1
        assert stats["duplicates"] == 1
        assert _count() == 1

    def test_repeated_ingestion_creates_no_extra_rows(self):
        first = ingestion_service.ingest_records(
            [_base_record()]
        )
        second = ingestion_service.ingest_records(
            [_base_record()]
        )

        assert first["inserted"] == 1
        assert second["updated"] == 1
        assert second["inserted"] == 0
        assert _count() == 1


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------


class TestNormalizeCoordinates:
    def test_blank_latitude_becomes_none(self):
        record = normalize_record(
            _base_record(latitude="")
        )
        assert record["latitude"] is None

    def test_blank_longitude_becomes_none(self):
        record = normalize_record(
            _base_record(longitude="   ")
        )
        assert record["longitude"] is None


class TestValidation:
    def test_invalid_latitude_rejected(self):
        stats = ingestion_service.ingest_records(
            [_base_record(latitude="200")]
        )

        assert stats["invalid"] == 1
        assert stats["inserted"] == 0
        assert _count() == 0

    def test_invalid_longitude_rejected(self):
        stats = ingestion_service.ingest_records(
            [_base_record(longitude="-999")]
        )

        assert stats["invalid"] == 1
        assert _count() == 0

    def test_invalid_record_does_not_abort_batch(self):
        stats = ingestion_service.ingest_records(
            [
                _base_record(),
                _base_record(
                    article_id="BAD",
                    latitude="not-a-number",
                ),
            ]
        )

        assert stats["total"] == 2
        assert stats["inserted"] == 1
        assert stats["invalid"] == 1
        assert _count() == 1


class TestDateNormalization:
    def test_rfc1123_date_normalized(self):
        ingestion_service.ingest_records(
            [
                _base_record(
                    published_date=(
                        "Thu, 30 Jan 2025 08:00:00 GMT"
                    )
                )
            ]
        )

        assert _crimes()[0].crime_date == "2025-01-30"

    def test_iso_datetime_normalized(self):
        ingestion_service.ingest_records(
            [
                _base_record(
                    article_id="ISO-DT",
                    url="https://example.com/iso-dt",
                    published_date="2025-02-15T10:30:00",
                )
            ]
        )

        assert _crimes()[0].crime_date == "2025-02-15"

    def test_iso_date_only_normalized(self):
        ingestion_service.ingest_records(
            [
                _base_record(
                    article_id="ISO-D",
                    url="https://example.com/iso-d",
                    published_date="2025-02-15",
                )
            ]
        )

        assert _crimes()[0].crime_date == "2025-02-15"


class TestFieldMapping:
    def test_locality_maps_to_location_name(self):
        ingestion_service.ingest_records(
            [_base_record(locality="My Locality")]
        )

        assert _crimes()[0].location_name == "My Locality"

    def test_published_date_maps_to_crime_date(self):
        ingestion_service.ingest_records(
            [_base_record(published_date="2025-04-05")]
        )

        assert _crimes()[0].crime_date == "2025-04-05"

    def test_risk_level_maps_to_severity_when_absent(self):
        ingestion_service.ingest_records(
            [_base_record()]
        )

        crime = _crimes()[0]
        assert crime.severity == "HIGH"
        assert crime.risk_level == "HIGH"

    def test_explicit_severity_takes_priority_over_risk(self):
        record = normalize_record(
            {**_base_record(), "severity": "LOW"}
        )

        assert record["severity"] == "LOW"


class TestRobustness:
    def test_missing_optional_metadata_does_not_crash(self):
        minimal = {
            "article_id": "SOLO-1",
            "crime_type": "Theft",
            "published_date": "2025-05-05",
            "latitude": "1.0",
            "longitude": "2.0",
        }

        stats = ingestion_service.ingest_records([minimal])

        assert stats["inserted"] == 1
        crime = _crimes()[0]
        assert crime.title is None
        assert crime.source is None
        assert crime.description is None

    def test_long_description_respects_model_limit(self):
        limit = ingestion_service.COLUMN_LIMITS["description"]

        ingestion_service.ingest_records(
            [_base_record(description="Z" * (limit + 100))]
        )

        assert len(_crimes()[0].description) == limit

    def test_invalid_severity_score_handled_safely(self):
        stats = ingestion_service.ingest_records(
            [
                _base_record(),
                _base_record(
                    article_id="ART-002",
                    url="https://example.com/art-002",
                    severity_score="not-a-number",
                ),
            ]
        )

        assert stats["inserted"] == 1
        assert stats["invalid"] == 1
        assert _count() == 1


# ---------------------------------------------------------------------------
# CSV ingestion
# ---------------------------------------------------------------------------


class TestCsvIngestion:
    def test_csv_fixture_ingested(self, tmp_path):
        csv_path = tmp_path / "news.csv"
        csv_path.write_text(
            "article_id,crime_type,locality,latitude,longitude,"
            "risk_level,severity_score,published_date\n"
            "C1,Burglary,Downtown,12.3,45.6,LOW,3,2025-06-01\n"
            'C2,Fraud,Uptown,,,"HIGH",7,"Thu, 02 Jun 2025 08:00:00 GMT"\n',
            encoding="utf-8",
        )

        stats = ingestion_service.ingest_csv(str(csv_path))

        assert stats["total"] == 2
        assert stats["inserted"] == 2
        assert stats["updated"] == 0
        assert _count() == 2
        assert stats["missing_coordinates"] == 1

        crimes = {c.article_id: c for c in _crimes()}

        c1 = crimes["C1"]
        assert c1.crime_type == "Burglary"
        assert c1.location_name == "Downtown"
        assert c1.latitude == 12.3
        assert c1.longitude == 45.6
        assert c1.severity == "LOW"
        assert c1.severity_score == 3
        assert c1.crime_date == "2025-06-01"

        c2 = crimes["C2"]
        assert c2.location_name == "Uptown"
        assert c2.latitude is None
        assert c2.longitude is None
        assert c2.severity == "HIGH"
        assert c2.severity_score == 7
        assert c2.crime_date == "2025-06-02"
