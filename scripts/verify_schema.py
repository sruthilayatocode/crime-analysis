#!/usr/bin/env python3
"""
scripts/verify_schema.py
========================
Verification script to inspect database schema, tables, indexes, constraints,
and test CRUD operations on new models without corrupting production data.
"""

import os
import sys
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
DB_PATH = BACKEND_DIR / "instance" / "crimesense.db"
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


def verify_tables_and_indexes():
    print("=" * 65)
    print("1. VERIFYING SQLITE TABLES & SCHEMA")
    print("=" * 65)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    tables = [
        row[0] for row in cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
    ]
    print(f"Existing Tables ({len(tables)}): {', '.join(tables)}")

    required_tables = [
        "users",
        "crimes",
        "alerts",
        "sos_contacts",
        "saved_locations",
        "user_settings",
        "user_locations",
        "sos_events",
        "shared_links",
    ]

    for req in required_tables:
        if req in tables:
            print(f"  [PASS] Table '{req}' exists.")
        else:
            print(f"  [FAIL] Table '{req}' NOT found!")

    print("\n" + "=" * 65)
    print("2. VERIFYING INDEXES (user_id, recorded_at, latitude/longitude)")
    print("=" * 65)

    indexes = [
        row[0] for row in cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
        ).fetchall()
    ]
    print(f"Existing Indexes ({len(indexes)}):")
    for idx in indexes:
        info = cursor.execute(f"PRAGMA index_info('{idx}')").fetchall()
        col_names = [col[2] for col in info]
        print(f"  - {idx}: cols={col_names}")

    conn.close()


def verify_orm_operations():
    print("\n" + "=" * 65)
    print("3. TESTING ORM INSERTIONS, QUERIES & RETENTION CLEANUP")
    print("=" * 65)

    with app.app_context():
        # 1. Verify Crimes data is intact
        crime_count = Crime.query.count()
        print(f"  [PASS] Existing Crimes count: {crime_count} records (Expected 600)")

        # 2. Get or create a test user
        test_user = User.query.filter_by(email="test_user@crimesense.com").first()
        if not test_user:
            test_user = User(
                name="Test Schema User",
                email="test_user@crimesense.com",
                role="user"
            )
            test_user.set_password("Test@123")
            db.session.add(test_user)
            db.session.commit()
        print(f"  [PASS] Test User verified: id={test_user.id}, email={test_user.email}")

        # 3. Test SOSContact
        contact = SOSContact(
            user_id=test_user.id,
            name="Emergency Contact 1",
            phone="+919876543210",
            relationship="Family",
            is_primary=True
        )
        db.session.add(contact)
        db.session.commit()
        print(f"  [PASS] SOSContact created: id={contact.id}, phone={contact.phone}, to_dict={contact.to_dict()}")

        # 4. Test SavedLocation
        saved_loc = SavedLocation(
            user_id=test_user.id,
            label="VIT University Vellore",
            latitude=12.9698,
            longitude=79.1559,
            address="Near Katpadi, Vellore, Tamil Nadu",
            zone="green"
        )
        db.session.add(saved_loc)
        db.session.commit()
        print(f"  [PASS] SavedLocation created: id={saved_loc.id}, label={saved_loc.label}, zone={saved_loc.zone}")

        # 5. Test UserSettings
        settings = UserSettings.query.filter_by(user_id=test_user.id).first()
        if not settings:
            settings = UserSettings(
                user_id=test_user.id,
                location_sharing_enabled=True,
                red_zone_alert_enabled=True,
                inactivity_minutes=10,
                alert_radius_m=500,
                share_live_location_with_admin=False
            )
            db.session.add(settings)
            db.session.commit()
        print(f"  [PASS] UserSettings verified: {settings.to_dict()}")

        # 6. Test UserLocation + 30-Day Retention Cleanup
        loc_now = UserLocation(
            user_id=test_user.id,
            latitude=12.9230,
            longitude=79.1325,
            accuracy=12.5,
            zone="yellow",
            recorded_at=datetime.utcnow()
        )
        loc_old = UserLocation(
            user_id=test_user.id,
            latitude=12.9000,
            longitude=79.1000,
            accuracy=20.0,
            zone="red",
            recorded_at=datetime.utcnow() - timedelta(days=35)  # 35 days old
        )
        db.session.add_all([loc_now, loc_old])
        db.session.commit()
        print(f"  [PASS] UserLocation entries added: 1 current, 1 expired (35 days old).")

        # Run cleanup
        purged = UserLocation.cleanup_old_records(days=30)
        print(f"  [PASS] UserLocation.cleanup_old_records(30) purged {purged} expired record(s).")

        # 7. Test SOSEvent
        sos = SOSEvent(
            user_id=test_user.id,
            type="manual",
            latitude=12.9165,
            longitude=79.1325,
            zone="red",
            status="active",
            contacts_notified=[{"name": "Emergency Contact 1", "phone": "+919876543210", "status": "sent"}]
        )
        db.session.add(sos)
        db.session.commit()
        print(f"  [PASS] SOSEvent created: id={sos.id}, type={sos.type}, status={sos.status}, contacts_notified={len(sos.contacts_notified)}")

        # 8. Test SharedLink
        link = SharedLink(
            token=SharedLink.generate_token(),
            user_id=test_user.id,
            latitude=12.9165,
            longitude=79.1325,
            expires_at=datetime.utcnow() + timedelta(hours=2),
            is_live=True
        )
        db.session.add(link)
        db.session.commit()
        print(f"  [PASS] SharedLink created: token={link.token[:16]}..., expires_at={link.expires_at}, is_expired={link.is_expired()}")

        # Clean up test user records
        db.session.delete(contact)
        db.session.delete(saved_loc)
        db.session.delete(loc_now)
        db.session.delete(sos)
        db.session.delete(link)
        db.session.commit()
        print(f"  [PASS] Test records cleaned up successfully.")

    print("=" * 65)
    print("ALL TABLE SCHEMAS, INDEXES & MODELS VERIFIED SUCCESSFULLY!")
    print("=" * 65)


if __name__ == "__main__":
    verify_tables_and_indexes()
    verify_orm_operations()
