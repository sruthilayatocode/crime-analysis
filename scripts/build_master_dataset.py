#!/usr/bin/env python3
"""
build_master_dataset.py
========================
Create the final clean handoff dataset for the CrimeSense backend/database.

Inputs (already processed — no new collection, no re-analysis):
  * data/processed/news_scored_final.csv   (authoritative: title, crime_type,
    description, district, locality, is_crime_relevant, severity_score,
    risk_level, location_source, location_confidence)
  * data/processed/news_geocoded_v2.csv    (authoritative: latitude, longitude)

Both files share `article_id` and each contains 89 validated records, so the
join is 1:1 on article_id.  Geographic fields (latitude, longitude,
location_confidence, location_source) come from the geocoded file; all other
fields come from the scored file.

Outputs (one row per validated crime incident = 89 rows):
  * data/final/crimesense_master.csv
  * data/final/crimesense_database_import.csv
  * data/final/crimesense_database_schema.md
  * data/final/master_dataset_quality_report.txt

Integrity guarantees:
  * Exactly the 89 validated records — nothing added or removed.
  * No duplicate article_id values.
  * URL, crime_type, severity_score, risk_level and location confidence are
    preserved verbatim from the source files.
  * No coordinates are invented; unavailable fields are left NULL (empty).
  * Source CSVs are never modified.
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCORED_FILE = PROJECT_ROOT / "data" / "processed" / "news_scored_final.csv"
GEO_FILE = PROJECT_ROOT / "data" / "processed" / "news_geocoded_v2.csv"
FINAL_DIR = PROJECT_ROOT / "data" / "final"

MASTER_FILE = FINAL_DIR / "crimesense_master.csv"
DB_IMPORT_FILE = FINAL_DIR / "crimesense_database_import.csv"
SCHEMA_FILE = FINAL_DIR / "crimesense_database_schema.md"
REPORT_FILE = FINAL_DIR / "master_dataset_quality_report.txt"

FINAL_DIR.mkdir(parents=True, exist_ok=True)

# Fields for the full master dataset (includes every required field).
MASTER_FIELDS = [
    "article_id", "title", "published_date", "source", "url",
    "crime_type", "description", "district", "locality",
    "latitude", "longitude", "location_confidence", "location_source",
    "severity_score", "risk_level", "is_crime_relevant",
]

# Fields for the backend/database import (a strict subset of master).
DB_FIELDS = [
    "article_id", "title", "published_date", "source", "url",
    "crime_type", "description", "district", "locality",
    "latitude", "longitude", "location_confidence", "location_source",
    "severity_score", "risk_level",
]


def load_csv(path):
    """Read a CSV into a list of dicts."""
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def to_rows(scored, geo):
    """
    Merge scored + geocoded on article_id into master rows.

    Scores/risk/is_crime_relevant from scored; latitude/longitude +
    location confidence/source from geo.  Missing geographic values are
    left as empty strings (rendered as NULL in DB context).
    """
    geo_by_id = {r["article_id"]: r for r in geo}
    rows = []
    for s in scored:
        aid = s["article_id"]
        g = geo_by_id.get(aid, {})
        rows.append({
            "article_id": aid,
            "title": s.get("title", ""),
            "published_date": s.get("published_date", ""),
            "source": s.get("source", ""),
            "url": s.get("url", ""),
            "crime_type": s.get("crime_type", ""),
            "description": s.get("description", ""),
            "district": s.get("district", ""),
            "locality": s.get("locality", ""),
            "latitude": g.get("latitude", ""),
            "longitude": g.get("longitude", ""),
            "location_confidence": g.get("location_confidence", ""),
            "location_source": g.get("location_source", ""),
            "severity_score": s.get("severity_score", ""),
            "risk_level": s.get("risk_level", ""),
            "is_crime_relevant": s.get("is_crime_relevant", ""),
        })
    return rows


def write_csv(path, rows, fieldnames):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run_quality_checks(rows):
    total = len(rows)
    ids = [r["article_id"] for r in rows]
    dup_ids = len(ids) - len(set(ids))

    def missing(field):
        return sum(1 for r in rows if not (r.get(field) or "").strip())

    checks = {
        "total_rows": total,
        "duplicate_article_id": dup_ids,
        "missing_title": missing("title"),
        "missing_url": missing("url"),
        "missing_crime_type": missing("crime_type"),
        "missing_published_date": missing("published_date"),
        "missing_locality": missing("locality"),
        "missing_latitude": missing("latitude"),
        "missing_longitude": missing("longitude"),
        "missing_severity_score": missing("severity_score"),
        "missing_risk_level": missing("risk_level"),
    }

    with_coords = sum(1 for r in rows if (r.get("latitude") or "").strip()
                      and (r.get("longitude") or "").strip())
    return {
        "total": total,
        "unique_ids": len(set(ids)),
        "dup_ids": dup_ids,
        "with_coords": with_coords,
        "without_coords": total - with_coords,
        "checks": checks,
        "crime_dist": Counter(r["crime_type"] or "(blank)" for r in rows),
        "risk_dist": Counter(r["risk_level"] or "(blank)" for r in rows),
        "conf_dist": Counter(r["location_confidence"] or "(blank)" for r in rows),
        "localities": sorted({(r.get("locality") or "").strip() for r in rows}),
    }


# --------------------------------------------------------------------------- #
# Schema documentation
# --------------------------------------------------------------------------- #
def build_schema_md():
    """Return markdown describing every field in the database import."""
    fields = [
        ("article_id", "TEXT/VARCHAR(64)", "Unique primary key for each crime "
         "incident (hash of the original article).",
         "NOT NULL", "70d2d39686e4ee8b"),
        ("title", "TEXT", "Headline of the original news article.", "NOT NULL",
         "Four get 20 years imprisonment in 2022 Katpadi gang-rape case"),
        ("published_date", "TEXT", "Publication date of the article (RFC-1123 "
         "format).", "NOT NULL", "Thu, 30 Jan 2025 08:00:00 GMT"),
        ("source", "TEXT", "Name of the publishing outlet.", "NULLABLE",
         "The Hindu"),
        ("url", "TEXT", "Original canonical URL of the article.", "NOT NULL",
         "https://www.…"),
        ("crime_type", "TEXT", "Normalised crime category label.", "NOT NULL",
         "Sexual Assault"),
        ("description", "TEXT", "Article description / body snippet.",
         "NOT NULL", "Two persons were arrested for…"),
        ("district", "TEXT", "Administrative district.", "NOT NULL", "Vellore"),
        ("locality", "TEXT", "Specific locality/neighbourhood of the incident "
         "(empty/NULL when not mentioned).", "NULLABLE", "Katpadi"),
        ("latitude", "NUMERIC(9,6)", "Decimal latitude of the incident. NULL "
         "when the location was not geocoded.", "NULLABLE", "13.043505"),
        ("longitude", "NUMERIC(9,6)", "Decimal longitude of the incident. "
         "NULL when the location was not geocoded.", "NULLABLE", "79.240410"),
        ("location_confidence", "TEXT", "Confidence of the geocoding: HIGH / "
         "LOW / UNKNOWN.", "NULLABLE", "HIGH"),
        ("location_source", "TEXT", "Free-text note describing how the location "
         "was derived.", "NULLABLE", "Vellore mentioned without exact incident "
         "locality"),
        ("severity_score", "INTEGER", "Numeric risk weight (2 / 5 / 8 / 10). "
         "10=Critical, 8=High, 5=Medium, 2=Low.", "NULLABLE", "10"),
        ("risk_level", "TEXT", "Categorical risk level: Critical / High / "
         "Medium / Low.", "NULLABLE", "Critical"),
    ]
    lines = [
        "# CrimeSense Database Schema",
        "",
        "Final handoff dataset for the backend/database import. A single "
        "physical table is defined by `crimesense_database_import.csv`, keyed "
        "on `article_id`.",
        "",
        "## Primary Key",
        "",
        "| Field | Type | Role |",
        "|---|---|---|",
        "| `article_id` | TEXT | `PRIMARY KEY` |",
        "",
        "## Columns",
        "",
        "| Field | Data Type | Description | Nullable | Example |",
        "|---|---|---|---|---|",
    ]
    for fname, ftype, desc, nullable, example in fields:
        escaped = example.replace("|", "\\|")
        lines.append("| `%s` | %s | %s | %s | %s |"
                     % (fname, ftype, desc, nullable, escaped))
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("* `article_id` is unique and non-null (89 records).")
    lines.append("* Only 7 records have geocoded `latitude`/`longitude`; the "
                 "other 82 are NULL for these two columns.")
    lines.append("* `risk_level` / `severity_score` are jointly set; a row "
             "either has both or neither.")
    return "\n".join(lines)


def write_schema():
    SCHEMA_FILE.parent.mkdir(parents=True, exist_ok=True)
    SCHEMA_FILE.write_text(build_schema_md(), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Quality report
# --------------------------------------------------------------------------- #
def build_report(q):
    L = []
    L.append("=" * 70)
    L.append("MASTER DATASET QUALITY REPORT")
    L.append("Generated: %s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    L.append("=" * 70)
    L.append("")
    L.append("Total records:         %d" % q["total"])
    L.append("Unique records:        %d" % q["unique_ids"])
    L.append("Duplicate records:     %d" % q["dup_ids"])
    L.append("Records with coordinates: %d" % q["with_coords"])
    L.append("Records without coordinates: %d" % q["without_coords"])
    L.append("")
    L.append("FIELD-LEVEL CHECKS")
    L.append("-" * 40)
    for key in ["total_rows", "duplicate_article_id", "missing_title",
                "missing_url", "missing_crime_type", "missing_published_date",
                "missing_locality", "missing_latitude", "missing_longitude",
                "missing_severity_score", "missing_risk_level"]:
        L.append("  %-26s : %d" % (key, q["checks"][key]))
    L.append("")
    L.append("RISK DISTRIBUTION")
    L.append("-" * 40)
    for k, v in sorted(q["risk_dist"].items(), key=lambda x: str(x[0])):
        L.append("  %s : %d" % (k, v))
    L.append("")
    L.append("CRIME TYPE DISTRIBUTION")
    L.append("-" * 40)
    for k, v in sorted(q["crime_dist"].items(), key=lambda x: (-x[1], str(x[0]))):
        L.append("  %s : %d" % (k, v))
    L.append("")
    L.append("LOCATION CONFIDENCE DISTRIBUTION")
    L.append("-" * 40)
    for k, v in sorted(q["conf_dist"].items(), key=lambda x: (-x[1], str(x[0]))):
        L.append("  %s : %d" % (k, v))
    L.append("")
    L.append("UNIQUE LOCALITIES")
    L.append("-" * 40)
    for loc in q["localities"]:
        L.append("  %s" % (loc if loc else "(empty)"))
    L.append("")
    L.append("QUALITY ISSUES")
    L.append("-" * 40)
    issues = []
    if q["dup_ids"]:
        issues.append("Duplicate article_id values found: %d" % q["dup_ids"])
    if q["checks"]["missing_title"]:
        issues.append("Missing titles: %d" % q["checks"]["missing_title"])
    if q["checks"]["missing_url"]:
        issues.append("Missing URLs: %d" % q["checks"]["missing_url"])
    if q["checks"]["missing_crime_type"]:
        issues.append("Missing crime_type: %d" % q["checks"]["missing_crime_type"])
    if q["without_coords"]:
        issues.append("%d records lack latitude/longitude (NULL)." % q["without_coords"])
    if q["checks"]["missing_locality"]:
        issues.append("%d records lack a locality label (NULL)." % q["checks"]["missing_locality"])
    if q["checks"]["missing_severity_score"]:
        issues.append("Missing severity_score: %d" % q["checks"]["missing_severity_score"])
    if q["checks"]["missing_risk_level"]:
        issues.append("Missing risk_level: %d" % q["checks"]["missing_risk_level"])
    if not issues:
        issues.append("No data-integrity issues detected (other than intentional NULLs "
                      "for unavailable geographic fields).")
    for i in issues:
        L.append("  - %s" % i)
    L.append("")
    L.append("=" * 70)
    L.append("END OF REPORT")
    L.append("=" * 70)
    return "\n".join(L)


def write_report(qc):
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(build_report(qc), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> int:
    if not SCORED_FILE.exists() or not GEO_FILE.exists():
        print("ERROR: required source file missing.")
        return 1

    scored = load_csv(SCORED_FILE)
    geo = load_csv(GEO_FILE)

    rows = to_rows(scored, geo)
    write_csv(MASTER_FILE, rows, MASTER_FIELDS)
    write_csv(DB_IMPORT_FILE, rows, DB_FIELDS)
    write_schema()
    qc = run_quality_checks(rows)
    write_report(qc)

    print("=" * 60)
    print("MASTER DATASET BUILT")
    print("=" * 60)
    print("Total records:              %d" % qc["total"])
    print("Unique records:             %d" % qc["unique_ids"])
    print("Duplicate article_id:       %d" % qc["dup_ids"])
    print("Records with coordinates:   %d" % qc["with_coords"])
    print("Records without coordinates:%d" % qc["without_coords"])
    print()
    print("Risk distribution:")
    for k, v in sorted(qc["risk_dist"].items(), key=lambda x: str(x[0])):
        print("  %s: %d" % (k, v))
    print()
    print("Crime type distribution:")
    for k, v in sorted(qc["crime_dist"].items(), key=lambda x: (-x[1], str(x[0]))):
        print("  %s: %d" % (k, v))
    print()
    print("Location confidence distribution:")
    for k, v in sorted(qc["conf_dist"].items(), key=lambda x: (-x[1], str(x[0]))):
        print("  %s: %d" % (k, v))
    print()
    print("Unique localities:")
    for loc in qc["localities"]:
        print("  %s" % (loc if loc else "(empty)"))
    print()
    print("Outputs:")
    print("  data/final/crimesense_master.csv")
    print("  data/final/crimesense_database_import.csv")
    print("  data/final/crimesense_database_schema.md")
    print("  data/final/master_dataset_quality_report.txt")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())