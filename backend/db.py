"""
db.py
=====
SQLite connection helper for the CrimeSense backend.

Uses the Python standard-library sqlite3 module (SQLAlchemy is incompatible
with this Python 3.13 environment), pointing at database/crimesense.db.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "crimesense.db"

# Columns returned by the public API (all 15 columns of the import file).
COLUMNS = [
    "article_id", "title", "published_date", "source", "url",
    "crime_type", "description", "district", "locality",
    "latitude", "longitude", "location_confidence", "location_source",
    "severity_score", "risk_level",
]


def get_connection() -> sqlite3.Connection:
    """Open a read connection to the CrimeSense database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a sqlite3.Row to a plain dict."""
    return dict(row) if row is not None else None


def query(sql: str, params: tuple = ()):
    """Run a SELECT and return a list of dicts."""
    conn = get_connection()
    try:
        rows = conn.execute(sql, params).fetchall()
        return [row_to_dict(r) for r in rows]
    finally:
        conn.close()


def query_one(sql: str, params: tuple = ()):
    """Run a SELECT and return a single dict (or None)."""
    conn = get_connection()
    try:
        row = conn.execute(sql, params).fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


def total_rows() -> int:
    conn = get_connection()
    try:
        return conn.execute("SELECT COUNT(*) FROM crime_incidents").fetchone()[0]
    finally:
        conn.close()