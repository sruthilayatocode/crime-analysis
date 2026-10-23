#!/usr/bin/env python
"""
scripts/import_crimes.py
========================
One-time idempotent import script that loads data/final/crimesense_database_import.csv
into the SQLite crimes table (backend/instance/crimesense.db).

Validation rules strictly enforced:
1. Skips duplicates (based on unique article_id).
2. Validates coordinates (latitude [-90, 90], longitude [-180, 180], or NULL).
3. Validates dates (must be parseable ISO/calendar date string).
4. Validates severity (numeric score clamped/verified within 0.0 to 10.0).
5. Validates risk_level (normalized to High / Medium / Low).

Prints:
- Rows read
- Rows inserted
- Rows skipped (with reasons and counts)
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import defaultdict
from pathlib import Path
from dateutil import parser as date_parser

# Setup paths relative to script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
DEFAULT_CSV = PROJECT_ROOT / "data" / "final" / "crimesense_database_import.csv"
DEFAULT_DB = BACKEND_DIR / "instance" / "crimesense.db"

sys.path.insert(0, str(BACKEND_DIR))


def build_app(db_path: Path):
    """Initialize minimal Flask application context connected to the target database."""
    from flask import Flask
    from database import db

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path.as_posix()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app


def validate_coordinates(lat_raw: any, lng_raw: any) -> tuple[bool, float | None, float | None, str | None]:
    """Validate coordinate pair. Empty is allowed as None; non-empty must be in valid ranges."""
    lat_str = str(lat_raw).strip() if lat_raw is not None else ""
    lng_str = str(lng_raw).strip() if lng_raw is not None else ""

    if not lat_str and not lng_str:
        return True, None, None, None

    if (lat_str and not lng_str) or (lng_str and not lat_str):
        return False, None, None, f"Incomplete coordinate pair: lat='{lat_str}', lng='{lng_str}'"

    try:
        lat = float(lat_str)
        lng = float(lng_str)
    except (ValueError, TypeError):
        return False, None, None, f"Non-numeric coordinates: lat='{lat_str}', lng='{lng_str}'"

    if not (-90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0):
        return False, None, None, f"Coordinates out of bounds: ({lat}, {lng})"

    return True, lat, lng, None


def validate_date(date_raw: any) -> tuple[bool, str | None, str | None]:
    """Validate date presence and parseability."""
    if date_raw is None:
        return False, None, "Missing published_date"

    date_str = str(date_raw).strip()
    if not date_str:
        return False, None, "Empty published_date"

    try:
        parsed = date_parser.parse(date_str)
        iso_str = parsed.strftime("%Y-%m-%d %H:%M:%S")
        return True, date_str, None
    except Exception:
        return False, None, f"Unparseable date: '{date_str}'"


def validate_severity(severity_raw: any) -> tuple[bool, float | None, str | None]:
    """Validate severity score is numeric and within [0.0, 10.0]."""
    if severity_raw is None:
        return False, None, "Missing severity_score"

    sev_str = str(severity_raw).strip()
    if not sev_str:
        return False, None, "Empty severity_score"

    try:
        score = float(sev_str)
    except (ValueError, TypeError):
        return False, None, f"Non-numeric severity_score: '{sev_str}'"

    if not (0.0 <= score <= 10.0):
        return False, None, f"Severity score '{score}' outside required range [0, 10]"

    return True, score, None


def validate_risk_level(risk_raw: any) -> tuple[bool, str | None, str | None]:
    """Validate and normalize risk level to High, Medium, or Low."""
    if risk_raw is None:
        return False, None, "Missing risk_level"

    risk_str = str(risk_raw).strip()
    if not risk_str:
        return False, None, "Empty risk_level"

    clean = risk_str.capitalize()
    if clean == "Critical":
        # Critical severity is categorized under High risk level
        return True, "High", None
    elif clean in {"High", "Medium", "Low"}:
        return True, clean, None
    else:
        return False, None, f"Invalid risk_level: '{risk_str}' (expected High, Medium, or Low)"


def import_crimes(csv_path: Path, db_path: Path, reset: bool = False):
    """Perform one-time idempotent import of validated crime CSV into SQLite."""
    if not csv_path.exists():
        print(f"Error: CSV file not found at {csv_path}", file=sys.stderr)
        return False

    app = build_app(db_path)

    with app.app_context():
        from database import db
        from models.crime import Crime

        # Ensure all tables exist
        db.create_all()

        if reset:
            deleted_count = db.session.query(Crime).delete()
            db.session.commit()
            print(f"[Reset] Truncated {deleted_count} existing records from crimes table.")

        # Query existing article_ids in database for duplicate detection
        existing_article_ids = {
            r[0] for r in db.session.query(Crime.article_id).all()
        }

        with open(csv_path, newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)

        rows_read = len(rows)
        rows_inserted = 0
        rows_skipped = 0
        skipped_reasons = defaultdict(list)
        seen_article_ids_in_batch = set()

        for idx, row in enumerate(rows, start=1):
            article_id = (row.get("article_id") or "").strip()

            # 1. Validate article_id presence
            if not article_id:
                rows_skipped += 1
                skipped_reasons["Missing article_id"].append(f"Row {idx}")
                continue

            # 2. Duplicate checking
            if article_id in existing_article_ids:
                rows_skipped += 1
                skipped_reasons["Duplicate: already exists in database"].append(f"Row {idx} ({article_id})")
                continue

            if article_id in seen_article_ids_in_batch:
                rows_skipped += 1
                skipped_reasons["Duplicate: repeated in CSV file"].append(f"Row {idx} ({article_id})")
                continue

            # 3. Validate coordinates
            coords_valid, lat, lng, coords_err = validate_coordinates(
                row.get("latitude"), row.get("longitude")
            )
            if not coords_valid:
                rows_skipped += 1
                skipped_reasons[f"Invalid coordinates: {coords_err}"].append(f"Row {idx} ({article_id})")
                continue

            # 4. Validate dates
            date_valid, pub_date, date_err = validate_date(
                row.get("published_date") or row.get("crime_date")
            )
            if not date_valid:
                rows_skipped += 1
                skipped_reasons[f"Invalid date: {date_err}"].append(f"Row {idx} ({article_id})")
                continue

            # 5. Validate severity (0-10)
            sev_valid, sev_score, sev_err = validate_severity(
                row.get("severity_score")
            )
            if not sev_valid:
                rows_skipped += 1
                skipped_reasons[f"Invalid severity: {sev_err}"].append(f"Row {idx} ({article_id})")
                continue

            # 6. Validate risk_level (High/Medium/Low)
            risk_valid, risk_level, risk_err = validate_risk_level(
                row.get("risk_level")
            )
            if not risk_valid:
                rows_skipped += 1
                skipped_reasons[f"Invalid risk_level: {risk_err}"].append(f"Row {idx} ({article_id})")
                continue

            # All validations passed -> create Crime record
            crime = Crime(
                article_id=article_id,
                title=(row.get("title") or "").strip() or None,
                published_date=pub_date,
                source=(row.get("source") or "").strip() or None,
                url=(row.get("url") or "").strip() or None,
                crime_type=(row.get("crime_type") or "").strip() or "General Crime",
                description=(row.get("description") or "").strip() or None,
                district=(row.get("district") or "").strip() or "Vellore",
                locality=(row.get("locality") or "").strip() or None,
                latitude=lat,
                longitude=lng,
                location_confidence=(row.get("location_confidence") or "").strip() or None,
                location_source=(row.get("location_source") or "").strip() or None,
                severity_score=sev_score,
                risk_level=risk_level,
                # Legacy compatibility fields
                location_name=(row.get("locality") or "").strip() or None,
                crime_date=pub_date,
                severity=risk_level,
            )

            db.session.add(crime)
            seen_article_ids_in_batch.add(article_id)
            existing_article_ids.add(article_id)
            rows_inserted += 1

        db.session.commit()

        total_in_db = db.session.query(Crime).count()

        # Print structured summary
        print("=" * 65)
        print("CrimeSense Database Import Report")
        print("=" * 65)
        print(f"Target Database : {db_path}")
        print(f"Source CSV      : {csv_path}")
        print("-" * 65)
        print(f"Rows read       : {rows_read}")
        print(f"Rows inserted   : {rows_inserted}")
        print(f"Rows skipped    : {rows_skipped}")
        print(f"Total in table  : {total_in_db}")
        print("-" * 65)

        if skipped_reasons:
            print("Reasons for skipped rows:")
            for reason, occurrences in sorted(skipped_reasons.items(), key=lambda kv: len(kv[1]), reverse=True):
                count = len(occurrences)
                sample = ", ".join(occurrences[:5])
                if count > 5:
                    sample += f", ... (+{count - 5} more)"
                print(f"  * {reason} ({count} rows):")
                print(f"      {sample}")
        else:
            print("Zero rows were skipped. All rows met validation criteria.")

        print("=" * 65)
        return True


def main():
    parser = argparse.ArgumentParser(
        description="One-time idempotent import script for CrimeSense crimes database."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV,
        help="Path to CSV dataset (default: data/final/crimesense_database_import.csv)",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help="Path to SQLite database file (default: backend/instance/crimesense.db)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Truncate the crimes table prior to importing (clean rebuild).",
    )

    args = parser.parse_args()
    success = import_crimes(args.csv, args.db, reset=args.reset)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
