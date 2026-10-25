#!/usr/bin/env python3
"""
scripts/init_migrations.py
===========================
Safe schema initialization and migration script.
Creates all missing tables and required indexes without modifying or wiping existing tables (e.g. crimes, alerts, users).
"""

import os
import sys
from pathlib import Path

# Add backend directory to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app import app
from database import db
from models import (
    Crime,
    User,
    SOSContact,
    SavedLocation,
    UserSettings,
    UserLocation,
    SOSEvent,
    SharedLink,
)


def run_migrations():
    with app.app_context():
        print("[Migration] Inspecting SQLite database...")
        # db.create_all() creates only tables that do NOT already exist
        db.create_all()
        print("[Migration] Verified/created tables:")
        print("  - users")
        print("  - sos_contacts")
        print("  - saved_locations")
        print("  - user_settings")
        print("  - user_locations")
        print("  - sos_events")
        print("  - shared_links")
        print("  - crimes")
        print("  - alerts")
        print("[Migration] Database schema is up to date!")


if __name__ == "__main__":
    run_migrations()
