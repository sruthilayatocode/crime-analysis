#!/usr/bin/env python3
"""
init_database.py
================
Create the CrimeSense SQLite database and populate it from the clean
handoff dataset.

Table  : crime_incidents
DB file: database/crimesense.db
Input  : data/final/crimesense_database_import.csv

The schema follows data/final/crimesense_database_schema.md exactly, using
the 15 columns in the database import file.  `article_id` is the PRIMARY KEY.

Empty geographic / risk fields in the CSV are loaded as SQL NULL (never
fabricated).  No raw/processed datasets are modified by this script.
"""

from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_FILE = PROJECT_ROOT / "database" / "crimesense.db"
IMPORT_FILE = PROJECT_ROOT / "data" / "final" / "crimesense_database_import.csv"

# Columns in the database import file (matching the schema doc).
COLUMNS = [
    "article_id", "title", "published_date", "source", "url",
    "crime_type", "description", "district", "locality",
    "latitude", "longitude", "location_confidence", "location_source",
    "severity_score", "risk_level",
]

# Numeric columns that must be stored as NULL when empty.
INDEX_COLS = ["locality", "crime_type", "risk_level", "location_confidence"]

DDL = """
CREATE TABLE IF NOT EXISTS crime_incidents (
    article_id         TEXT PRIMARY KEY,
    title              TEXT NOT NULL,
    published_date     TEXT NOT NULL,
    source             TEXT,
    url                TEXT NOT NULL,
    crime_type         TEXT NOT NULL,
    description        TEXT NOT NULL,
    district           TEXT NOT NULL,
    locality           TEXT,
    latitude           REAL,
    longitude          REAL,
    location_confidence TEXT,
    location_source    TEXT,
    severity_score     INTEGER,
    risk_level         TEXT
);
"""


def read_rows():
    with IMPORT_FILE.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sanitize(row):
    """Replace empty strings with None (SQL NULL)."""
    out = {}
    for col in COLUMNS:
        val = (row.get(col) or "").strip()
        out[col] = None if val == "" else val
    return out


def main() -> int:
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    rows = read_rows()
    conn = sqlite3.connect(str(DB_FILE))
    try:
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS crime_incidents")
        cur.execute(DDL)
        for col in INDEX_COLS:
            cur.execute(
                'CREATE INDEX IF NOT EXISTS idx_crime_incidents_%s ON crime_incidents(%s)'
                % (col, col)
            )
        cleaned = [sanitize(r) for r in rows]
        placeholders = ",".join("?" * len(COLUMNS))
        sql = "INSERT INTO crime_incidents (%s) VALUES (%s)" % (
            ",".join(COLUMNS), placeholders)
        cur.executemany(sql, [[r[c] for c in COLUMNS] for r in cleaned])
        conn.commit()

        total = cur.execute("SELECT COUNT(*) FROM crime_incidents").fetchone()[0]
        dup = total - cur.execute(
            "SELECT COUNT(DISTINCT article_id) FROM crime_incidents").fetchone()[0]
        print("SQLite DB created: %s" % DB_FILE)
        print("Rows imported:        %d" % total)
        print("Duplicate article_id: %d" % dup)
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())