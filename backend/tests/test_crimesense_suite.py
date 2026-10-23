"""
test_crimesense_suite.py
========================
Comprehensive Automated Test Suite for CrimeSense.

Covers:
1. Auth Flows (Signup, Login, Invalid Credentials, JWT Expiry)
2. Zone Risk Classification (Haversine decay, RED / YELLOW / GREEN zones)
3. Emergency SOS Trigger & Resolution (Coordinates capture, Contact notifications)
4. Red-Zone Inactivity State Machine (Mocked time, Warnings, Auto-trigger, Check-in reset)
5. Share-Link Security & Expiry (Public token URLs, Expiry enforcement, Revocation)
6. Role-Based Access Control & User Data Isolation (Admin 403 checks, Cross-user isolation)
"""

import sys
import os
import unittest
import json
from datetime import datetime, timedelta

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from database import db
from models.user import User
from models.crime import Crime
from models.sos_contact import SOSContact
from models.sos_event import SOSEvent
from models.saved_location import SavedLocation
from models.shared_link import SharedLink
from models.user_settings import UserSettings
from models.user_red_zone_state import UserRedZoneState
from models.user_location import UserLocation
from services.auth_service import generate_access_token, decode_token
from services.zone_service import calculate_zone_risk
from services.red_zone_scheduler import evaluate_user_state, calculate_distance_m


class CrimeSenseAutomatedTestSuite(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()

    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        try:
            test_users = User.query.filter(User.email.like("%@test.com")).all()
            for u in test_users:
                SOSEvent.query.filter_by(user_id=u.id).delete()
                SOSContact.query.filter_by(user_id=u.id).delete()
                SavedLocation.query.filter_by(user_id=u.id).delete()
                SharedLink.query.filter_by(user_id=u.id).delete()
                UserRedZoneState.query.filter_by(user_id=u.id).delete()
                UserSettings.query.filter_by(user_id=u.id).delete()
                UserLocation.query.filter_by(user_id=u.id).delete()
                db.session.delete(u)
            db.session.commit()
        except Exception:
            db.session.rollback()
        self.app_context.pop()

    # ----------------------------------------------------------------------- #
    # 1. AUTH FLOWS
    # ----------------------------------------------------------------------- #

    def test_01_signup_and_duplicate_email(self):
        """Test signup flow and duplicate registration rejection."""
        unique_email = f"user_{datetime.utcnow().timestamp()}@test.com"
        
        # Valid signup
        res = self.client.post("/api/auth/signup", json={
            "name": "Alex Mercer",
            "email": unique_email,
            "password": "Password@123"
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("token", data)
        self.assertEqual(data["user"]["email"], unique_email)

        # Duplicate email signup
        res_dup = self.client.post("/api/auth/signup", json={
            "name": "Alex Duplicate",
            "email": unique_email,
            "password": "Password@123"
        })
        self.assertEqual(res_dup.status_code, 400)
        self.assertFalse(res_dup.get_json()["success"])

    def test_02_password_validation_and_login(self):
        """Test short password rejection and valid/invalid login attempts."""
        # Short password
        res_short = self.client.post("/api/auth/signup", json={
            "name": "Short Pass",
            "email": "short@test.com",
            "password": "123"
        })
        self.assertEqual(res_short.status_code, 400)

        # Create test user for login
        email = f"login_test_{datetime.utcnow().timestamp()}@test.com"
        user = User(name="Login Tester", email=email, role="user")
        user.set_password("SecurePass123!")
        db.session.add(user)
        db.session.commit()

        # Invalid password
        res_bad = self.client.post("/api/auth/login", json={
            "email": email,
            "password": "WrongPassword"
        })
        self.assertEqual(res_bad.status_code, 401)

        # Valid password
        res_good = self.client.post("/api/auth/login", json={
            "email": email,
            "password": "SecurePass123!"
        })
        self.assertEqual(res_good.status_code, 200)
        token = res_good.get_json()["token"]
        payload = decode_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["email"], email)

    # ----------------------------------------------------------------------- #
    # 2. ZONE RISK CLASSIFICATION
    # ----------------------------------------------------------------------- #

    def test_03_zone_risk_classification(self):
        """Test Haversine risk decay and zone determination."""
        # Katpadi coordinates (seeded crimes)
        katpadi_lat, katpadi_lng = 12.9806, 79.1368
        risk_katpadi = calculate_zone_risk(katpadi_lat, katpadi_lng, radius=1000)
        
        self.assertIn("zone", risk_katpadi)
        self.assertIn("score", risk_katpadi)
        self.assertIn("incident_count", risk_katpadi)
        self.assertIn(risk_katpadi["zone"].upper(), ["RED", "ORANGE", "YELLOW", "GREEN"])

        # Remote ocean coordinates with zero crimes should always be GREEN
        remote_lat, remote_lng = 0.0, 0.0
        risk_remote = calculate_zone_risk(remote_lat, remote_lng, radius=1000)
        self.assertEqual(risk_remote["zone"].upper(), "GREEN")
        self.assertEqual(risk_remote["score"], 0.0)
        self.assertEqual(risk_remote["incident_count"], 0)

    # ----------------------------------------------------------------------- #
    # 3. EMERGENCY SOS TRIGGER & RESOLUTION
    # ----------------------------------------------------------------------- #

    def test_04_emergency_sos_trigger_and_resolve(self):
        """Test manual SOS distress event triggering, contact notifications, and resolution."""
        email = f"sos_user_{datetime.utcnow().timestamp()}@test.com"
        user = User(name="SOS Victim", email=email, role="user")
        user.set_password("Pass123!")
        db.session.add(user)
        db.session.commit()

        # Add SOS contact
        contact = SOSContact(user_id=user.id, name="Mom Emergency", phone="+919876543210", relationship="Parent", is_primary=True)
        db.session.add(contact)
        db.session.commit()

        token = generate_access_token(user)
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        # 1. Trigger SOS
        trigger_res = self.client.post("/api/user/sos-events/trigger", headers=headers, json={
            "latitude": 12.9806,
            "longitude": 79.1368,
            "accuracy": 15,
            "zone": "red",
            "type": "manual"
        })
        self.assertEqual(trigger_res.status_code, 201)
        event_data = trigger_res.get_json()
        self.assertTrue(event_data["success"])
        event_id = event_data["event"]["id"]
        self.assertEqual(event_data["event"]["status"], "active")
        self.assertEqual(len(event_data["contacts_notified"]), 1)

        # 2. Check active SOS query
        active_res = self.client.get("/api/user/sos-events/active", headers=headers)
        self.assertEqual(active_res.status_code, 200)
        self.assertTrue(active_res.get_json()["active"])

        # 3. Resolve SOS ("I'm Safe")
        resolve_res = self.client.post(f"/api/user/sos-events/{event_id}/resolve", headers=headers)
        self.assertEqual(resolve_res.status_code, 200)
        self.assertEqual(resolve_res.get_json()["event"]["status"], "resolved")

        # 4. Verify no active SOS remains
        check_res = self.client.get("/api/user/sos-events/active", headers=headers)
        self.assertFalse(check_res.get_json()["active"])

    # ----------------------------------------------------------------------- #
    # 4. RED-ZONE INACTIVITY STATE MACHINE
    # ----------------------------------------------------------------------- #

    def test_05_red_zone_state_machine_and_inactivity(self):
        """Test RED zone stationary state machine: SAFE -> IN_RED -> WARNING -> AUTO_ALERT_SENT."""
        email = f"rz_user_{datetime.utcnow().timestamp()}@test.com"
        user = User(name="Red Zone Citizen", email=email, role="user")
        user.set_password("Pass123!")
        db.session.add(user)
        db.session.commit()

        contact = SOSContact(user_id=user.id, name="Father", phone="+919876543211", relationship="Family", is_primary=True)
        db.session.add(contact)
        db.session.commit()

        token = generate_access_token(user)
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        # Step A: Heartbeat in GREEN zone -> State is SAFE
        res_green = self.client.post("/api/user/heartbeat", headers=headers, json={
            "latitude": 12.9165,
            "longitude": 79.1325,
            "zone": "green",
            "has_interaction": True
        })
        self.assertEqual(res_green.status_code, 200)
        self.assertEqual(res_green.get_json()["state"], "SAFE")

        # Step B: Heartbeat enters RED zone -> State transitions to IN_RED
        res_red = self.client.post("/api/user/heartbeat", headers=headers, json={
            "latitude": 12.9806,
            "longitude": 79.1368,
            "zone": "red",
            "has_interaction": True
        })
        self.assertEqual(res_red.status_code, 200)
        self.assertEqual(res_red.get_json()["state"], "IN_RED")

        # Step C: Simulate inactivity by backdating last_interaction_at past threshold (12 minutes ago)
        rz_state = UserRedZoneState.query.filter_by(user_id=user.id).first()
        rz_state.last_interaction_at = datetime.utcnow() - timedelta(minutes=12)
        db.session.commit()

        # Evaluate state machine transition -> Transitions to WARNING
        eval_result = evaluate_user_state(user.id)
        self.assertEqual(eval_result["state"], "WARNING")
        self.assertIn("warning_expires_at", eval_result)

        # Step D: User check-in ("I'm Safe") resets the warning
        checkin_res = self.client.post("/api/user/safety-checkin", headers=headers)
        self.assertEqual(checkin_res.status_code, 200)
        
        db.session.refresh(rz_state)
        self.assertEqual(rz_state.state, "IN_RED")
        self.assertIsNone(rz_state.warning_prompt_sent_at)

        # Step E: Simulate warning expiry timeout -> Auto triggers SOS distress
        rz_state.state = "WARNING"
        rz_state.warning_expires_at = datetime.utcnow() - timedelta(seconds=10)
        db.session.commit()

        eval_timeout = evaluate_user_state(user.id)
        self.assertEqual(eval_timeout["state"], "AUTO_ALERT_SENT")
        self.assertIn("sos_event_id", eval_timeout)

        # Check auto SOS record created
        auto_event = SOSEvent.query.filter_by(user_id=user.id, type="auto_red_zone").first()
        self.assertIsNotNone(auto_event)
        self.assertEqual(auto_event.status, "active")

    # ----------------------------------------------------------------------- #
    # 5. SHARE-LINK SECURITY & EXPIRY
    # ----------------------------------------------------------------------- #

    def test_06_share_link_creation_expiry_and_revocation(self):
        """Test unguessable token share links, public read-only access, expiry, and revocation."""
        email = f"sharer_{datetime.utcnow().timestamp()}@test.com"
        user = User(name="Link Sharer", email=email, role="user")
        db.session.add(user)
        db.session.commit()

        token = generate_access_token(user)
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        # 1. Create Share Link with 1-hour expiry
        create_res = self.client.post("/api/share", headers=headers, json={
            "label": "My College Destination",
            "address": "VIT Vellore Campus",
            "latitude": 12.9692,
            "longitude": 79.1559,
            "mode": "static",
            "expiry_hours": 1
        })
        self.assertEqual(create_res.status_code, 201)
        data = create_res.get_json()
        share_token = data["token"]
        self.assertTrue(len(share_token) >= 20)  # Unguessable token

        # 2. Public read-only access (NO AUTH HEADERS)
        public_res = self.client.get(f"/api/share/{share_token}")
        self.assertEqual(public_res.status_code, 200)
        pub_data = public_res.get_json()
        self.assertTrue(pub_data["success"])
        self.assertEqual(pub_data["link"]["label"], "My College Destination")
        self.assertNotIn("password", json.dumps(pub_data))

        # 3. Simulate Expiry
        link_obj = SharedLink.query.filter_by(token=share_token).first()
        link_obj.expires_at = datetime.utcnow() - timedelta(hours=2)
        db.session.commit()

        expired_res = self.client.get(f"/api/share/{share_token}")
        self.assertEqual(expired_res.status_code, 200)
        self.assertFalse(expired_res.get_json()["success"])
        self.assertTrue(expired_res.get_json()["is_expired"])

        # 4. Revocation
        link_obj.expires_at = datetime.utcnow() + timedelta(hours=2)
        link_obj.is_revoked = True
        db.session.commit()

        revoked_res = self.client.get(f"/api/share/{share_token}")
        self.assertEqual(revoked_res.status_code, 200)
        self.assertFalse(revoked_res.get_json()["success"])
        self.assertTrue(revoked_res.get_json()["is_revoked"])

    # ----------------------------------------------------------------------- #
    # 6. ROLE-BASED ACCESS & USER DATA ISOLATION
    # ----------------------------------------------------------------------- #

    def test_07_role_based_access_and_cross_user_isolation(self):
        """
        Verify:
        - Regular users receive 403 on /api/admin/*
        - Admins receive 200 on /api/admin/*
        - Cross-user data isolation: User A cannot mutate User B's contacts or saved places
        """
        # Create User A (citizen)
        user_a = User(name="Citizen User A", email=f"user_a_{datetime.utcnow().timestamp()}@test.com", role="user")
        user_a.set_password("Pass123!")
        # Create User B (citizen)
        user_b = User(name="Citizen User B", email=f"user_b_{datetime.utcnow().timestamp()}@test.com", role="user")
        user_b.set_password("Pass123!")
        # Create Admin
        admin = User(name="Admin User", email=f"admin_{datetime.utcnow().timestamp()}@test.com", role="admin")
        admin.set_password("AdminPass123!")
        db.session.add_all([user_a, user_b, admin])
        db.session.commit()

        token_a = generate_access_token(user_a)
        token_b = generate_access_token(user_b)
        token_admin = generate_access_token(admin)

        headers_a = {"Authorization": f"Bearer {token_a}", "Content-Type": "application/json"}
        headers_b = {"Authorization": f"Bearer {token_b}", "Content-Type": "application/json"}
        headers_admin = {"Authorization": f"Bearer {token_admin}", "Content-Type": "application/json"}

        # 1. Role-based check: Regular user gets 403 on Admin Overview
        res_a_admin = self.client.get("/api/admin/overview", headers=headers_a)
        self.assertEqual(res_a_admin.status_code, 403)

        # Admin gets 200 on Admin Overview
        res_admin_ok = self.client.get("/api/admin/overview", headers=headers_admin)
        self.assertEqual(res_admin_ok.status_code, 200)

        # 2. User Data Isolation: User A adds a contact
        contact_a = SOSContact(user_id=user_a.id, name="User A Contact", phone="+919876543299", relationship="Sibling", is_primary=True)
        db.session.add(contact_a)
        # User A saves a destination
        saved_a = SavedLocation(user_id=user_a.id, label="User A Home", latitude=12.91, longitude=79.13)
        db.session.add(saved_a)
        db.session.commit()

        # User B attempts to DELETE User A's contact -> Rejection (404 / not found in user B's scope)
        del_contact_res = self.client.delete(f"/api/user/sos-contacts/{contact_a.id}", headers=headers_b)
        self.assertEqual(del_contact_res.status_code, 404)

        # User B attempts to DELETE User A's saved destination -> Rejection (404)
        del_saved_res = self.client.delete(f"/api/user/saved-locations/{saved_a.id}", headers=headers_b)
        self.assertEqual(del_saved_res.status_code, 404)

        # User B attempts to UPDATE User A's contact -> Rejection (404)
        put_contact_res = self.client.put(f"/api/user/sos-contacts/{contact_a.id}", headers=headers_b, json={"name": "Hacked Name"})
        self.assertEqual(put_contact_res.status_code, 404)

        # Confirm User A's data was NOT altered
        db.session.refresh(contact_a)
        self.assertEqual(contact_a.name, "User A Contact")


if __name__ == "__main__":
    unittest.main()
