"""
test_persistence_e2e.py
========================
End-to-End Database Persistence Test for CrimeSense.

Verifies:
1. Citizen user signs up via API.
2. User adds an SOS emergency contact.
3. User saves a custom location with coordinates.
4. User updates their safety and location sharing settings.
5. User sends a location heartbeat.
6. Direct SQLite inspection: Verifies directly via sqlite3 (bypassing the app) that
   rows are stored on disk in SQLite with accurate data.
7. App restart simulation: Creates a new application context and validates data persists across restarts.
8. Cleans up test entities and confirms foreign-key cascades delete all child records.
"""

import os
import sqlite3
import sys
import time
from pathlib import Path
import pytest

# Ensure backend directory is in sys.path
TEST_DIR = Path(__file__).resolve().parent
BACKEND_DIR = TEST_DIR.parent
DB_PATH = BACKEND_DIR / "instance" / "crimesense.db"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import app
from database import db
from models.user import User


def get_direct_db_conn():
    """Direct sqlite3 connection to verify disk state independently."""
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


@pytest.fixture
def client():
    """Test client fixture."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_end_to_end_persistence(client):
    unique_suffix = int(time.time() * 1000)
    test_email = f"persistence_test_{unique_suffix}@test.com"
    test_password = "Password123!"
    test_name = f"Test User {unique_suffix}"

    created_user_id = None

    try:
        # -------------------------------------------------------------
        # Step 1: Sign up a test citizen user
        # -------------------------------------------------------------
        signup_resp = client.post(
            "/api/auth/signup",
            json={"name": test_name, "email": test_email, "password": test_password},
        )
        assert signup_resp.status_code == 201, f"Signup failed: {signup_resp.data}"
        signup_data = signup_resp.get_json()
        assert signup_data["success"] is True
        token = signup_data["token"]
        created_user_id = signup_data["user"]["id"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # -------------------------------------------------------------
        # Step 2: Add an emergency SOS contact
        # -------------------------------------------------------------
        contact_payload = {
            "name": "Trusted Guardian",
            "phone": "+919876543210",
            "relationship": "Parent",
            "is_primary": True,
        }
        contact_resp = client.post(
            "/api/user/sos-contacts",
            headers=auth_headers,
            json=contact_payload,
        )
        assert contact_resp.status_code == 201, f"Add contact failed: {contact_resp.data}"
        contact_data = contact_resp.get_json()
        assert contact_data["success"] is True
        contact_id = contact_data["contact"]["id"]

        # -------------------------------------------------------------
        # Step 3: Save a destination / location
        # -------------------------------------------------------------
        saved_loc_payload = {
            "label": "Home Safe Zone",
            "address": "Gandhi Road, Vellore",
            "latitude": 12.9246,
            "longitude": 79.1348,
            "is_pinned": True,
        }
        loc_resp = client.post(
            "/api/user/saved-locations",
            headers=auth_headers,
            json=saved_loc_payload,
        )
        assert loc_resp.status_code in (200, 201), f"Save location failed: {loc_resp.data}"
        loc_data = loc_resp.get_json()
        assert loc_data["success"] is True
        saved_loc_id = loc_data["location"]["id"]

        # -------------------------------------------------------------
        # Step 4: Update user settings
        # -------------------------------------------------------------
        settings_payload = {
            "location_sharing_enabled": True,
            "red_zone_alert_enabled": True,
            "inactivity_minutes": 15,
            "alert_radius_m": 750,
            "share_live_location_with_admin": False,
        }
        settings_resp = client.post(
            "/api/user/settings",
            headers=auth_headers,
            json=settings_payload,
        )
        assert settings_resp.status_code == 200, f"Update settings failed: {settings_resp.data}"
        settings_data = settings_resp.get_json()
        assert settings_data["settings"]["inactivity_minutes"] == 15
        assert settings_data["settings"]["alert_radius_m"] == 750

        # -------------------------------------------------------------
        # Step 5: Send a location heartbeat
        # -------------------------------------------------------------
        heartbeat_payload = {
            "latitude": 12.9250,
            "longitude": 79.1355,
            "accuracy": 8.5,
            "zone": "green",
        }
        hb_resp = client.post(
            "/api/user/location",
            headers=auth_headers,
            json=heartbeat_payload,
        )
        assert hb_resp.status_code == 201, f"Location heartbeat failed: {hb_resp.data}"
        hb_data = hb_resp.get_json()
        assert hb_data["saved"] is True

        # -------------------------------------------------------------
        # Step 6: Verify rows DIRECTLY in SQLite via raw SQL
        # -------------------------------------------------------------
        direct_conn = get_direct_db_conn()

        # 6a. Verify User
        user_row = direct_conn.execute(
            "SELECT * FROM users WHERE id = ?", (created_user_id,)
        ).fetchone()
        assert user_row is not None, "Direct SQLite check: User row not found!"
        assert user_row["email"] == test_email
        assert user_row["name"] == test_name
        assert user_row["last_login_at"] is not None

        # 6b. Verify SOSContact
        contact_row = direct_conn.execute(
            "SELECT * FROM sos_contacts WHERE id = ? AND user_id = ?",
            (contact_id, created_user_id),
        ).fetchone()
        assert contact_row is not None, "Direct SQLite check: SOSContact row not found!"
        assert contact_row["name"] == "Trusted Guardian"
        assert contact_row["phone"] == "+919876543210"
        assert contact_row["is_primary"] in (1, True)

        # 6c. Verify SavedLocation
        saved_row = direct_conn.execute(
            "SELECT * FROM saved_locations WHERE id = ? AND user_id = ?",
            (saved_loc_id, created_user_id),
        ).fetchone()
        assert saved_row is not None, "Direct SQLite check: SavedLocation row not found!"
        assert saved_row["label"] == "Home Safe Zone"
        assert round(saved_row["latitude"], 4) == 12.9246
        assert round(saved_row["longitude"], 4) == 79.1348
        assert saved_row["is_pinned"] in (1, True)

        # 6d. Verify UserSettings
        settings_row = direct_conn.execute(
            "SELECT * FROM user_settings WHERE user_id = ?", (created_user_id,)
        ).fetchone()
        assert settings_row is not None, "Direct SQLite check: UserSettings row not found!"
        assert settings_row["inactivity_minutes"] == 15
        assert settings_row["alert_radius_m"] == 750
        assert settings_row["location_sharing_enabled"] in (1, True)

        # 6e. Verify UserLocation (heartbeat)
        loc_history_rows = direct_conn.execute(
            "SELECT * FROM user_locations WHERE user_id = ?", (created_user_id,)
        ).fetchall()
        assert len(loc_history_rows) >= 1, "Direct SQLite check: UserLocation heartbeat row not found!"
        assert round(loc_history_rows[0]["latitude"], 4) == 12.9250
        assert round(loc_history_rows[0]["longitude"], 4) == 79.1355

        direct_conn.close()

        # -------------------------------------------------------------
        # Step 7: Restart simulation (verify persistence across sessions)
        # -------------------------------------------------------------
        # Close test client and spawn a fresh client on the same database
        with app.test_client() as new_client:
            # Query settings
            re_settings_resp = new_client.get("/api/user/settings", headers=auth_headers)
            assert re_settings_resp.status_code == 200
            re_settings_data = re_settings_resp.get_json()
            assert re_settings_data["settings"]["alert_radius_m"] == 750
            assert re_settings_data["settings"]["inactivity_minutes"] == 15

            # Query saved locations
            re_loc_resp = new_client.get("/api/user/saved-locations", headers=auth_headers)
            assert re_loc_resp.status_code == 200
            re_loc_data = re_loc_resp.get_json()
            labels = [loc["label"] for loc in re_loc_data["locations"]]
            assert "Home Safe Zone" in labels

            # Query contacts
            re_contacts_resp = new_client.get("/api/user/sos-contacts", headers=auth_headers)
            assert re_contacts_resp.status_code == 200
            re_contacts_data = re_contacts_resp.get_json()
            contact_names = [c["name"] for c in re_contacts_data["contacts"]]
            assert "Trusted Guardian" in contact_names

    finally:
        # -------------------------------------------------------------
        # Step 8: Clean up test entities and verify CASCADE deletion
        # -------------------------------------------------------------
        if created_user_id:
            cleanup_conn = get_direct_db_conn()
            cleanup_conn.execute("DELETE FROM users WHERE id = ?", (created_user_id,))
            cleanup_conn.commit()

            # Confirm parent user is removed
            u_check = cleanup_conn.execute(
                "SELECT COUNT(*) FROM users WHERE id = ?", (created_user_id,)
            ).fetchone()[0]
            assert u_check == 0

            # Confirm CASCADE deleted child records
            c_check = cleanup_conn.execute(
                "SELECT COUNT(*) FROM sos_contacts WHERE user_id = ?", (created_user_id,)
            ).fetchone()[0]
            assert c_check == 0, f"CASCADE failed: {c_check} orphan sos_contacts remain!"

            l_check = cleanup_conn.execute(
                "SELECT COUNT(*) FROM saved_locations WHERE user_id = ?", (created_user_id,)
            ).fetchone()[0]
            assert l_check == 0, f"CASCADE failed: {l_check} orphan saved_locations remain!"

            s_check = cleanup_conn.execute(
                "SELECT COUNT(*) FROM user_settings WHERE user_id = ?", (created_user_id,)
            ).fetchone()[0]
            assert s_check == 0, f"CASCADE failed: {s_check} orphan user_settings remain!"

            h_check = cleanup_conn.execute(
                "SELECT COUNT(*) FROM user_locations WHERE user_id = ?", (created_user_id,)
            ).fetchone()[0]
            assert h_check == 0, f"CASCADE failed: {h_check} orphan user_locations remain!"

            cleanup_conn.close()


if __name__ == "__main__":
    pytest.main(["-v", __file__])
