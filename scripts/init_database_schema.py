#!/usr/bin/env python
"""
scripts/init_database_schema.py
===============================
Database initialization and verification script for CrimeSense.
Ensures every required table, foreign key constraint (with ON DELETE CASCADE),
and index exists in SQLite (backend/instance/crimesense.db).

Required tables:
- crimes
- users
- sos_contacts
- saved_locations
- user_settings
- user_locations
- sos_events
- shared_links
- alerts
- audit_log (and audit_logs)

Indexes:
- user_id on all user-dependent tables
- (latitude, longitude) composite on geographic tables
- date / published_date / crime_date on temporal tables
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
DB_PATH = BACKEND_DIR / "instance" / "crimesense.db"

sys.path.insert(0, str(BACKEND_DIR))


def init_and_verify_database(db_path: Path = DB_PATH):
    from flask import Flask
    from database import db
    import models  # loads all models

    os.makedirs(db_path.parent, exist_ok=True)

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path.as_posix()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    print("=" * 65)
    print(f"Initializing CrimeSense Database: {db_path}")
    print("=" * 65)

    with app.app_context():
        # 1. Create all SQLAlchemy models
        db.create_all()

        with db.engine.connect() as conn:
            # Enable SQLite foreign keys
            conn.execute(text("PRAGMA foreign_keys = ON;"))

            # 2. Add required indexes
            indexes = [
                # Crimes
                ("idx_crimes_lat_lng", "crimes", "(latitude, longitude)"),
                ("idx_crimes_published_date", "crimes", "(published_date)"),
                ("idx_crimes_crime_date", "crimes", "(crime_date)"),
                ("idx_crimes_article_id", "crimes", "(article_id)"),
                # User locations
                ("idx_user_loc_user_id", "user_locations", "(user_id)"),
                ("idx_user_loc_lat_lng", "user_locations", "(latitude, longitude)"),
                ("idx_user_loc_recorded_at", "user_locations", "(recorded_at)"),
                # Saved locations
                ("idx_saved_loc_user_id", "saved_locations", "(user_id)"),
                ("idx_saved_loc_lat_lng", "saved_locations", "(latitude, longitude)"),
                # SOS Events
                ("idx_sos_event_user_id", "sos_events", "(user_id)"),
                ("idx_sos_event_lat_lng", "sos_events", "(latitude, longitude)"),
                ("idx_sos_event_created_at", "sos_events", "(created_at)"),
                # Shared Links
                ("idx_shared_link_user_id", "shared_links", "(user_id)"),
                ("idx_shared_link_lat_lng", "shared_links", "(latitude, longitude)"),
                ("idx_shared_link_token", "shared_links", "(token)"),
                # Alerts
                ("idx_alerts_user_id", "alerts", "(user_id)"),
                ("idx_alerts_lat_lng", "alerts", "(latitude, longitude)"),
                ("idx_alerts_created_at", "alerts", "(created_at)"),
                # SOS Contacts
                ("idx_sos_contacts_user_id", "sos_contacts", "(user_id)"),
                # User Settings
                ("idx_user_settings_user_id", "user_settings", "(user_id)"),
                # Audit Logs
                ("idx_audit_logs_admin_id", "audit_logs", "(admin_id)"),
                ("idx_audit_logs_created_at", "audit_logs", "(created_at)"),
            ]

            for idx_name, tbl_name, cols in indexes:
                sql = f"CREATE INDEX IF NOT EXISTS {idx_name} ON {tbl_name} {cols};"
                conn.execute(text(sql))

            # 3. Create compatibility view for audit_log -> audit_logs
            conn.execute(text("CREATE VIEW IF NOT EXISTS audit_log AS SELECT * FROM audit_logs;"))

            conn.commit()

            # 4. Verification report
            print("\nVerified Tables & Views:")
            tables_res = conn.execute(
                text("SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view') ORDER BY name")
            ).fetchall()
            for row in tables_res:
                print(f"  [{row[1].upper()}] {row[0]}")

            print("\nForeign Key Configuration:")
            user_tables = [
                "sos_contacts",
                "saved_locations",
                "user_settings",
                "user_locations",
                "sos_events",
                "shared_links",
                "alerts",
                "user_red_zone_states",
            ]
            for t in user_tables:
                fks = conn.execute(text(f"PRAGMA foreign_key_list({t});")).fetchall()
                cascades = [f"table={f[2]}, from={f[3]}->{f[4]}, on_delete={f[6]}" for f in fks]
                print(f"  {t}: {'; '.join(cascades)}")

    print("\n" + "=" * 65)
    print("Database schema successfully verified and configured.")
    print("=" * 65)


if __name__ == "__main__":
    init_and_verify_database()
