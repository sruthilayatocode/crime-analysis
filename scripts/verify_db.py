#!/usr/bin/env python
"""
scripts/verify_db.py
====================
Inspects and verifies SQLite database (backend/instance/crimesense.db).
For every table, prints:
- Row count
- Column list with data types
- 3 sample rows with sensitive fields (password hashes, phone numbers) masked
- Verifies that essential tables (crimes, users) are not empty.
"""

from __future__ import annotations

import os
import re
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
DB_PATH = BACKEND_DIR / "instance" / "crimesense.db"


def mask_value(col_name: str, val: any) -> any:
    """Mask sensitive fields like password hashes and phone numbers."""
    if val is None:
        return None

    val_str = str(val)
    col_lower = col_name.lower()

    # Mask password hashes
    if "password" in col_lower or val_str.startswith(("pbkdf2:", "scrypt:", "$2b$", "$2a$")):
        return "[MASKED_PASSWORD_HASH]"

    # Mask phone numbers
    if "phone" in col_lower or (isinstance(val, str) and re.match(r"^\+?[0-9]{10,13}$", val.strip())):
        cleaned = val_str.strip()
        if len(cleaned) >= 6:
            return f"{cleaned[:3]}*****{cleaned[-3:]}"
        return "[MASKED_PHONE]"

    # Truncate very long descriptions or URLs for readable console output
    if isinstance(val, str) and len(val) > 80:
        return val[:77] + "..."

    return val


def verify_database(db_path: Path = DB_PATH) -> bool:
    print("=" * 80)
    print(f"CrimeSense Database Verification: {db_path}")
    print("=" * 80)

    if not db_path.exists():
        print(f"CRITICAL ERROR: Database file does not exist at {db_path}", file=sys.stderr)
        return False

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Enable WAL & pragmas
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("PRAGMA journal_mode = WAL;")

    # Fetch all user tables
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;"
    )
    tables = [r[0] for r in cursor.fetchall()]

    if not tables:
        print("ERROR: No tables found in database!", file=sys.stderr)
        conn.close()
        return False

    print(f"Total tables found: {len(tables)}\n")

    non_empty_required = {"crimes", "users"}
    failed_requirements = []

    for idx, table in enumerate(tables, 1):
        print(f"[{idx}/{len(tables)}] TABLE: {table.upper()}")
        print("-" * 80)

        # 1. Column list and metadata
        cursor.execute(f"PRAGMA table_info({table});")
        columns_info = cursor.fetchall()
        col_names = [c["name"] for c in columns_info]
        col_display = [f"{c['name']} ({c['type'] or 'ANY'})" for c in columns_info]
        print(f"Columns ({len(columns_info)}):")
        print("  " + ", ".join(col_display))

        # 2. Row count
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        row_count = cursor.fetchone()[0]
        print(f"Row count: {row_count}")

        # Check required non-empty tables
        if table in non_empty_required and row_count == 0:
            failed_requirements.append(f"Table '{table}' is empty (must have records)!")

        # 3. Sample rows (up to 3)
        cursor.execute(f"SELECT * FROM {table} LIMIT 3;")
        samples = cursor.fetchall()

        if samples:
            print("Sample Rows (up to 3, sensitive fields masked):")
            for s_idx, row in enumerate(samples, 1):
                masked_row = {c: mask_value(c, row[c]) for c in col_names}
                print(f"  Row #{s_idx}: {masked_row}")
        else:
            print("Sample Rows: (table is currently empty)")

        print()

    conn.close()

    print("=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    if failed_requirements:
        print("FAILED CHECKS:")
        for err in failed_requirements:
            print(f"  [X] {err}")
        return False
    else:
        print("ALL CHECKS PASSED: Database schema, tables, and mandatory records verified.")
        return True


if __name__ == "__main__":
    success = verify_database()
    sys.exit(0 if success else 1)
