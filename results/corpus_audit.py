import sqlite3
import json
import math
from collections import Counter, defaultdict

DB_PATH = "backend/instance/crimesense.db"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

rows = cur.execute("SELECT * FROM crimes;").fetchall()
total_records = len(rows)

print(f"Total crime records: {total_records}")

# 1. Coordinate analysis
coord_counts = Counter()
vellore_coords = Counter()
non_vellore_coords = Counter()
district_counts = Counter()
crime_type_counts = Counter()
risk_level_counts = Counter()
severity_scores = []
confidence_counts = Counter()

# Specific coords
CENTROID = (12.9165, 79.1325)

for r in rows:
    lat = r["latitude"]
    lon = r["longitude"]
    distr = r["district"] or "Unknown"
    ctype = r["crime_type"] or "Unknown"
    risk = r["risk_level"] or "Unknown"
    conf = r["location_confidence"] or "Unknown"
    sev = r["severity_score"]
    
    district_counts[distr] += 1
    crime_type_counts[ctype] += 1
    risk_level_counts[risk] += 1
    confidence_counts[conf] += 1
    if sev is not None:
        severity_scores.append(float(sev))
        
    if lat is not None and lon is not None:
        coord = (round(float(lat), 6), round(float(lon), 6))
        coord_counts[coord] += 1
        if distr.lower() == "vellore":
            vellore_coords[coord] += 1
        else:
            non_vellore_coords[coord] += 1

unique_coords = len(coord_counts)
unique_vellore = len(vellore_coords)
unique_non_vellore = len(non_vellore_coords)
centroid_count = coord_counts[CENTROID]
centroid_pct = (centroid_count / total_records) * 100.0

# Count records within 1000m of Centroid
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(min(1.0, max(0.0, a))))

within_1000m = 0
within_1100m = 0
for r in rows:
    if r["latitude"] is not None and r["longitude"] is not None:
        d = haversine(CENTROID[0], CENTROID[1], float(r["latitude"]), float(r["longitude"]))
        if d <= 1000.0:
            within_1000m += 1
        if d <= 1100.0:
            within_1100m += 1

external_district_count = total_records - district_counts["Vellore"]

audit_summary = {
    "total_records": total_records,
    "unique_coordinates": unique_coords,
    "unique_vellore_coordinates": unique_vellore,
    "unique_external_coordinates": unique_non_vellore,
    "centroid_coordinate": CENTROID,
    "centroid_records": centroid_count,
    "centroid_percentage": round(centroid_pct, 4),
    "records_within_1000m_of_centroid": within_1000m,
    "records_within_1100m_of_centroid": within_1100m,
    "vellore_district_records": district_counts["Vellore"],
    "external_district_records": external_district_count,
    "district_breakdown": dict(district_counts),
    "crime_type_breakdown": dict(crime_type_counts),
    "risk_level_breakdown": dict(risk_level_counts),
    "confidence_breakdown": dict(confidence_counts),
    "severity_mean": round(sum(severity_scores)/len(severity_scores), 4) if severity_scores else 0,
    "severity_min": min(severity_scores) if severity_scores else 0,
    "severity_max": max(severity_scores) if severity_scores else 0,
    "top_5_coordinates": [
        {"coord": list(c), "count": cnt, "pct": round(cnt/total_records*100, 2)}
        for c, cnt in coord_counts.most_common(5)
    ]
}

print(json.dumps(audit_summary, indent=2))

with open("results/corpus_audit.json", "w") as f:
    json.dump(audit_summary, f, indent=2)

conn.close()
