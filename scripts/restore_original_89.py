"""
scripts/restore_original_89.py
==============================
Restore the original 89 validated Vellore-region records from the CSV.
These were wiped when --reset was used with the scraper.
"""
import csv
import sqlite3
from pathlib import Path

DB_PATH = r"C:\Users\sruth\crime analysis\backend\instance\crimesense.db"
CSV_PATH = r"C:\Users\sruth\crime analysis\data\final\crimesense_database_import.csv"

# Read original 89 records
with open(CSV_PATH, encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

print(f"Original CSV: {len(rows)} records")
print(f"Columns: {list(rows[0].keys())}")

# Connect to DB
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# Check current state
count = conn.execute("SELECT COUNT(*) FROM crimes").fetchone()[0]
print(f"Current DB records: {count}")

# Import the original 89 records
# The CSV columns are: article_id, title, published_date, source, url, crime_type, description, district, locality, latitude
# We need to map these to the DB columns

imported = 0
for r in rows:
    # Check if already exists
    existing = conn.execute("SELECT id FROM crimes WHERE article_id = ?", (r["article_id"],)).fetchone()
    if existing:
        continue
    
    conn.execute("""
        INSERT INTO crimes (article_id, title, published_date, source, url, crime_type, description, district, locality, latitude)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        r["article_id"],
        r.get("title"),
        r.get("published_date"),
        r.get("source"),
        r.get("url"),
        r.get("crime_type"),
        r.get("description"),
        r.get("district"),
        r.get("locality"),
        r.get("latitude") if r.get("latitude") else None,
    ))
    imported += 1

conn.commit()

count = conn.execute("SELECT COUNT(*) FROM crimes").fetchone()[0]
print(f"Imported: {imported} records")
print(f"Total DB records: {count}")

conn.close()
print("Done")
