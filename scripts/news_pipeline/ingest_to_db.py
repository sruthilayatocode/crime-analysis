#!/usr/bin/env python
"""
CLI: ingest the processed/geocoded news CSV into the CrimeSense
SQLite database using the existing NewsIngestionService.

Usage (from the repository root):

    py scripts/news_pipeline/ingest_to_db.py

The script reuses the ingestion/deduplication logic in
``backend/services/news_ingestion_service.py``. It does NOT
duplicate that logic and does NOT modify the service, the
database schema, or any existing records. No new database is
created, and no destructive operation (DELETE/DROP/TRUNCATE/
reset) is ever issued.
"""

import os
import sys


# ---------------------------------------------------------------------------
# Import path setup
# ---------------------------------------------------------------------------
# Allow the script to be run from the repository root:
#     py scripts/news_pipeline/ingest_to_db.py
#
# REPO_ROOT is added so ``backend`` is importable and BACKEND_DIR is
# added so the top-level backend modules (``app``, ``config``,
# ``database``, ``models``, ``services``) resolve.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

REPO_ROOT = os.path.abspath(
    os.path.join(SCRIPT_DIR, "..", "..")
)

BACKEND_DIR = os.path.join(REPO_ROOT, "backend")

for _path in (REPO_ROOT, BACKEND_DIR):
    if _path not in sys.path:
        sys.path.insert(0, _path)


from app import app  # noqa: E402
import services.news_ingestion_service as _service  # noqa: E402


# Path to the processed/geocoded news CSV (relative to repo root).
CSV_PATH = os.path.join(
    REPO_ROOT, "data", "processed", "news_geocoded.csv"
)


class NewsIngestionService:
    """
    Thin facade over the already-created ingestion service so this
    CLI can call ``NewsIngestionService.ingest_csv(...)`` while
    reusing the existing module-level functions.
    """

    @staticmethod
    def ingest_csv(file_path):
        return _service.ingest_csv(file_path)

    @staticmethod
    def ingest_records(records):
        return _service.ingest_records(records)

    @staticmethod
    def normalize_record(record):
        return _service.normalize_record(record)


def _print_summary(stats):
    """Print a concise ingestion summary."""

    print("CrimeSense news ingestion complete.")
    print(f"CSV: {CSV_PATH}")
    print(f"Total:               {stats['total']}")
    print(f"Inserted:            {stats['inserted']}")
    print(f"Updated:             {stats['updated']}")
    print(f"Duplicates:          {stats['duplicates']}")
    print(f"Invalid:             {stats['invalid']}")
    print(f"Missing coordinates: {stats['missing_coordinates']}")


def main(argv=None):
    """
    Ingest the processed news CSV into the existing SQLite DB.

    Returns 0 on success, 1 when the CSV is missing.
    """

    if not os.path.exists(CSV_PATH):

        print(
            "Processed news CSV not found: "
            f"{CSV_PATH}"
        )
        print(
            "Run the news pipeline scraper/cleaner/geocoder "
            "first to generate it."
        )

        return 1

    with app.app_context():

        stats = NewsIngestionService.ingest_csv(CSV_PATH)

    _print_summary(stats)

    return 0


if __name__ == "__main__":

    sys.exit(main())
