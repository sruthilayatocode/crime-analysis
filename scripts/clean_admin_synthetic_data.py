"""
scripts/clean_admin_synthetic_data.py
=====================================
Purge all synthetic, mock, and test records associated with the Admin pages
from both backend/instance/crimesense.db and database/crime_analysis.db.
"""

import sqlite3
import os
from pathlib import Path

ROOT = Path(r"c:\Users\sruth\crime analysis")
DB_PATHS = [
    ROOT / "backend" / "instance" / "crimesense.db",
    ROOT / "database" / "crime_analysis.db"
]

def clean_database(db_path: Path):
    if not db_path.exists():
        print(f"[Skip] {db_path} does not exist.")
        return

    print(f"\n--- Cleaning {db_path} ---")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # 1. Remove synthetic test users (e.g. Test Resident)
    c.execute("SELECT id, name, email FROM users WHERE LOWER(email) LIKE '%test%' OR LOWER(name) LIKE '%test%'")
    test_users = c.fetchall()
    test_user_ids = [u[0] for u in test_users]
    print(f"Found {len(test_users)} test users to delete: {test_users}")

    if test_user_ids:
        placeholders = ",".join("?" for _ in test_user_ids)
        c.execute(f"DELETE FROM sos_contacts WHERE user_id IN ({placeholders})", test_user_ids)
        c.execute(f"DELETE FROM user_settings WHERE user_id IN ({placeholders})", test_user_ids)
        c.execute(f"DELETE FROM user_locations WHERE user_id IN ({placeholders})", test_user_ids)
        c.execute(f"DELETE FROM user_red_zone_states WHERE user_id IN ({placeholders})", test_user_ids)
        c.execute(f"DELETE FROM sos_events WHERE user_id IN ({placeholders})", test_user_ids)
        c.execute(f"DELETE FROM users WHERE id IN ({placeholders})", test_user_ids)

    # 2. Delete synthetic/mock SOS events created during testing
    c.execute("DELETE FROM sos_events")
    print("Cleared synthetic/test SOS events (table now clean).")

    # 3. Delete synthetic SOS contacts with fake dummy numbers (+919876543210 etc)
    c.execute("DELETE FROM sos_contacts WHERE phone = '+919876543210' OR user_id NOT IN (SELECT id FROM users)")
    print("Cleared dummy/orphan SOS contacts.")

    # 4. Clean orphan user locations & red zone states
    c.execute("DELETE FROM user_red_zone_states WHERE user_id NOT IN (SELECT id FROM users)")
    c.execute("DELETE FROM user_locations WHERE user_id NOT IN (SELECT id FROM users)")

    # 5. Clean test audit logs
    c.execute("""
        DELETE FROM audit_logs 
        WHERE details LIKE '%Test Locality%' 
           OR details LIKE '%Test Spot%' 
           OR target_entity LIKE '%Test%'
    """)
    print("Cleaned test incident audit logs.")

    # 6. Verify remaining users and records
    c.execute("SELECT id, name, email, role FROM users")
    remaining_users = c.fetchall()
    print(f"Active real users ({len(remaining_users)}): {remaining_users}")

    c.execute("SELECT COUNT(*) FROM crimes")
    total_crimes = c.fetchone()[0]
    print(f"Total authentic crime records: {total_crimes}")

    c.execute("SELECT COUNT(*) FROM sos_events")
    total_sos = c.fetchone()[0]
    print(f"Active/historical SOS events: {total_sos}")

    conn.commit()
    conn.close()
    print(f"[Done] Cleaned {db_path.name}")

if __name__ == "__main__":
    for p in DB_PATHS:
        clean_database(p)
