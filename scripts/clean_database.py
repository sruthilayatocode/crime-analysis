"""
scripts/clean_database.py
========================
Remove out-of-scope records from the database.
These records are preserved in quarantine CSV files.
Keep only Vellore-region records.
"""
import csv
import sqlite3
from pathlib import Path

DB_PATH = r"C:\Users\sruth\crime analysis\backend\instance\crimesense.db"
PROJECT_ROOT = Path(r"C:\Users\sruth\crime analysis")

# Vellore-region geographic scope
VELLORE_REGION_LOCALITIES = {
    "vellore", "katpadi", "gudiyatham", "gudiyattam", "pernambut",
    "ambur", "vaniyambadi", "tirupattur", "tirupathur", "jolarpet",
    "natrampalli", "ranipet", "walajapet", "arcot", "melvisharam",
    "sholingur", "alangayam", "thuthipattu", "avaniyapuram",
    "kaniyambadi", "pallikonda", "vellore fort", "katpadi railway station",
}
VELLORE_REGION_DISTRICTS = {
    "vellore", "ranipet", "tirupattur", "tirupathur",
}

def normalize(text):
    if not text: return ""
    return text.strip().lower()

def is_vellore_region(locality, district, title, description):
    loc = normalize(locality)
    dist = normalize(district)
    title_lower = normalize(title)
    desc_lower = normalize(description)
    all_text = f"{loc} {title_lower} {desc_lower}"
    
    for dist_name in VELLORE_REGION_DISTRICTS:
        if dist_name in dist:
            return True
    for vloc in VELLORE_REGION_LOCALITIES:
        if vloc in loc:
            return True
    for vloc in VELLORE_REGION_LOCALITIES:
        if vloc in title_lower or vloc in desc_lower:
            return True
    return False

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# Get all records
rows = conn.execute("SELECT * FROM crimes").fetchall()
print(f"Total records: {len(rows)}")

to_keep = []
to_delete = []

for row in rows:
    d = dict(row)
    if is_vellore_region(d.get("locality"), d.get("district"), d.get("title"), d.get("description")):
        to_keep.append(d["id"])
    else:
        to_delete.append(d["id"])

print(f"To keep (Vellore-region): {len(to_keep)}")
print(f"To delete (out-of-scope): {len(to_delete)}")

# Delete out-of-scope records
for id in to_delete:
    conn.execute("DELETE FROM crimes WHERE id = ?", (id,))

conn.commit()

count = conn.execute("SELECT COUNT(*) FROM crimes").fetchone()[0]
print(f"Remaining records: {count}")

conn.close()
print("Done")
