"""
Import the CrimeSense handoff dataset into the active
crime storage (Supabase PostgreSQL, or the local SQLite
fallback when Supabase credentials are not configured).

Source:
    data/final/crimesense_database_import.csv

Column mapping (CSV -> crimes table):
    crime_type   <- crime_type
    description  <- description
    latitude     <- latitude        (empty -> NULL)
    longitude    <- longitude       (empty -> NULL)
    location_name<- locality or district
    crime_date   <- published_date  (converted to YYYY-MM-DD)
    severity     <- risk_level

Usage (from the backend/ directory):

    python import_dataset.py            # add records
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


def build_record(row):
    """Map one CSV row to a crimes payload."""

    location_name = (
        row.get("locality")
        or row.get("district")
        or None
    )

    return {
        "crime_type": (
            row.get("crime_type") or ""
        ).strip(),
        "description": row.get("description"),
        "latitude": parse_coordinate(
            row.get("latitude")
        ),
        "longitude": parse_coordinate(
            row.get("longitude")
        ),
        "location_name": location_name,
        "crime_date": parse_crime_date(
            row.get("published_date")
        ),
        "severity": row.get("risk_level"),
    }


def main():

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

    arguments = parser.parse_args()

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

        imported_count = 0
        skipped_count = 0

        with open(
            DATASET_PATH,
            newline="",
            encoding="utf-8"
        ) as csv_file:

            reader = csv.DictReader(csv_file)

            for row in reader:

                record = build_record(row)

                if not record["crime_type"]:
                    skipped_count += 1
                    continue

                try:

                    crime_service.create_crime(
                        record
                    )

                    imported_count += 1

                except Exception as error:

                    print(
                        "Skipped row "
                        f"({row.get('article_id')}): "
                        f"{error}"
                    )

                    skipped_count += 1

        total = len(
            repository.list_crimes()
        )

        print(
            f"Imported {imported_count} records, "
            f"skipped {skipped_count}. "
            f"Storage now holds {total} crimes."
        )


if __name__ == "__main__":
    main()