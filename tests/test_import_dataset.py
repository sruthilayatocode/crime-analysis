"""
Tests for the dataset importer.
"""

from __future__ import annotations

import csv
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest

from backend.app import app as flask_app  # noqa: E402
from services import crime_service  # noqa: E402
from backend import import_dataset  # noqa: E402
from database import db  # noqa: E402


@pytest.fixture()
def client():
    with flask_app.test_client() as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clear_crimes():
    with flask_app.app_context():
        db.session.execute(db.text("DELETE FROM crimes"))
        db.session.commit()
        db.session.remove()
    yield
    with flask_app.app_context():
        db.session.execute(db.text("DELETE FROM crimes"))
        db.session.commit()
        db.session.remove()


def _write_csv(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".csv", text=True)
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    return path


class TestCsvFieldMapping:
    def test_all_fields_mapped(self, client):
        csv_content = (
            "article_id,title,published_date,source,url,crime_type,description,district,locality,latitude,longitude,location_confidence,location_source,severity_score,risk_level\n"
            'art-1,Test Article,"Fri, 12 Jun 2026 07:00:00 GMT",The Hindu,https://example.com/1,Fraud,Desc,Vellore,Katpadi,13.043505,79.240410,HIGH,Geocoder,5,Medium\n'
        )
        path = _write_csv(csv_content)
        old_path = import_dataset.DATASET_PATH
        import_dataset.DATASET_PATH = path
        try:
            import_dataset.main([])
        finally:
            import_dataset.DATASET_PATH = old_path
            os.remove(path)

        with flask_app.app_context():
            crimes = crime_service.list_crimes()
            assert len(crimes) == 1
            c = crimes[0]
            assert c["article_id"] == "art-1"
            assert c["title"] == "Test Article"
            assert c["source"] == "The Hindu"
            assert c["url"] == "https://example.com/1"
            assert c["crime_type"] == "Fraud"
            assert c["description"] == "Desc"
            assert c["district"] == "Vellore"
            assert c["location_name"] == "Katpadi"
            assert c["latitude"] == 13.043505
            assert c["longitude"] == 79.240410
            assert c["location_confidence"] == "HIGH"
            assert c["location_source"] == "Geocoder"
            assert c["severity_score"] == 5
            assert c["risk_level"] == "Medium"
            assert c["severity"] == "Medium"
            assert c["crime_date"] == "2026-06-12"


class TestDuplicateHandling:
    def test_duplicate_article_id_skipped_in_csv(self, client):
        csv_content = (
            "article_id,title,published_date,source,url,crime_type,description,district,locality,latitude,longitude,location_confidence,location_source,severity_score,risk_level\n"
            'art-1,First,"Fri, 12 Jun 2026 07:00:00 GMT",The Hindu,https://example.com/1,Fraud,Desc,Vellore,Katpadi,13.043505,79.240410,HIGH,Geocoder,5,Medium\n'
            'art-1,Second,"Fri, 12 Jun 2026 07:00:00 GMT",The Hindu,https://example.com/1,Fraud,Desc2,Vellore,Katpadi,13.043505,79.240410,HIGH,Geocoder,5,Medium\n'
        )
        path = _write_csv(csv_content)
        old_path = import_dataset.DATASET_PATH
        import_dataset.DATASET_PATH = path
        try:
            import_dataset.main([])
        finally:
            import_dataset.DATASET_PATH = old_path
            os.remove(path)

        with flask_app.app_context():
            crimes = crime_service.list_crimes()
            assert len(crimes) == 1
            assert crimes[0]["title"] == "First"

    def test_repeated_import_updates_existing(self, client):
        csv_content = (
            "article_id,title,published_date,source,url,crime_type,description,district,locality,latitude,longitude,location_confidence,location_source,severity_score,risk_level\n"
            'art-1,Original,"Fri, 12 Jun 2026 07:00:00 GMT",The Hindu,https://example.com/1,Fraud,Desc,Vellore,Katpadi,13.043505,79.240410,HIGH,Geocoder,5,Medium\n'
        )
        path = _write_csv(csv_content)
        old_path = import_dataset.DATASET_PATH
        import_dataset.DATASET_PATH = path
        try:
            import_dataset.main([])
            import_dataset.main([])
        finally:
            import_dataset.DATASET_PATH = old_path
            os.remove(path)

        with flask_app.app_context():
            crimes = crime_service.list_crimes()
            assert len(crimes) == 1
            assert crimes[0]["title"] == "Original"


class TestCoordinateValidation:
    def test_missing_coordinates_stored_as_null(self, client):
        csv_content = (
            "article_id,title,published_date,source,url,crime_type,description,district,locality,latitude,longitude,location_confidence,location_source,severity_score,risk_level\n"
            'art-1,No Coords,"Fri, 12 Jun 2026 07:00:00 GMT",The Hindu,https://example.com/1,Fraud,Desc,Vellore,,,,UNKNOWN,Manual,,Medium\n'
        )
        path = _write_csv(csv_content)
        old_path = import_dataset.DATASET_PATH
        import_dataset.DATASET_PATH = path
        try:
            import_dataset.main([])
        finally:
            import_dataset.DATASET_PATH = old_path
            os.remove(path)

        with flask_app.app_context():
            crimes = crime_service.list_crimes()
            assert len(crimes) == 1
            assert crimes[0]["latitude"] is None
            assert crimes[0]["longitude"] is None

    def test_invalid_latitude_skipped(self, client):
        csv_content = (
            "article_id,title,published_date,source,url,crime_type,description,district,locality,latitude,longitude,location_confidence,location_source,severity_score,risk_level\n"
            'art-1,Invalid Lat,"Fri, 12 Jun 2026 07:00:00 GMT",The Hindu,https://example.com/1,Fraud,Desc,Vellore,Katpadi,999,79.240410,HIGH,Geocoder,5,Medium\n'
        )
        path = _write_csv(csv_content)
        old_path = import_dataset.DATASET_PATH
        import_dataset.DATASET_PATH = path
        try:
            import_dataset.main([])
        finally:
            import_dataset.DATASET_PATH = old_path
            os.remove(path)

        with flask_app.app_context():
            crimes = crime_service.list_crimes()
            assert len(crimes) == 0

    def test_invalid_longitude_skipped(self, client):
        csv_content = (
            "article_id,title,published_date,source,url,crime_type,description,district,locality,latitude,longitude,location_confidence,location_source,severity_score,risk_level\n"
            'art-1,Invalid Lon,"Fri, 12 Jun 2026 07:00:00 GMT",The Hindu,https://example.com/1,Fraud,Desc,Vellore,Katpadi,13.043505,999,HIGH,Geocoder,5,Medium\n'
        )
        path = _write_csv(csv_content)
        old_path = import_dataset.DATASET_PATH
        import_dataset.DATASET_PATH = path
        try:
            import_dataset.main([])
        finally:
            import_dataset.DATASET_PATH = old_path
            os.remove(path)

        with flask_app.app_context():
            crimes = crime_service.list_crimes()
            assert len(crimes) == 0
