import sqlite3

DB_PATH = r"C:\Users\sruth\crime analysis\backend\instance\crimesense.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

rows = conn.execute("SELECT * FROM crimes").fetchall()
print(f"Total records: {len(rows)}")

with_coords = [r for r in rows if r["latitude"] is not None and r["longitude"] is not None]
print(f"Records with coordinates: {len(with_coords)}")

with_risk = [r for r in rows if r["risk_level"]]
print(f"Records with risk_level: {len(with_risk)}")
risk_counts = {}
for r in rows:
    lvl = r["risk_level"] or "NULL"
    risk_counts[lvl] = risk_counts.get(lvl, 0) + 1
print(f"Risk levels: {risk_counts}")

with_severity = [r for r in rows if r["severity_score"] is not None]
print(f"Records with severity_score: {len(with_severity)}")

with_location_confidence = [r for r in rows if r["location_confidence"]]
print(f"Records with location_confidence: {len(with_location_confidence)}")

loc_conf_counts = {}
for r in rows:
    lc = r["location_confidence"] or "NULL"
    loc_conf_counts[lc] = loc_conf_counts.get(lc, 0) + 1
print(f"Location confidence: {loc_conf_counts}")

with_locality = [r for r in rows if r["locality"]]
with_district = [r for r in rows if r["district"]]
with_desc = [r for r in rows if r["description"]]
print(f"With locality: {len(with_locality)}, district: {len(with_district)}, description: {len(with_desc)}")

print("\n--- Sample record with coords ---")
for r in with_coords[:3]:
    d = dict(r)
    print({k: d[k] for k in ["title","crime_type","locality","district","latitude","longitude","location_confidence","risk_level","severity_score","source","url","published_date"]})

print("\n--- Columns ---")
print([c[0] for c in conn.execute("SELECT * FROM crimes").description])

conn.close()