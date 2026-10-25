"""
End-to-end verification script for Phase 1 fixes.
Tests live against backend/app.py test_client.
"""
import sys
from pathlib import Path

# Add backend and root
_BACKEND = Path(__file__).resolve().parent.parent
_ROOT = _BACKEND.parent
sys.path.insert(0, str(_BACKEND))
sys.path.insert(0, str(_ROOT))

from app import app
from database import db
from models.crime import Crime
from models.user import User

def run_e2e_verification():
    print("=" * 70)
    print("CRIMESENSE PHASE 1 — END-TO-END VERIFICATION")
    print("=" * 70)

    client = app.test_client()

    with app.app_context():
        initial_crimes_count = Crime.query.count()
        print(f"[DB Check] Initial Crime Records: {initial_crimes_count}")
        assert initial_crimes_count >= 685, f"Expected at least 685 records, found {initial_crimes_count}"

        # 1. Verify /api/system/info
        res_sys = client.get("/api/system/info")
        print(f"1. GET /api/system/info -> Status: {res_sys.status_code}")
        assert res_sys.status_code == 200
        assert res_sys.get_json()["success"] is True

        # 2. Verify /api/ml/hotspots
        res_ml = client.post("/api/ml/hotspots", json={"eps_km": 1.0, "min_samples": 3})
        print(f"2. POST /api/ml/hotspots -> Status: {res_ml.status_code}, Clusters: {len(res_ml.get_json().get('hotspots', []))}")
        assert res_ml.status_code == 200

        # 3. Verify Unauthenticated 401 on protected endpoint
        res_unauth = client.get("/api/admin/crimes/pending")
        print(f"3. GET /api/admin/crimes/pending (Unauth) -> Status: {res_unauth.status_code}, Response: {res_unauth.get_json()}")
        assert res_unauth.status_code == 401
        assert res_unauth.get_json()["success"] is False

        # 4. Verify Admin Overview with uppercase ADMIN role
        admin = User.query.filter(User.role.ilike("admin")).first()
        from services.auth_service import generate_access_token
        admin_token = generate_access_token(admin)
        res_admin_overview = client.get("/api/admin/overview", headers={"Authorization": f"Bearer {admin_token}"})
        print(f"4. GET /api/admin/overview (Admin role={admin.role}) -> Status: {res_admin_overview.status_code}")
        assert res_admin_overview.status_code == 200

        # 5. Citizen Registration, Login, Report Submission, and Tracking
        import uuid
        test_email = f"citizen_e2e_{uuid.uuid4().hex[:6]}@test.com"
        reg_res = client.post("/api/auth/register", json={
            "name": "Audit Citizen",
            "email": test_email,
            "password": "CitizenPassword@123"
        })
        print(f"5. Citizen Registration -> Status: {reg_res.status_code}")
        assert reg_res.status_code == 201
        citizen_token = reg_res.get_json()["token"]
        citizen_user = User.query.filter_by(email=test_email).first()

        # Submit citizen report
        report_payload = {
            "crime_type": "Theft",
            "location_name": "Test Locality, Katpadi",
            "latitude": 12.9806,
            "longitude": 79.1368,
            "crime_date": "2026-10-25 10:00:00",
            "severity": "Medium",
            "description": "Bicycle stolen outside building lobby."
        }
        rep_res = client.post(
            "/api/crimes/report",
            headers={"Authorization": f"Bearer {citizen_token}"},
            json=report_payload
        )
        print(f"6. Citizen Report Submission -> Status: {rep_res.status_code}")
        assert rep_res.status_code == 201
        created_crime = rep_res.get_json()["data"]
        crime_id = created_crime["id"]
        assert created_crime["status"] == "PENDING"
        assert created_crime["reported_by_id"] == citizen_user.id

        # Citizen tracks my-reports
        my_rep_res = client.get("/api/crimes/my-reports", headers={"Authorization": f"Bearer {citizen_token}"})
        print(f"7. Citizen Report Tracking -> Status: {my_rep_res.status_code}, Count: {my_rep_res.get_json().get('count')}")
        assert my_rep_res.status_code == 200
        assert any(c["id"] == crime_id for c in my_rep_res.get_json()["data"])

        # 8. Admin reviews pending queue
        pending_res = client.get("/api/admin/crimes/pending", headers={"Authorization": f"Bearer {admin_token}"})
        print(f"8. Admin Pending Queue -> Status: {pending_res.status_code}, Found report #{crime_id}: {any(c['id'] == crime_id for c in pending_res.get_json()['data'])}")
        assert pending_res.status_code == 200
        assert any(c["id"] == crime_id for c in pending_res.get_json()["data"])

        # 9. Admin approves the report
        app_res = client.patch(
            f"/api/admin/crimes/{crime_id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"admin_notes": "Verified by Station Officer"}
        )
        print(f"9. Admin Approve Report -> Status: {app_res.status_code}")
        assert app_res.status_code == 200
        app_data = app_res.get_json()["data"]
        assert app_data["status"] == "APPROVED"
        assert app_data["admin_notes"] == "Verified by Station Officer"
        assert app_data["reviewed_by_id"] == admin.id

        # 10. Clean up only the test citizen and test crime record to preserve pristine database
        db.session.delete(Crime.query.get(crime_id))
        db.session.delete(citizen_user)
        db.session.commit()

        final_count = Crime.query.count()
        print(f"[DB Check] Final Crime Records: {final_count} (Preserved exactly {initial_crimes_count})")
        assert final_count == initial_crimes_count, f"Expected {initial_crimes_count}, found {final_count}"

    print("=" * 70)
    print("ALL PHASE 1 END-TO-END AUDIT CHECKS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_e2e_verification()
