"""
Unit and integration tests for Authentication, Citizen Crime Reporting,
and Administrative Incident Triage workflows.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from flask import Flask  # noqa: E402
from database import db  # noqa: E402
from models.crime import Crime  # noqa: E402
from models.user import User  # noqa: E402
from migrations import migrate_crime_schema  # noqa: E402
from routes.auth_routes import auth_bp  # noqa: E402
from routes.user_routes import user_bp  # noqa: E402
from routes.crime_routes import crime_bp  # noqa: E402
from routes.alert_routes import alert_bp  # noqa: E402
from services import auth_service, user_service, crime_service  # noqa: E402
from services.errors import ApiError  # noqa: E402


@pytest.fixture
def app(tmp_path):
    db_path = tmp_path / "test_auth_report.db"
    db_uri = "sqlite:///" + str(db_path)

    test_app = Flask(__name__)
    test_app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    test_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    test_app.config["TESTING"] = True

    db.init_app(test_app)

    test_app.register_blueprint(auth_bp)
    test_app.register_blueprint(user_bp)
    test_app.register_blueprint(crime_bp)
    test_app.register_blueprint(alert_bp)

    @test_app.errorhandler(ApiError)
    def handle_api_error(error):
        from flask import jsonify
        resp = jsonify(error.to_dict())
        resp.status_code = error.status_code
        return resp

    with test_app.app_context():
        db.create_all()
        migrate_crime_schema()
        # Seed an admin user
        admin = auth_service.create_account(
            name="Test Admin",
            email="admin@test.local",
            password="AdminPassword123!",
            role="ADMIN"
        )
        # Seed a normal user
        citizen = auth_service.create_account(
            name="Jane Citizen",
            email="jane@test.local",
            password="CitizenPassword123!",
            role="USER"
        )
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_auth_registration_and_login(client):
    """Verify citizen account registration and login exchange for signed token."""
    # Register new account
    reg_res = client.post("/api/auth/register", json={
        "name": "New User",
        "email": "newuser@test.local",
        "password": "Password123"
    })
    assert reg_res.status_code == 201
    reg_data = reg_res.get_json()
    assert reg_data["success"] is True
    assert "token" in reg_data
    assert reg_data["user"]["role"] == "USER"

    # Login with credentials
    login_res = client.post("/api/auth/login", json={
        "email": "newuser@test.local",
        "password": "Password123"
    })
    assert login_res.status_code == 200
    login_data = login_res.get_json()
    assert login_data["success"] is True
    token = login_data["token"]

    # Access current user profile with token
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.get_json()
    assert me_data["user"]["email"] == "newuser@test.local"


def test_auth_unauthorized_when_no_token(client):
    """Protected endpoints must reject unauthenticated requests with 401."""
    res = client.get("/api/auth/me")
    assert res.status_code == 401
    assert "token" in res.get_json()["message"].lower()


def test_citizen_report_submission_and_personal_tracking(client):
    """Citizen can submit a crime report (PENDING) and track it in my-reports."""
    login_res = client.post("/api/auth/login", json={
        "email": "jane@test.local",
        "password": "CitizenPassword123!"
    })
    token = login_res.get_json()["token"]

    # Submit incident
    report_payload = {
        "crime_type": "Theft",
        "description": "Bicycle stolen near Katpadi junction",
        "location_name": "Katpadi",
        "crime_date": "2026-10-23",
        "severity": "Medium",
        "latitude": 12.9716,
        "longitude": 79.1394
    }
    submit_res = client.post(
        "/api/crimes/report",
        headers={"Authorization": f"Bearer {token}"},
        json=report_payload
    )
    assert submit_res.status_code == 201
    created = submit_res.get_json()["data"]
    assert created["status"] == "PENDING"
    assert created["reported_by_name"] == "Jane Citizen"
    crime_id = created["id"]

    # View personal reports
    my_reports_res = client.get(
        "/api/crimes/my-reports",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert my_reports_res.status_code == 200
    my_reports = my_reports_res.get_json()["data"]
    assert any(r["id"] == crime_id and r["status"] == "PENDING" for r in my_reports)


def test_admin_triage_queue_approve_and_reject(client):
    """Admin reviews pending queue, approves or rejects reports with notes."""
    # Jane submits a report
    j_login = client.post("/api/auth/login", json={
        "email": "jane@test.local",
        "password": "CitizenPassword123!"
    })
    j_token = j_login.get_json()["token"]

    client.post("/api/crimes/report", headers={"Authorization": f"Bearer {j_token}"}, json={
        "crime_type": "Vandalism",
        "description": "Graffiti on station wall",
        "location_name": "Vellore Fort",
        "crime_date": "2026-10-22",
        "severity": "Low",
        "latitude": 12.9165,
        "longitude": 79.1325
    })

    # Admin logs in
    a_login = client.post("/api/auth/login", json={
        "email": "admin@test.local",
        "password": "AdminPassword123!"
    })
    a_token = a_login.get_json()["token"]

    # Admin gets pending queue
    queue_res = client.get(
        "/api/admin/crimes/pending",
        headers={"Authorization": f"Bearer {a_token}"}
    )
    assert queue_res.status_code == 200
    pending_list = queue_res.get_json()["data"]
    assert len(pending_list) >= 1
    pending_crime = pending_list[0]
    p_id = pending_crime["id"]

    # Admin approves
    approve_res = client.patch(
        f"/api/admin/crimes/{p_id}/approve",
        headers={"Authorization": f"Bearer {a_token}"},
        json={"admin_notes": "Verified against police log"}
    )
    assert approve_res.status_code == 200
    approved_data = approve_res.get_json()["data"]
    assert approved_data["status"] == "APPROVED"
    assert approved_data["admin_notes"] == "Verified against police log"
    assert approved_data["reviewed_by_name"] == "Test Admin"


def test_citizen_forbidden_from_admin_actions(client):
    """Citizen must receive 403 Forbidden when attempting administrative actions."""
    j_login = client.post("/api/auth/login", json={
        "email": "jane@test.local",
        "password": "CitizenPassword123!"
    })
    j_token = j_login.get_json()["token"]

    # Attempt to access pending queue
    res = client.get("/api/admin/crimes/pending", headers={"Authorization": f"Bearer {j_token}"})
    assert res.status_code == 403

    # Attempt to list all users
    users_res = client.get("/api/users", headers={"Authorization": f"Bearer {j_token}"})
    assert users_res.status_code == 403


def test_crime_status_filtering(client, app):
    """Filter crimes by status APPROVED vs PENDING vs ALL."""
    with app.app_context():
        # Insert one approved and one pending
        crime_service.create_crime({
            "crime_type": "Robbery",
            "description": "Existing bank record",
            "location_name": "Vellore Center",
            "status": "APPROVED"
        })
        user = user_service.get_user_by_email("jane@test.local")
        crime_service.create_report({
            "crime_type": "Theft",
            "description": "Pending citizen notice",
            "location_name": "Gandhi Nagar",
            "crime_date": "2026-10-23"
        }, user)

    # Filter APPROVED
    app_res = client.get("/api/crimes?status=APPROVED")
    assert app_res.status_code == 200
    assert all(c["status"] == "APPROVED" for c in app_res.get_json()["data"])

    # Filter PENDING
    pen_res = client.get("/api/crimes?status=PENDING")
    assert pen_res.status_code == 200
    assert any(c["status"] == "PENDING" for c in pen_res.get_json()["data"])
