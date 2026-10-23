import sqlite3
import json
import csv
from pathlib import Path

DB_PATH = r"C:\Users\sruth\crime analysis\backend\instance\crimesense.db"
DATA_ROOT = Path(r"C:\Users\sruth\crime analysis\data")

# 1. Database state
conn = sqlite3.connect(DB_PATH)
db_count = conn.execute("SELECT COUNT(*) FROM crimes").fetchone()[0]
print(f"Database records: {db_count}")

# Check if original 89 are present
orig_count = conn.execute("SELECT COUNT(*) FROM crimes WHERE district = 'Vellore'").fetchone()[0]
print(f"Records with district='Vellore': {orig_count}")
conn.close()

# 2. Final CSV
final_csv = DATA_ROOT / "final" / "crimesense_database_import.csv"
with open(final_csv, encoding="utf-8-sig") as f:
    final_records = list(csv.DictReader(f))
print(f"\nFinal CSV: {len(final_records)} records")

# 3. Collected candidates
candidates_json = DATA_ROOT / "raw" / "collected_sources" / "collected_candidates.json"
if candidates_json.exists():
    candidates = json.loads(candidates_json.read_text(encoding="utf-8"))
    print(f"Collected candidates: {len(candidates)} records")
else:
    print("Collected candidates: file not found")

# 4. Seen URLs
seen_json = DATA_ROOT / "raw" / "collected_sources" / "collection_state_seen_urls.json"
if seen_json.exists():
    seen = json.loads(seen_json.read_text(encoding="utf-8"))
    print(f"Seen URLs: {len(seen)}")
else:
    print("Seen URLs: file not found")

# 5. Accepted incidents
accepted_json = DATA_ROOT / "processed" / "accepted_incidents.json"
if accepted_json.exists():
    accepted = json.loads(accepted_json.read_text(encoding="utf-8"))
    print(f"Accepted incidents: {len(accepted)} records")
else:
    print("Accepted incidents: file not found")

# 6. Batches
batch_dir = DATA_ROOT / "raw" / "collected_sources" / "batches"
if batch_dir.exists():
    batches = list(batch_dir.glob("*.json"))
    print(f"Batch files: {len(batches)}")
else:
    print("Batch directory: not found")

# 7. Researcher URLs
researcher_urls = DATA_ROOT / "raw" / "collected_sources" / "researcher_urls.txt"
if researcher_urls.exists():
    urls = [l for l in researcher_urls.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    print(f"Researcher URLs: {len(urls)}")
else:
    print("Researcher URLs: file not found")

# 8. Source registry
source_registry = DATA_ROOT / "raw" / "collected_sources" / "SOURCE_REGISTRY.md"
if source_registry.exists():
    print(f"\nSource registry exists: {source_registry}")
    print(source_registry.read_text(encoding="utf-8")[:2000])
