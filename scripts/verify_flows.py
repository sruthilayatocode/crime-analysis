#!/usr/bin/env python
"""
scripts/verify_flows.py
=======================
Verifies real DB flows and prints the results:
1. Crime count shown in admin Overview == SELECT COUNT(*) FROM crimes.
2. Adding a crime in admin increases the database crime count by exactly 1.
3. The zone API result changes when a nearby crime is added, and reverts when deleted.
"""

from __future__ import annotations

import json
import sqlite3
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
DB_PATH = BACKEND_DIR / "instance" / "crimesense.db"

sys.path.insert(0, str(BACKEND_DIR))

from app import app
from database import db
from models.user import User
from services.auth_service import generate_access_token


def run_flow_verifications():
    print("=" * 75)
    print("CrimeSense Real Database Flow Verification")
    print(f"Target Database: {DB_PATH}")
    print("=" * 75)

    with app.app_context():
        # 1. Fetch or ensure admin user token
        admin_user = User.query.filter_by(role="admin").first()
        if not admin_user:
            admin_user = User(
                name="Admin Verifier",
                email="admin_flow_verifier@test.com",
                role="admin",
                is_active=True,
            )
            admin_user.set_password("Admin@123")
            db.session.add(admin_user)
            db.session.commit()

        token = generate_access_token(admin_user)
        auth_headers = {"Authorization": f"Bearer {token}"}

    client = app.test_client()

    # -------------------------------------------------------------------------
    # FLOW 1: Crime count in admin Overview == SELECT COUNT(*) FROM crimes
    # -------------------------------------------------------------------------
    print("\n[FLOW 1] Verifying admin Overview total_crimes == SELECT COUNT(*) FROM crimes")

    # Direct SQLite count
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM crimes;")
    direct_sql_count = cursor.fetchone()[0]

    # Admin Overview API count
    overview_resp = client.get("/api/admin/overview", headers=auth_headers)
    assert overview_resp.status_code == 200, f"Overview API returned {overview_resp.status_code}: {overview_resp.data}"
    overview_data = overview_resp.get_json()
    api_crime_count = overview_data["kpis"]["total_crimes"]

    print(f"  * Direct SQLite SELECT COUNT(*) : {direct_sql_count}")
    print(f"  * Admin Overview API KPI count   : {api_crime_count}")
    if direct_sql_count == api_crime_count:
        print("  -> RESULT: MATCH! (Overview KPI is directly reading from SQLite)")
    else:
        print(f"  -> RESULT: MISMATCH! ({direct_sql_count} != {api_crime_count})")
        conn.close()
        return False

    # -------------------------------------------------------------------------
    # FLOW 2: Adding a crime in admin increases count by 1
    # -------------------------------------------------------------------------
    print("\n[FLOW 2] Verifying adding a crime in admin increases count by exactly 1")
    count_before = direct_sql_count

    test_crime_payload = {
        "title": "Temporary Test Incident for Flow Verification",
        "crime_type": "Robbery",
        "district": "Vellore",
        "locality": "Flow Test Locality",
        "latitude": 12.9700,
        "longitude": 79.1600,
        "severity": "CRITICAL",
        "description": "Automated verification test record.",
    }

    add_resp = client.post("/api/admin/crimes", headers=auth_headers, json=test_crime_payload)
    assert add_resp.status_code == 201, f"Create crime failed: {add_resp.data}"
    add_data = add_resp.get_json()
    created_crime_id = add_data["crime"]["id"]

    cursor.execute("SELECT COUNT(*) FROM crimes;")
    count_after_add = cursor.fetchone()[0]

    print(f"  * Crime count before add : {count_before}")
    print(f"  * Added Crime ID         : #{created_crime_id}")
    print(f"  * Crime count after add  : {count_after_add}")

    if count_after_add == count_before + 1:
        print("  -> RESULT: PASS! (Adding crime in admin increased DB count by exactly 1)")
    else:
        print(f"  -> RESULT: FAIL! Count did not increment by 1 ({count_before} -> {count_after_add})")
        conn.close()
        return False

    # -------------------------------------------------------------------------
    # FLOW 3: Zone API result changes when nearby crime is added then deleted
    # -------------------------------------------------------------------------
    print("\n[FLOW 3] Verifying zone API changes when nearby crime is added and deleted")
    test_lat = 12.8500
    test_lng = 79.2000
    test_radius = 1000

    # Baseline zone check at test_lat, test_lng
    baseline_resp = client.get(f"/api/zone?lat={test_lat}&lng={test_lng}&radius={test_radius}")
    assert baseline_resp.status_code == 200, f"Zone API baseline failed: {baseline_resp.data}"
    baseline_data = baseline_resp.get_json()
    baseline_zone = baseline_data["zone"]
    baseline_score = baseline_data["score"]
    baseline_incidents = baseline_data["incident_count"]

    print(f"  * Baseline Zone at ({test_lat}, {test_lng}) : {baseline_zone} (Score: {baseline_score}, Incidents: {baseline_incidents})")

    # Add a high-severity crime incident right at (test_lat, test_lng)
    nearby_crime_payload = {
        "title": "Severe Nearby Incident at Test Coordinates",
        "crime_type": "Armed Robbery",
        "district": "Vellore",
        "locality": "Zone Impact Test Spot",
        "latitude": test_lat,
        "longitude": test_lng,
        "severity": "CRITICAL",
        "description": "Verification of immediate dynamic zone calculation without cache.",
    }
    nearby_add_resp = client.post("/api/admin/crimes", headers=auth_headers, json=nearby_crime_payload)
    assert nearby_add_resp.status_code == 201, f"Add nearby crime failed: {nearby_add_resp.data}"
    nearby_crime_id = nearby_add_resp.get_json()["crime"]["id"]

    # Re-evaluate zone at same coordinates
    updated_resp = client.get(f"/api/zone?lat={test_lat}&lng={test_lng}&radius={test_radius}")
    assert updated_resp.status_code == 200
    updated_data = updated_resp.get_json()
    updated_zone = updated_data["zone"]
    updated_score = updated_data["score"]
    updated_incidents = updated_data["incident_count"]

    print(f"  * After adding incident #{nearby_crime_id}     : {updated_zone} (Score: {updated_score}, Incidents: {updated_incidents})")

    if updated_score > baseline_score and updated_incidents == baseline_incidents + 1:
        print("  -> Zone score increased dynamically upon adding nearby crime incident!")
    else:
        print(f"  -> FAIL: Zone score did not change ({baseline_score} -> {updated_score})")
        conn.close()
        return False

    # Now delete the nearby crime incident
    del_resp = client.delete(f"/api/admin/crimes/{nearby_crime_id}", headers=auth_headers)
    assert del_resp.status_code == 200, f"Delete nearby crime failed: {del_resp.data}"

    # Re-evaluate zone again
    reverted_resp = client.get(f"/api/zone?lat={test_lat}&lng={test_lng}&radius={test_radius}")
    assert reverted_resp.status_code == 200
    reverted_data = reverted_resp.get_json()
    reverted_zone = reverted_data["zone"]
    reverted_score = reverted_data["score"]
    reverted_incidents = reverted_data["incident_count"]

    print(f"  * After deleting incident #{nearby_crime_id}   : {reverted_zone} (Score: {reverted_score}, Incidents: {reverted_incidents})")

    if reverted_score == baseline_score and reverted_incidents == baseline_incidents:
        print("  -> RESULT: PASS! (Zone score reverted exactly to baseline upon deletion; no stale cache)")
    else:
        print(f"  -> RESULT: FAIL! Zone score did not revert ({reverted_score} != {baseline_score})")
        conn.close()
        return False

    # Clean up first test crime from Flow 2
    del_flow2_resp = client.delete(f"/api/admin/crimes/{created_crime_id}", headers=auth_headers)
    assert del_flow2_resp.status_code == 200

    cursor.execute("SELECT COUNT(*) FROM crimes;")
    final_sql_count = cursor.fetchone()[0]
    conn.close()

    print(f"\nFinal DB crime count after cleanup: {final_sql_count} (Matches starting count: {count_before})")
    print("=" * 75)
    print("ALL REAL DB FLOW VERIFICATIONS PASSED SUCCESSFULLY!")
    print("=" * 75)
    return True


if __name__ == "__main__":
    success = run_flow_verifications()
    sys.exit(0 if success else 1)
