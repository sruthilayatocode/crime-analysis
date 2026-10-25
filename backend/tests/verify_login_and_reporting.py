import time
import urllib.request
import json
import urllib.error
import sys
from pathlib import Path

# Add backend to sys.path for clean up
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

BASE = "http://127.0.0.1:5000"

def request(url, method="GET", data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    encoded_data = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

def main():
    print("--- 1. Admin Login (admin@crimesense.com) ---")
    s, r = request(f"{BASE}/api/auth/login", "POST", {"email": "admin@crimesense.com", "password": "Admin@123"})
    print(f"Status: {s}, Success: {r.get('success')}, Role: {r.get('user', {}).get('role')}")
    assert s == 200, f"Expected 200, got {s}"
    admin_token = r.get("token")

    print("\n--- 2. Demo Citizen Login (user@crimesense.com) ---")
    s, r = request(f"{BASE}/api/auth/login", "POST", {"email": "user@crimesense.com", "password": "User@123"})
    print(f"Status: {s}, Success: {r.get('success')}, Role: {r.get('user', {}).get('role')}")
    assert s == 200, f"Expected 200, got {s}"
    user_token = r.get("token")

    print("\n--- 3. Invalid Password Test ---")
    s, r = request(f"{BASE}/api/auth/login", "POST", {"email": "user@crimesense.com", "password": "WrongPassword!"})
    print(f"Status: {s}, Message: {r.get('message')}")
    assert s == 401, f"Expected 401, got {s}"

    print("\n--- 4. Unknown Email Test ---")
    s, r = request(f"{BASE}/api/auth/login", "POST", {"email": "nonexistent_999@test.com", "password": "User@123"})
    print(f"Status: {s}, Message: {r.get('message')}")
    assert s == 401, f"Expected 401, got {s}"

    print("\n--- 5. New Citizen Registration Test ---")
    new_email = f"citizen_{int(time.time())}@test.com"
    s, r = request(f"{BASE}/api/auth/register", "POST", {"name": "Test Citizen", "email": new_email, "password": "SecurePass123!"})
    print(f"Status: {s}, Success: {r.get('success')}, Registered Email: {r.get('user', {}).get('email')}")
    assert s == 201, f"Expected 201, got {s}"

    print("\n--- 6. Login with Newly Registered Citizen ---")
    s, r = request(f"{BASE}/api/auth/login", "POST", {"email": new_email, "password": "SecurePass123!"})
    print(f"Status: {s}, Success: {r.get('success')}")
    assert s == 200, f"Expected 200, got {s}"
    new_token = r.get("token")

    print("\n--- 7. Submit Citizen Incident Report ---")
    report_payload = {
        "crime_type": "Theft",
        "location_name": "Katpadi, Vellore",
        "description": "Test verification report filed by citizen",
        "crime_date": "2026-10-25 13:00:00",
        "latitude": 12.969484,
        "longitude": 79.156887,
        "severity": "Medium"
    }
    s, r = request(f"{BASE}/api/crimes/report", "POST", report_payload, token=new_token)
    report_data = r.get("data") or r.get("report", {})
    report_id = report_data.get("id")
    print(f"Status: {s}, Success: {r.get('success')}, Report ID: {report_id}, Report Status: {report_data.get('status')}")
    assert s in (200, 201), f"Expected 200 or 201, got {s}"

    print("\n--- 8. Citizen Tracks Own Submitted Reports ---")
    s, r = request(f"{BASE}/api/crimes/my-reports", "GET", token=new_token)
    reports = r if isinstance(r, list) else r.get("data") or r.get("reports", [])
    found_in_my_reports = any(x.get("id") == report_id for x in reports)
    print(f"Status: {s}, Total Own Reports: {len(reports)}, Found Report {report_id}: {found_in_my_reports}")
    assert found_in_my_reports, "Submitted report not found in citizen's personal report list"

    print("\n--- 9. Admin Inspects Pending Triage Queue ---")
    s, r = request(f"{BASE}/api/admin/crimes/pending", "GET", token=admin_token)
    pending = r.get("pending_crimes", []) if isinstance(r, dict) else r
    found_in_pending = any(x.get("id") == report_id for x in pending)
    print(f"Status: {s}, Total Pending Reports: {len(pending)}, Found Report {report_id}: {found_in_pending}")
    assert found_in_pending, "Submitted report not found in admin pending triage queue"

    print("\n--- 10. Admin Approves Pending Report ---")
    s, r = request(f"{BASE}/api/admin/crimes/{report_id}/approve", "POST", {"admin_notes": "Verified incident"}, token=admin_token)
    approved_status = r.get("status") or (r.get("data", {}) if isinstance(r.get("data"), dict) else {}).get("status")
    print(f"Status: {s}, Updated Status: {approved_status}")
    assert s == 200, f"Expected 200, got {s}"

    print("\n--- 11. Role Separation: Citizen blocked from Admin Triage ---")
    s, r = request(f"{BASE}/api/admin/crimes/pending", "GET", token=new_token)
    print(f"Status: {s} (Expected 403 Forbidden)")
    assert s == 403, f"Expected 403, got {s}"

    # Clean up test-created records to preserve exact database baseline
    from app import app
    from database import db
    from models.crime import Crime
    from models.user import User

    with app.app_context():
        if report_id:
            c = Crime.query.get(report_id)
            if c:
                db.session.delete(c)
        u = User.query.filter_by(email=new_email).first()
        if u:
            db.session.delete(u)
        db.session.commit()
    print("\n--- Cleaned up temporary test-owned records safely. Database pristine! ---")
    print("\n=== ALL AUTHENTICATION AND REPORTING CHECKS PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    main()
