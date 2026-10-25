"""
backend/tests/test_google_auth.py
==================================
Comprehensive Unit and Integration Tests for Google OAuth / GIS Sign-In Flow.
Tests:
- ID token verification (signature, issuer, audience, expiry, verified email)
- Invalid / malformed tokens
- First-time citizen sign-in & role separation (never automatic admin)
- Account deduplication
- Existing account linking & account takeover prevention
- Deactivated accounts
- CrimeSense JWT issuance & authentication integration
- Incident reporting submission & tracking by Google-authenticated citizens
- Role restriction (citizen forbidden from admin endpoints)
"""

import os
import time
import unittest
from unittest.mock import patch, MagicMock
from app import app
from database import db
from models.user import User
from models.crime import Crime
from services.auth_service import verify_google_id_token


class TestGoogleAuth(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        self.created_users = []
        self.created_crimes = []

    def tearDown(self):
        with app.app_context():
            for cid in self.created_crimes:
                c = db.session.get(Crime, cid)
                if c:
                    db.session.delete(c)
            for uid in self.created_users:
                u = db.session.get(User, uid)
                if u:
                    db.session.delete(u)
            db.session.commit()

    # -------------------------------------------------------------------------
    # Unit Tests for verify_google_id_token
    # -------------------------------------------------------------------------

    def test_verify_token_missing_client_id_config(self):
        """Should raise ValueError if GOOGLE_CLIENT_ID is not configured in backend."""
        with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "", "VITE_GOOGLE_CLIENT_ID": ""}):
            with self.assertRaises(ValueError) as ctx:
                verify_google_id_token("mock_token", client_id=None)
            self.assertIn("missing GOOGLE_CLIENT_ID", str(ctx.exception))

    def test_verify_token_malformed_string(self):
        """Should raise ValueError for non-string or malformed token string."""
        with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "test-client-id.apps.googleusercontent.com"}):
            with self.assertRaises(ValueError):
                verify_google_id_token("", client_id="test-client-id.apps.googleusercontent.com")
            with self.assertRaises(ValueError):
                verify_google_id_token("not-a-valid-jwt", client_id="test-client-id.apps.googleusercontent.com")

    def test_verify_token_wrong_audience(self):
        """Should raise ValueError when token audience does not match backend client ID."""
        mock_idinfo = {
            "iss": "https://accounts.google.com",
            "aud": "wrong-client-id.apps.googleusercontent.com",
            "exp": time.time() + 3600,
            "email_verified": True,
            "sub": "google_sub_123",
            "email": "test@example.com",
            "name": "Test User",
        }
        with patch("google.oauth2.id_token.verify_oauth2_token", return_value=mock_idinfo):
            with self.assertRaises(ValueError) as ctx:
                verify_google_id_token("valid_format_jwt", client_id="expected-client-id.apps.googleusercontent.com")
            self.assertIn("audience mismatch", str(ctx.exception).lower())

    def test_verify_token_expired(self):
        """Should raise ValueError when token exp claim is in the past."""
        mock_idinfo = {
            "iss": "https://accounts.google.com",
            "aud": "test-client-id.apps.googleusercontent.com",
            "exp": time.time() - 3600,  # 1 hour ago
            "email_verified": True,
            "sub": "google_sub_123",
            "email": "test@example.com",
        }
        with patch("google.oauth2.id_token.verify_oauth2_token", return_value=mock_idinfo):
            with self.assertRaises(ValueError) as ctx:
                verify_google_id_token("valid_format_jwt", client_id="test-client-id.apps.googleusercontent.com")
            self.assertIn("expired", str(ctx.exception).lower())

    def test_verify_token_unverified_email(self):
        """Should raise ValueError if Google reports email_verified is False."""
        mock_idinfo = {
            "iss": "https://accounts.google.com",
            "aud": "test-client-id.apps.googleusercontent.com",
            "exp": time.time() + 3600,
            "email_verified": False,
            "sub": "google_sub_123",
            "email": "unverified@example.com",
        }
        with patch("google.oauth2.id_token.verify_oauth2_token", return_value=mock_idinfo):
            with self.assertRaises(ValueError) as ctx:
                verify_google_id_token("valid_format_jwt", client_id="test-client-id.apps.googleusercontent.com")
            self.assertIn("not verified", str(ctx.exception).lower())

    def test_verify_token_invalid_issuer(self):
        """Should raise ValueError if iss is not from accounts.google.com."""
        mock_idinfo = {
            "iss": "https://attacker-domain.com",
            "aud": "test-client-id.apps.googleusercontent.com",
            "exp": time.time() + 3600,
            "email_verified": True,
            "sub": "google_sub_123",
            "email": "user@example.com",
        }
        with patch("google.oauth2.id_token.verify_oauth2_token", return_value=mock_idinfo):
            with self.assertRaises(ValueError) as ctx:
                verify_google_id_token("valid_format_jwt", client_id="test-client-id.apps.googleusercontent.com")
            self.assertIn("invalid google token issuer", str(ctx.exception).lower())

    def test_verify_token_success(self):
        """Should return normalized profile dictionary upon successful verification."""
        mock_idinfo = {
            "iss": "https://accounts.google.com",
            "aud": "test-client-id.apps.googleusercontent.com",
            "exp": time.time() + 3600,
            "email_verified": True,
            "sub": "google_sub_999",
            "email": "citizen@gmail.com",
            "name": "Jane Citizen",
            "picture": "https://example.com/avatar.jpg",
        }
        with patch("google.oauth2.id_token.verify_oauth2_token", return_value=mock_idinfo):
            profile = verify_google_id_token("valid_format_jwt", client_id="test-client-id.apps.googleusercontent.com")
            self.assertEqual(profile["google_id"], "google_sub_999")
            self.assertEqual(profile["email"], "citizen@gmail.com")
            self.assertEqual(profile["name"], "Jane Citizen")
            self.assertEqual(profile["avatar_url"], "https://example.com/avatar.jpg")

    # -------------------------------------------------------------------------
    # Integration Tests for POST /api/auth/google Endpoint
    # -------------------------------------------------------------------------

    def test_google_login_endpoint_first_time_citizen_role_and_jwt(self):
        """
        First-time Google sign-in should:
        1. Create new user with normal citizen role ('user') - never admin.
        2. Mark account as verified.
        3. Issue valid CrimeSense JWT token and refresh token.
        """
        ts = int(time.time() * 1000)
        fake_gid = f"gid_new_{ts}"
        fake_email = f"new_citizen_{ts}@test.com"

        mock_profile = {
            "google_id": fake_gid,
            "email": fake_email,
            "name": "New Citizen User",
            "avatar_url": "https://example.com/citizen.png",
        }

        with patch("routes.auth_routes.verify_google_id_token", return_value=mock_profile):
            resp = self.client.post("/api/auth/google", json={"credential": "mock_jwt_credential"})

        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertIn("token", data)
        self.assertIn("refresh_token", data)
        self.assertEqual(data["role"], "user")
        self.assertEqual(data["user"]["role"], "user")
        self.assertTrue(data["user"]["is_verified"])
        self.assertEqual(data["user"]["email"], fake_email)

        user_id = data["user"]["id"]
        self.created_users.append(user_id)

        # Confirm in DB
        with app.app_context():
            u = db.session.get(User, user_id)
            self.assertIsNotNone(u)
            self.assertEqual(u.role, "user")
            self.assertTrue(u.is_verified)
            self.assertEqual(u.google_id, fake_gid)

    def test_google_login_endpoint_deduplication(self):
        """Subsequent logins with the same Google ID should not duplicate records."""
        ts = int(time.time() * 1000)
        fake_gid = f"gid_dedup_{ts}"
        fake_email = f"dedup_user_{ts}@test.com"

        mock_profile = {
            "google_id": fake_gid,
            "email": fake_email,
            "name": "Dedup Citizen",
            "avatar_url": None,
        }

        with patch("routes.auth_routes.verify_google_id_token", return_value=mock_profile):
            resp1 = self.client.post("/api/auth/google", json={"credential": "cred_1"})
            data1 = resp1.get_json()
            user_id = data1["user"]["id"]
            self.created_users.append(user_id)

            resp2 = self.client.post("/api/auth/google", json={"credential": "cred_2"})
            data2 = resp2.get_json()
            self.assertEqual(data2["user"]["id"], user_id)

        with app.app_context():
            count = User.query.filter_by(google_id=fake_gid).count()
            self.assertEqual(count, 1)

    def test_google_login_endpoint_account_linking_existing_citizen(self):
        """
        If a citizen user already exists with matching email (registered via email/password),
        Google login should link their Google ID safely and mark is_verified=True.
        """
        ts = int(time.time() * 1000)
        fake_email = f"existing_citizen_{ts}@test.com"
        fake_gid = f"gid_linked_{ts}"

        with app.app_context():
            existing = User(
                name="Existing Citizen",
                email=fake_email,
                role="user",
                is_active=True,
                is_verified=False
            )
            existing.set_password("CitizenPass123!")
            db.session.add(existing)
            db.session.commit()
            uid = existing.id
            self.created_users.append(uid)

        mock_profile = {
            "google_id": fake_gid,
            "email": fake_email,
            "name": "Existing Citizen Google",
            "avatar_url": "https://example.com/new_avatar.png",
        }

        with patch("routes.auth_routes.verify_google_id_token", return_value=mock_profile):
            resp = self.client.post("/api/auth/google", json={"credential": "mock_cred"})

        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["user"]["id"], uid)
        self.assertEqual(data["user"]["google_id"], fake_gid)

        with app.app_context():
            u = db.session.get(User, uid)
            self.assertEqual(u.google_id, fake_gid)
            self.assertTrue(u.is_verified)
            # Ensure password hash is preserved (email/password login remains intact)
            self.assertTrue(u.check_password("CitizenPass123!"))

    def test_google_login_prevents_account_takeover_different_google_id(self):
        """
        If an account with email is already bound to Google ID A,
        attempting to authenticate with Google ID B under that email must be rejected (409 Conflict).
        """
        ts = int(time.time() * 1000)
        fake_email = f"takeover_test_{ts}@test.com"
        legit_gid = f"gid_legit_{ts}"
        attacker_gid = f"gid_attacker_{ts}"

        with app.app_context():
            legit_user = User(
                name="Legit User",
                email=fake_email,
                google_id=legit_gid,
                role="user",
                is_active=True,
                is_verified=True
            )
            db.session.add(legit_user)
            db.session.commit()
            uid = legit_user.id
            self.created_users.append(uid)

        mock_profile = {
            "google_id": attacker_gid,
            "email": fake_email,
            "name": "Attacker",
            "avatar_url": None,
        }

        with patch("routes.auth_routes.verify_google_id_token", return_value=mock_profile):
            resp = self.client.post("/api/auth/google", json={"credential": "attacker_cred"})

        self.assertEqual(resp.status_code, 409)
        self.assertIn("already associated with a different Google account", resp.get_json()["message"])

    def test_google_login_prevents_admin_account_takeover(self):
        """
        Administrator accounts cannot be linked via Google Sign-In,
        preventing account takeover and automatic admin escalation.
        """
        ts = int(time.time() * 1000)
        admin_email = f"admin_security_{ts}@test.com"
        fake_gid = f"gid_attacker_{ts}"

        with app.app_context():
            admin_user = User(
                name="Admin User",
                email=admin_email,
                google_id=None,
                role="admin",
                is_active=True,
                is_verified=True
            )
            admin_user.set_password("AdminSecret123!")
            db.session.add(admin_user)
            db.session.commit()
            uid = admin_user.id
            self.created_users.append(uid)

        mock_profile = {
            "google_id": fake_gid,
            "email": admin_email,
            "name": "Admin Impersonator",
            "avatar_url": None,
        }

        with patch("routes.auth_routes.verify_google_id_token", return_value=mock_profile):
            resp = self.client.post("/api/auth/google", json={"credential": "cred"})

        self.assertEqual(resp.status_code, 403)
        self.assertIn("administrator accounts cannot be linked", resp.get_json()["message"].lower())

    def test_google_login_inactive_user_rejected(self):
        """Deactivated accounts cannot log in via Google."""
        ts = int(time.time() * 1000)
        fake_gid = f"inactive_gid_{ts}"
        fake_email = f"inactive_{ts}@test.com"

        with app.app_context():
            u = User(name="Inactive User", email=fake_email, google_id=fake_gid, role="user", is_active=False)
            db.session.add(u)
            db.session.commit()
            uid = u.id
            self.created_users.append(uid)

        mock_profile = {
            "google_id": fake_gid,
            "email": fake_email,
            "name": "Inactive User",
            "avatar_url": None,
        }

        with patch("routes.auth_routes.verify_google_id_token", return_value=mock_profile):
            resp = self.client.post("/api/auth/google", json={"credential": "mock_cred"})

        self.assertEqual(resp.status_code, 403)
        self.assertIn("deactivated", resp.get_json()["message"].lower())

    # -------------------------------------------------------------------------
    # Incident Reporting & Role Separation for Google-Authenticated Citizen
    # -------------------------------------------------------------------------

    def test_google_authenticated_citizen_incident_reporting_and_tracking(self):
        """
        Verify that a citizen authenticated via Google receives a CrimeSense JWT
        that successfully authorizes:
        1. Submitting a new incident report (POST /api/crimes/report).
        2. Tracking their submitted reports (GET /api/crimes/my-reports).
        3. Enforces role separation: citizen is denied access to admin-only review routes (403).
        """
        ts = int(time.time() * 1000)
        fake_gid = f"citizen_reporter_gid_{ts}"
        fake_email = f"reporter_{ts}@test.com"

        mock_profile = {
            "google_id": fake_gid,
            "email": fake_email,
            "name": "Google Reporter Citizen",
            "avatar_url": None,
        }

        # Step 1: Sign in with Google
        with patch("routes.auth_routes.verify_google_id_token", return_value=mock_profile):
            resp = self.client.post("/api/auth/google", json={"credential": "mock_token"})
        self.assertEqual(resp.status_code, 200)
        auth_data = resp.get_json()
        token = auth_data["token"]
        uid = auth_data["user"]["id"]
        self.created_users.append(uid)

        auth_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        # Step 2: Submit an incident report
        report_payload = {
            "crime_type": "Theft",
            "description": "Bicycle stolen from public bike rack near metro station",
            "location_name": "Indiranagar Metro Station",
            "crime_date": "2026-10-25T14:30:00",
            "latitude": 12.9784,
            "longitude": 77.6408,
            "severity": "Low",
        }
        submit_resp = self.client.post("/api/crimes/report", json=report_payload, headers=auth_headers)
        self.assertEqual(submit_resp.status_code, 201)
        submit_data = submit_resp.get_json()
        self.assertTrue(submit_data["success"])
        crime_id = submit_data["data"]["id"]
        self.created_crimes.append(crime_id)
        self.assertEqual(submit_data["data"]["reported_by_id"], uid)
        self.assertEqual(submit_data["data"]["status"], "PENDING")

        # Step 3: Track their submitted reports
        track_resp = self.client.get("/api/crimes/my-reports", headers=auth_headers)
        self.assertEqual(track_resp.status_code, 200)
        track_data = track_resp.get_json()
        self.assertTrue(track_data["success"])
        my_report_ids = [r["id"] for r in track_data["data"]]
        self.assertIn(crime_id, my_report_ids)

        # Step 4: Role separation - citizen must be forbidden from administrative pending reports endpoint
        admin_resp = self.client.get("/api/admin/crimes/pending", headers=auth_headers)
        self.assertEqual(admin_resp.status_code, 403)


if __name__ == "__main__":
    unittest.main()
