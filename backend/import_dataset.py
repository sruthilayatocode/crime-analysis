"""
Import the CrimeSense handoff dataset into the active
crime storage (SQLite via SQLAlchemy).

Source:
    data/final/crimesense_database_import.csv

Column mapping (CSV -> crimes table):
    article_id      -> article_id
    title           -> title
    published_date  -> crime_date
    source          -> source
    url             -> url
    crime_type      -> crime_type
    description     -> description
    district        -> district
    locality        -> location_name
    latitude        -> latitude        (empty -> NULL, validated)
    longitude       -> longitude       (empty -> NULL, validated)
    location_confidence -> location_confidence
    location_source -> location_source
    severity_score  -> severity_score  (validated integer)
    risk_level      -> risk_level

Deduplication:
    - article_id is the primary deduplication key.
    - If article_id is missing, url is used as fallback.
    - Rows with no stable key are inserted without dedup checks.
    - Duplicate rows within the same CSV are skipped.

Usage (from the backend/ directory):

    python import_dataset.py            # add/update records
    python import_dataset.py --clear    # wipe table first
"""

import argparse
import csv
import os
import sys
from email.utils import parsedate_to_datetime


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from backend.app import app  # noqa: E402
except ModuleNotFoundError:
    from app import app  # noqa: E402

from services import crime_service  # noqa: E402
from services.data_service import get_crime_repository  # noqa: E402


DATASET_PATH = os.path.join(
    os.path.dirname(BASE_DIR),
    "data",
    "final",
    "crimesense_database_import.csv",
)


def parse_crime_date(raw_value):
    """
    Convert RFC-1123 dates such as
    "Thu, 30 Jan 2025 08:00:00 GMT" to YYYY-MM-DD.
    Falls back to the raw value when parsing fails.
    """

    if not raw_value:
        return None

    try:

        parsed = parsedate_to_datetime(
            raw_value.strip()
        )

        return parsed.strftime("%Y-%m-%d")

    except (
        TypeError,
        ValueError
    ):

        return raw_value.strip()


def parse_coordinate(raw_value):
    """Return a float coordinate or None."""

    if raw_value is None:
        return None

    text = str(raw_value).strip()

    if not text:
        return None

    return float(text)


def validate_coordinates(latitude, longitude):
    """Validate coordinate ranges."""

    if latitude is not None:
        if not -90 <= latitude <= 90:
            raise ValueError(
                "Latitude must be between -90 and 90"
            )

    if longitude is not None:
        if not -180 <= longitude <= 180:
            raise ValueError(
                "Longitude must be between -180 and 180"
            )


def validate_severity_score(raw_value):
    """Return a validated integer or None."""

    if raw_value is None:
        return None

    text = str(raw_value).strip()

    if not text:
        return None

    try:
        return int(text)
    except ValueError:
        raise ValueError(
            "severity_score must be a valid integer"
        )


def find_existing_crime(record):
    """
    Return an existing crime dict matching the record
    by article_id or url, or None.
    """

    from models.crime import Crime  # noqa: E402

    article_id = record.get("article_id")
    if article_id:
        existing = (
            Crime.query.filter_by(article_id=article_id).first()
        )
        if existing:
            return existing.to_dict()

    url = record.get("url")
    if url:
        existing = (
            Crime.query.filter_by(url=url).first()
        )
        if existing:
            return existing.to_dict()

    return None


def build_record(row):
    """Map one CSV row to a crimes payload."""

    location_name = (
        row.get("locality")
        or row.get("district")
        or None
    )

    latitude = parse_coordinate(
        row.get("latitude")
    )
    longitude = parse_coordinate(
        row.get("longitude")
    )

    validate_coordinates(latitude, longitude)

    severity_score = validate_severity_score(
        row.get("severity_score")
    )

    return {
        "article_id": (
            row.get("article_id") or ""
        ).strip() or None,
        "title": (
            row.get("title") or ""
        ).strip() or None,
        "source": (
            row.get("source") or ""
        ).strip() or None,
        "url": (
            row.get("url") or ""
        ).strip() or None,
        "crime_type": (
            row.get("crime_type") or ""
        ).strip(),
        "description": (
            row.get("description") or ""
        ).strip() or None,
        "district": (
            row.get("district") or ""
        ).strip() or None,
        "location_name": location_name,
        "crime_date": parse_crime_date(
            row.get("published_date")
        ),
        "latitude": latitude,
        "longitude": longitude,
        "location_confidence": (
            row.get("location_confidence") or ""
        ).strip() or None,
        "location_source": (
            row.get("location_source") or ""
        ).strip() or None,
        "severity_score": severity_score,
        "severity": (
            row.get("risk_level") or ""
        ).strip() or None,
        "risk_level": (
            row.get("risk_level") or ""
        ).strip() or None,
    }


def main(argv=None):

    parser = argparse.ArgumentParser(
        description=(
            "Import crimesense_database_import.csv "
            "into the active crime storage."
        )
    )

    parser.add_argument(
        "--clear",
        action="store_true",
        help=(
            "Delete all existing crime records "
            "before importing"
        )
    )

    arguments = parser.parse_args(argv)

    if not os.path.exists(DATASET_PATH):
        print(
            f"Dataset not found: {DATASET_PATH}"
        )
        sys.exit(1)

    with app.app_context():

        repository = get_crime_repository()

        if arguments.clear:

            existing = repository.list_crimes()

            for crime in existing:
                repository.delete_crime(
                    crime["id"]
                )

            print(
                f"Cleared {len(existing)} "
                "existing records"
            )

        total_rows = 0
        inserted_count = 0
        updated_count = 0
        skipped_duplicate_count = 0
        invalid_count = 0
        missing_coordinates_count = 0

        seen_keys = set()

        with open(
            DATASET_PATH,
            newline="",
            encoding="utf-8"
        ) as csv_file:

            reader = csv.DictReader(csv_file)

            for row in reader:

                total_rows += 1

                try:

                    record = build_record(row)

                except ValueError as error:

                    print(
                        "Invalid row "
                        f"({row.get('article_id')}): "
                        f"{error}"
                    )

                    invalid_count += 1
                    continue

                if not record["crime_type"]:
                    print(
                        "Skipped row "
                        f"({row.get('article_id')}): "
                        "missing crime_type"
                    )

                    invalid_count += 1
                    continue

                if record.get("latitude") is None or record.get("longitude") is None:
                    missing_coordinates_count += 1

                key = (
                    record.get("article_id")
                    or record.get("url")
                )

                if key:
                    if key in seen_keys:
                        skipped_duplicate_count += 1
                        continue

                    seen_keys.add(key)

                existing = find_existing_crime(record)

                if existing:

                    try:

                        repository.update_crime(
                            existing["id"],
                            record
                        )

                        updated_count += 1

                    except Exception as error:

                        print(
                            "Failed to update row "
                            f"({record.get('article_id')}): "
                            f"{error}"
                        )

                        invalid_count += 1

                else:

                    try:

                        repository.insert_crime(
                            record
                        )

                        inserted_count += 1

                    except Exception as error:

                        print(
                            "Skipped row "
                            f"({record.get('article_id')}): "
                            f"{error}"
                        )

                        skipped_duplicate_count += 1

        total = len(
            repository.list_crimes()
        )

        print(
            f"CSV rows: {total_rows}\n"
            f"Inserted: {inserted_count}\n"
            f"Updated: {updated_count}\n"
            f"Skipped duplicates: {skipped_duplicate_count}\n"
            f"Invalid: {invalid_count}\n"
            f"Missing coordinates: {missing_coordinates_count}\n"
            f"Final database row count: {total}"
        )


if __name__ == "__main__":
    main()
