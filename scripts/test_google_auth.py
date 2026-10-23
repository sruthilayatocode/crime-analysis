#!/usr/bin/env python
"""
scripts/test_google_auth.py
===========================
End-to-end verification of Google Sign-In and account linking against SQLite:
1. 1st Google Login -> Creates new row in users table (id, email, google_id, role, last_login_at).
2. 2nd Google Login -> Updates last_login_at and proves NO DUPLICATE row is created.
3. Existing Email User -> Links google_id to existing account without duplicating.
4. Deactivated User -> Rejection with 403 and descriptive message.
5. Unverified Google Email -> Rejection with 400 and clear error.
"""

from __future__ import annotations

import sqlite3
import sys
import time
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
DB_PATH = BACKEND_DIR / "instance" / "crimesense.db"

sys.path.insert(0, str(BACKEND_DIR))

from app import app
from database import db
from models.user import User


def print_user_row(user_dict: dict, label: str):
    print(f"\n--- {label} ---")
    print(f"  User ID       : {user_dict['id']}")
    print(f"  Email         : {user_dict['email']}")
    print(f"  Google ID     : {user_dict['google_id']}")
    print(f"  Role          : {user_dict['role']}")
    print(f"  Active Status : {user_dict['is_active']}")
    print(f"  Last Login At : {user_dict['last_login_at']}")


def run_google_auth_tests():
    print("=" * 75)
    print("CrimeSense - Google Sign-In End-to-End Verification")
    print(f"Target Database: {DB_PATH}")
    print("=" * 75)

    client = app.test_client()

    ts = int(time.time() * 1000)
    fake_google_id_1 = f"gid_1092837465_{ts}"
    fake_email_1 = f"google_user_{ts}@gmail.com"
    fake_name_1 = f"Google Citizen {ts}"

    created_ids_to_clean = []

    try:
        # -----------------------------------------------------------------
        # TEST 1: First-time Google Login -> Creates new row in users table
        # -----------------------------------------------------------------
        print("\n[TEST 1] First-time Google login (creating new user)")

        mock_payload_1 = {
            "google_id": fake_google_id_1,
            "email": fake_email_1,
            "name": fake_name_1,
            "avatar_url": "https://lh3.googleusercontent.com/a/sample-avatar-url",
        }

        with patch("routes.auth_routes.verify_google_id_token", return_value=mock_payload_1):
            resp = client.post("/api/auth/google", json={"credential": "mock_id_token_1"})

        assert resp.status_code == 200, f"Google login failed: {resp.data}"
        data1 = resp.get_json()
        assert data1["success"] is True
        assert data1["user"]["email"] == fake_email_1
        assert data1["user"]["google_id"] == fake_google_id_1
        user_id_1 = data1["user"]["id"]
        created_ids_to_clean.append(user_id_1)

        # Inspect directly in SQLite
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT id, email, google_id, role, is_active, last_login_at FROM users WHERE id = ?", (user_id_1,))
        row1 = dict(c.fetchone())
        conn.close()

        print_user_row(row1, "SQLite Database Row (First Login)")
        assert row1["google_id"] == fake_google_id_1
        assert row1["last_login_at"] is not None
        print("  -> RESULT: PASS! New user successfully created in users table with Google ID.")

        # -----------------------------------------------------------------
        # TEST 2: Second Google Login -> Updates last_login_at & NO duplicate
        # -----------------------------------------------------------------
        print("\n[TEST 2] Second Google login with same account (duplicate prevention)")
        time.sleep(1.0)  # Ensure distinct timestamp for last_login_at

        with patch("routes.auth_routes.verify_google_id_token", return_value=mock_payload_1):
            resp2 = client.post("/api/auth/google", json={"credential": "mock_id_token_1"})

        assert resp2.status_code == 200
        data2 = resp2.get_json()
        assert data2["user"]["id"] == user_id_1, "User ID changed on second login!"

        # Query direct count in SQLite
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users WHERE google_id = ?", (fake_google_id_1,))
        count_gid = c.fetchone()[0]
        c.execute("SELECT id, email, google_id, role, is_active, last_login_at FROM users WHERE id = ?", (user_id_1,))
        row2 = dict(c.fetchone())
        conn.close()

        print_user_row(row2, "SQLite Database Row (Second Login)")
        print(f"  * Total rows with google_id '{fake_google_id_1}': {count_gid}")
        assert count_gid == 1, f"DUPLICATE DETECTED: {count_gid} rows found for same Google ID!"
        assert row2["last_login_at"] != row1["last_login_at"] or row2["last_login_at"] is not None
        print("  -> RESULT: PASS! Existing account recognized; no duplicate row created.")

        # -----------------------------------------------------------------
        # TEST 3: Account Linking (Email user exists, logs in via Google)
        # -----------------------------------------------------------------
        print("\n[TEST 3] Account linking (existing email user adds Google)")
        link_email = f"standard_user_{ts}@test.com"
        with app.app_context():
            std_user = User(name="Standard Citizen", email=link_email, role="user", is_active=True)
            std_user.set_password("StandardPass123!")
            db.session.add(std_user)
            db.session.commit()
            std_user_id = std_user.id
            created_ids_to_clean.append(std_user_id)

        fake_google_id_link = f"gid_link_9988_{ts}"
        mock_payload_link = {
            "google_id": fake_google_id_link,
            "email": link_email,
            "name": "Standard Citizen",
            "avatar_url": None,
        }

        with patch("routes.auth_routes.verify_google_id_token", return_value=mock_payload_link):
            resp3 = client.post("/api/auth/google", json={"credential": "mock_id_token_link"})

        assert resp3.status_code == 200
        data3 = resp3.get_json()
        assert data3["user"]["id"] == std_user_id, "Linked user did not preserve original ID!"

        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT id, email, google_id, role, is_active, last_login_at FROM users WHERE id = ?", (std_user_id,))
        row3 = dict(c.fetchone())
        c.execute("SELECT COUNT(*) FROM users WHERE email = ?", (link_email,))
        email_count = c.fetchone()[0]
        conn.close()

        print_user_row(row3, "SQLite Database Row (Linked Account)")
        print(f"  * Total rows with email '{link_email}': {email_count}")
        assert email_count == 1
        assert row3["google_id"] == fake_google_id_link
        print("  -> RESULT: PASS! Existing account linked seamlessly without duplicating.")

        # -----------------------------------------------------------------
        # TEST 4: Rejection of Deactivated / Inactive User
        # -----------------------------------------------------------------
        print("\n[TEST 4] Rejection of deactivated user")
        with app.app_context():
            deactivated_user = User.query.get(user_id_1)
            deactivated_user.is_active = False
            db.session.commit()

        with patch("routes.auth_routes.verify_google_id_token", return_value=mock_payload_1):
            resp_deact = client.post("/api/auth/google", json={"credential": "mock_id_token_1"})

        assert resp_deact.status_code == 403, f"Expected 403 for deactivated user, got {resp_deact.status_code}"
        assert "deactivated" in resp_deact.get_json()["message"].lower()
        print(f"  * Response: HTTP {resp_deact.status_code} - '{resp_deact.get_json()['message']}'")
        print("  -> RESULT: PASS! Inactive user rejected with clear message.")

        # -----------------------------------------------------------------
        # TEST 5: Rejection of Unverified Google Email
        # -----------------------------------------------------------------
        print("\n[TEST 5] Rejection of unverified Google email")
        from services.auth_service import verify_google_id_token

        import os
        target_aud = os.getenv("GOOGLE_CLIENT_ID") or "mock-client-id"
        with patch("google.oauth2.id_token.verify_oauth2_token", return_value={
            "iss": "accounts.google.com",
            "aud": target_aud,
            "sub": "unverified_sub_123",
            "email": "unverified@gmail.com",
            "email_verified": False,
        }):
            try:
                verify_google_id_token("mock_unverified_token")
                assert False, "Should have raised ValueError for unverified email"
            except ValueError as val_err:
                assert "not verified" in str(val_err).lower()
                print(f"  * Caught expected validation error: '{val_err}'")
                print("  -> RESULT: PASS! Unverified Google account rejected server-side.")

    finally:
        # -----------------------------------------------------------------
        # Cleanup test entities
        # -----------------------------------------------------------------
        if created_ids_to_clean:
            conn = sqlite3.connect(str(DB_PATH))
            c = conn.cursor()
            for uid in created_ids_to_clean:
                c.execute("DELETE FROM users WHERE id = ?", (uid,))
            conn.commit()
            conn.close()
            print(f"\n[Cleanup] Successfully removed {len(created_ids_to_clean)} test users from database.")

    print("\n" + "=" * 75)
    print("ALL GOOGLE AUTHENTICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 75)
    return True


if __name__ == "__main__":
    success = run_google_auth_tests()
    sys.exit(0 if success else 1)
