"""
backend/tests/test_google_auth.py
==================================
Unit and integration tests for Google OAuth sign-in flow.
Compatible with standard unittest and pytest.
"""

import time
import unittest
from unittest.mock import patch
from app import app
from database import db
from models.user import User


class TestGoogleAuth(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_google_login_new_user_and_deduplication(self):
        ts = int(time.time() * 1000)
        fake_gid = f"test_gid_{ts}"
        fake_email = f"unittest_google_{ts}@test.com"

        mock_profile = {
            "google_id": fake_gid,
            "email": fake_email,
            "name": "Unittest Google User",
            "avatar_url": "https://example.com/avatar.png",
        }

        user_id = None
        try:
            # First login: creates new user
            with patch("routes.auth_routes.verify_google_id_token", return_value=mock_profile):
                resp1 = self.client.post("/api/auth/google", json={"credential": "mock_cred_1"})
            self.assertEqual(resp1.status_code, 200)
            data1 = resp1.get_json()
            self.assertTrue(data1["success"])
            user_id = data1["user"]["id"]
            self.assertEqual(data1["user"]["email"], fake_email)
            self.assertEqual(data1["user"]["google_id"], fake_gid)
            self.assertEqual(data1["role"], "user")

            # Second login: no duplicate created, same user ID
            with patch("routes.auth_routes.verify_google_id_token", return_value=mock_profile):
                resp2 = self.client.post("/api/auth/google", json={"credential": "mock_cred_2"})
            self.assertEqual(resp2.status_code, 200)
            data2 = resp2.get_json()
            self.assertEqual(data2["user"]["id"], user_id)

            # Verify DB count
            with app.app_context():
                count = User.query.filter_by(google_id=fake_gid).count()
                self.assertEqual(count, 1)
        finally:
            if user_id:
                with app.app_context():
                    User.query.filter_by(id=user_id).delete()
                    db.session.commit()

    def test_google_login_inactive_user_rejected(self):
        ts = int(time.time() * 1000)
        fake_gid = f"inactive_gid_{ts}"
        fake_email = f"inactive_{ts}@test.com"

        with app.app_context():
            u = User(name="Inactive User", email=fake_email, google_id=fake_gid, role="user", is_active=False)
            db.session.add(u)
            db.session.commit()
            uid = u.id

        try:
            with patch("routes.auth_routes.verify_google_id_token", return_value={
                "google_id": fake_gid,
                "email": fake_email,
                "name": "Inactive User",
                "avatar_url": None,
            }):
                resp = self.client.post("/api/auth/google", json={"credential": "mock_cred"})
            self.assertEqual(resp.status_code, 403)
            self.assertIn("deactivated", resp.get_json()["message"].lower())
        finally:
            with app.app_context():
                User.query.filter_by(id=uid).delete()
                db.session.commit()


if __name__ == "__main__":
    unittest.main()
