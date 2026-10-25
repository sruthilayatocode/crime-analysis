"""One-off state audit: count records across DB + all data files."""
import csv, json, sqlite3, os
from pathlib import Path

ROOT = Path(r"C:\Users\sruth\crime analysis")
DB = ROOT / "backend/instance/crimesense.db"

def csv_rows(p):
    with open(p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

files = {
    "FINAL canonical (89)": ROOT / "data/final/crimesense_database_import.csv",
    "FINAL expanded": ROOT / "data/final/crimesense_database_import_expanded.csv",
    "FINAL combined_92": ROOT / "data/final/crimesense_dataset_combined_92.csv",
    "RAW collected_incidents (ledger, ~95?)": ROOT / "data/raw/collected_incidents.csv",
    "PROCESSED expanded_candidates": ROOT / "data/processed/crimesense_expanded_candidates.csv",
}
print("=== FILE ROW COUNTS ===")
for label, p in files.items():
    if p.exists():
        rows = csv_rows(p)
        # try to count Vellore-only (district contains vellore)
        vellore = sum(1 for r in rows if "vellore" in (r.get("district") or "").lower())
        print(f"{label}: {len(rows)} rows | Vellore(district)= {vellore} | cols={list(rows[0].keys()) if rows else []}")
    else:
        print(f"{label}: MISSING")

print("\n=== JSON COUNTS ===")
for label, p in [
    ("PROCESSED accepted_incidents", ROOT / "data/processed/accepted_incidents.json"),
    ("RAW collected_candidates", ROOT / "data/raw/collected_sources/collected_candidates.json"),
    ("RAW batches/batch_collected", ROOT / "data/raw/collected_sources/batches/batch_collected.json"),
]:
    if p.exists():
        j = json.loads(p.read_text(encoding="utf-8"))
        print(f"{label}: {len(j)} records")
    else:
        print(f"{label}: MISSING")

print("\n=== DATABASE ===")
if DB.exists():
    con = sqlite3.connect(str(DB))
    con.row_factory = sqlite3.Row
    tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print("Tables:", tables)
    for tn in tables:
        n = con.execute(f"SELECT COUNT(*) FROM [{tn}]").fetchone()[0]
        cols = [c[1] for c in con.execute(f"PRAGMA table_info([{tn}])").fetchall()]
        print(f"  [{tn}]: {n} rows, cols={cols}")
        if tn == "crimes" and n:
            for row in con.execute("SELECT district, locality, COUNT(*) c FROM crimes GROUP BY district, locality ORDER BY c DESC LIMIT 40").fetchall():
                print(f"     {row['district'] or '-'} | {row['locality'] or '-'} | {row['c']}")
    con.close()
else:
    print("DB not found at", DB)
