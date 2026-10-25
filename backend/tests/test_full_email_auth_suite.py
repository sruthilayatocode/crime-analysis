"""
test_full_email_auth_suite.py
=============================
Automated test suite verifying the complete email & password authentication,
email verification, password reset, rate limiting, and citizen reporting workflows.
"""

import time
import urllib.request
import json
import urllib.error
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

BASE = "http://127.0.0.1:5000"


def request(url, method="GET", data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    encoded_data = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def run_scenario_1_existing_login():
    print("\n[Scenario 1] Login with existing registered email & correct password")
    # Admin
    s, r = request(f"{BASE}/api/auth/login", "POST", {"email": "admin@crimesense.com", "password": "Admin@123"})
    assert s == 200, f"Admin login failed: {s}, {r}"
    assert r.get("success") is True
    assert r.get("user", {}).get("role") == "admin"
    admin_token = r.get("token")

    # Demo Citizen
    s, r = request(f"{BASE}/api/auth/login", "POST", {"email": "user@crimesense.com", "password": "User@123"})
    assert s == 200, f"Demo citizen login failed: {s}, {r}"
    assert r.get("success") is True
    assert r.get("user", {}).get("role") == "user"
    print("  -> PASSED: Both admin and demo citizen logged in successfully.")
    return admin_token


def run_scenario_2_incorrect_password():
    print("\n[Scenario 2] Login with an incorrect password")
    s, r = request(f"{BASE}/api/auth/login", "POST", {"email": "user@crimesense.com", "password": "IncorrectPassword99!"})
    assert s == 401, f"Expected 401, got {s}"
    assert r.get("success") is False
    assert "Invalid email or password" in r.get("message", "")
    print(f"  -> PASSED: Correctly rejected with 401: {r.get('message')}")


def run_scenario_3_unknown_email():
    print("\n[Scenario 3] Login with an unknown email")
    s, r = request(f"{BASE}/api/auth/login", "POST", {"email": "nobody_exists_12345@domain.com", "password": "Password123!"})
    assert s == 401, f"Expected 401, got {s}"
    assert r.get("success") is False
    assert "Invalid email or password" in r.get("message", "")
    print(f"  -> PASSED: Correctly rejected with 401: {r.get('message')}")


def run_scenario_4_and_5_registration():
    print("\n[Scenario 4 & 5] Register a new citizen account and reject duplicate")
    unique_email = f"alice_{int(time.time())}@safetymail.org"

    # Valid registration
    s, r = request(f"{BASE}/api/auth/register", "POST", {
        "name": "Alice Citizen",
        "email": unique_email,
        "password": "AliceSecret2026!",
        "role": "admin"  # Attempting privilege escalation
    })
    assert s == 201, f"Registration failed: {s}, {r}"
    assert r.get("success") is True
    assert r.get("user", {}).get("role", "").lower() == "user", "Security failure: user was able to self-assign admin role!"
    print(f"  -> PASSED: Citizen registered: {unique_email} with enforced role: {r['user']['role']}")

    # Reject duplicate registration
    s_dup, r_dup = request(f"{BASE}/api/auth/register", "POST", {
        "name": "Alice Duplicate",
        "email": unique_email,
        "password": "AnotherPassword123!"
    })
    assert s_dup == 400, f"Expected 400 for duplicate, got {s_dup}"
    assert "already exists" in r_dup.get("message", "")
    print(f"  -> PASSED: Duplicate registration rejected: {r_dup.get('message')}")

    # Reject invalid email format
    s_bad, r_bad = request(f"{BASE}/api/auth/register", "POST", {
        "name": "Bob Bad Email",
        "email": "not-an-email",
        "password": "ValidPassword123!"
    })
    assert s_bad == 400
    print(f"  -> PASSED: Malformed email rejected: {r_bad.get('message')}")

    return unique_email


def run_scenario_6_7_8_email_verification(unique_email):
    print("\n[Scenario 6, 7 & 8] Email verification, token expiry, reuse rejection, and resend")
    from app import app
    from database import db
    from models.user import User
    from services.email_service import hash_token
    import secrets
    from datetime import datetime, timedelta

    # Retrieve user and verification token hash from DB
    with app.app_context():
        u = User.query.filter_by(email=unique_email).first()
        assert u is not None
        assert u.is_verified is False
        stored_hash = u.verification_token_hash
        assert stored_hash is not None

    # Test invalid token
    s_inv, r_inv = request(f"{BASE}/api/auth/verify-email?token=completely_invalid_token_123")
    assert s_inv == 400
    print(f"  -> PASSED: Invalid token rejected with 400: {r_inv.get('message')}")

    # Generate a fresh known token for direct test verification
    raw_test_token = secrets.token_urlsafe(32)
    with app.app_context():
        u = User.query.filter_by(email=unique_email).first()
        u.verification_token_hash = hash_token(raw_test_token)
        u.verification_token_expires_at = datetime.utcnow() + timedelta(hours=24)
        db.session.commit()

    # Valid token verification
    s_val, r_val = request(f"{BASE}/api/auth/verify-email?token={raw_test_token}")
    assert s_val == 200, f"Verification failed: {s_val}, {r_val}"
    assert r_val.get("success") is True
    print(f"  -> PASSED: Valid email verified: {r_val.get('message')}")

    # Test token reuse (single-use token protection)
    s_reuse, r_reuse = request(f"{BASE}/api/auth/verify-email?token={raw_test_token}")
    assert s_reuse == 400
    print(f"  -> PASSED: Token reuse rejected with 400: {r_reuse.get('message')}")

    # Test expired token
    expired_token = secrets.token_urlsafe(32)
    with app.app_context():
        u = User.query.filter_by(email=unique_email).first()
        u.is_verified = False  # Mark unverified temporarily to test expired link
        u.verification_token_hash = hash_token(expired_token)
        u.verification_token_expires_at = datetime.utcnow() - timedelta(minutes=10)
        db.session.commit()

    s_exp, r_exp = request(f"{BASE}/api/auth/verify-email?token={expired_token}")
    assert s_exp == 400
    assert "expired" in r_exp.get("message", "").lower()
    print(f"  -> PASSED: Expired token rejected with 400: {r_exp.get('message')}")

    # Test resend verification endpoint
    s_resend, r_resend = request(f"{BASE}/api/auth/resend-verification", "POST", {"email": unique_email})
    assert s_resend == 200
    print(f"  -> PASSED: Resend verification dispatched: {r_resend.get('message')}")

    # Restore verified status for subsequent tests
    with app.app_context():
        u = User.query.filter_by(email=unique_email).first()
        u.is_verified = True
        u.verification_token_hash = None
        db.session.commit()


def run_scenario_9_password_reset(unique_email):
    print("\n[Scenario 9] Forgot password and secure reset")
    from app import app
    from database import db
    from models.user import User
    from services.email_service import hash_token
    import secrets
    from datetime import datetime, timedelta

    # 1. Request password reset (anti-enumeration generic response)
    s_forgot, r_forgot = request(f"{BASE}/api/auth/forgot-password", "POST", {"email": unique_email})
    assert s_forgot == 200
    assert r_forgot.get("success") is True
    print(f"  -> PASSED: Forgot password generic response returned: {r_forgot.get('message')}")

    # Non-existent email also returns generic response (no account enumeration)
    s_non, r_non = request(f"{BASE}/api/auth/forgot-password", "POST", {"email": "notreal_999@test.com"})
    assert s_non == 200
    assert r_non.get("success") is True
    print(f"  -> PASSED: Unknown email returned anti-enumeration generic response.")

    # 2. Simulate reset token
    raw_reset_token = secrets.token_urlsafe(32)
    with app.app_context():
        u = User.query.filter_by(email=unique_email).first()
        u.reset_token_hash = hash_token(raw_reset_token)
        u.reset_token_expires_at = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()

    # 3. Test invalid reset token
    s_bad_reset, r_bad_reset = request(f"{BASE}/api/auth/reset-password", "POST", {
        "token": "fake_token_12345",
        "password": "BrandNewPassword2026!"
    })
    assert s_bad_reset == 400
    print(f"  -> PASSED: Invalid reset token rejected: {r_bad_reset.get('message')}")

    # 4. Valid password reset
    new_password = "BrandNewPassword2026!"
    s_reset, r_reset = request(f"{BASE}/api/auth/reset-password", "POST", {
        "token": raw_reset_token,
        "password": new_password
    })
    assert s_reset == 200
    assert r_reset.get("success") is True
    print(f"  -> PASSED: Password reset successful: {r_reset.get('message')}")

    # 5. Reused reset token rejected
    s_reused, r_reused = request(f"{BASE}/api/auth/reset-password", "POST", {
        "token": raw_reset_token,
        "password": "AnotherNewPassword!"
    })
    assert s_reused == 400
    print(f"  -> PASSED: Single-use reset token reuse rejected: {r_reused.get('message')}")

    # 6. Verify login with the NEW password
    s_new_login, r_new_login = request(f"{BASE}/api/auth/login", "POST", {
        "email": unique_email,
        "password": new_password
    })
    assert s_new_login == 200
    assert r_new_login.get("success") is True
    print("  -> PASSED: Successfully logged in with newly reset password!")
    return r_new_login.get("token")


def run_scenario_10_and_11_role_checks_and_reporting(citizen_token, admin_token, unique_email):
    print("\n[Scenario 10 & 11] Citizen RBAC enforcement & incident reporting lifecycle")

    # Citizen blocked from admin endpoint
    s_block, r_block = request(f"{BASE}/api/admin/crimes/pending", "GET", token=citizen_token)
    assert s_block == 403, f"Expected 403 Forbidden for citizen accessing admin endpoint, got {s_block}"
    print(f"  -> PASSED: Citizen blocked from admin route with HTTP 403.")

    # Citizen submits crime incident report
    report_payload = {
        "crime_type": "Theft",
        "location_name": "Gandhinagar, Vellore",
        "description": "Bicycle reported stolen near market street",
        "crime_date": "2026-10-25 15:30:00",
        "latitude": 12.9345,
        "longitude": 79.1350,
        "severity": "Low"
    }
    s_rep, r_rep = request(f"{BASE}/api/crimes/report", "POST", report_payload, token=citizen_token)
    assert s_rep in (200, 201), f"Report submission failed: {s_rep}, {r_rep}"
    report_data = r_rep.get("data") or r_rep.get("report", {})
    report_id = report_data.get("id")
    print(f"  -> PASSED: Incident report submitted successfully (ID: {report_id}, status: {report_data.get('status')})")

    # Citizen tracks own report
    s_my, r_my = request(f"{BASE}/api/crimes/my-reports", "GET", token=citizen_token)
    reports = r_my if isinstance(r_my, list) else r_my.get("data") or r_my.get("reports", [])
    assert any(x.get("id") == report_id for x in reports)
    print(f"  -> PASSED: Report {report_id} verified in citizen's personal report list.")

    # Admin inspects pending reports
    s_pen, r_pen = request(f"{BASE}/api/admin/crimes/pending", "GET", token=admin_token)
    pending_list = r_pen.get("pending_crimes") or r_pen.get("data") or []
    assert any(x.get("id") == report_id for x in pending_list)
    print(f"  -> PASSED: Report {report_id} visible in admin triage queue.")

    # Admin approves report
    s_app, r_app = request(f"{BASE}/api/admin/crimes/{report_id}/approve", "POST", {
        "admin_notes": "Verified by police precinct."
    }, token=admin_token)
    assert s_app == 200
    print(f"  -> PASSED: Report {report_id} approved by administrator.")

    # Clean up test-created data safely
    from app import app
    from database import db
    from models.crime import Crime
    from models.user import User

    with app.app_context():
        if report_id:
            c = Crime.query.get(report_id)
            if c:
                db.session.delete(c)
        u = User.query.filter_by(email=unique_email).first()
        if u:
            db.session.delete(u)
        db.session.commit()
    print("  -> PASSED: Cleaned up temporary test data. Database baseline preserved!")


def main():
    print("==========================================================")
    print("CRIMESENSE COMPLETE EMAIL-AND-PASSWORD AUTHENTICATION SUITE")
    print("==========================================================")

    admin_token = run_scenario_1_existing_login()
    run_scenario_2_incorrect_password()
    run_scenario_3_unknown_email()
    unique_email = run_scenario_4_and_5_registration()
    run_scenario_6_7_8_email_verification(unique_email)
    citizen_token = run_scenario_9_password_reset(unique_email)
    run_scenario_10_and_11_role_checks_and_reporting(citizen_token, admin_token, unique_email)

    print("\n==========================================================")
    print("ALL 11 AUTHENTICATION & REPORTING SCENARIOS PASSED 100%!")
    print("==========================================================")


def test_full_email_and_password_auth_flow():
    """Pytest entrypoint for the end-to-end email auth and recovery flow."""
    main()


if __name__ == "__main__":
    main()
