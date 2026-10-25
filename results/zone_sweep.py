import sqlite3
import math
import json
import csv
import numpy as np
from datetime import datetime, timezone

DB_PATH = "backend/instance/crimesense.db"
CENTROID = (12.9165, 79.1325)
EARTH_RADIUS = 6371000.0

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
crimes_db = cur.execute("SELECT * FROM crimes;").fetchall()
conn.close()

# Prepare crime list
crimes = []
fixed_now = datetime(2026, 10, 21, 0, 0, 0, tzinfo=timezone.utc)

def parse_date(d_str):
    if not d_str:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(str(d_str).strip()[:19], fmt).replace(tzinfo=timezone.utc)
        except Exception:
            pass
    return None

def recency_weight(dt):
    if not dt:
        return 0.4
    days = (fixed_now - dt).total_seconds() / 86400.0
    if days <= 182.5:
        return 1.0
    elif days <= 730.0:
        return 0.7
    else:
        return 0.4

def haversine(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * EARTH_RADIUS * math.asin(math.sqrt(min(1.0, max(0.0, a))))

for r in crimes_db:
    if r["latitude"] is not None and r["longitude"] is not None:
        dt = parse_date(r["published_date"]) or parse_date(r["crime_date"])
        crimes.append({
            "id": r["id"],
            "lat": float(r["latitude"]),
            "lon": float(r["longitude"]),
            "severity": float(r["severity_score"]) if r["severity_score"] is not None else 5.0,
            "weight": recency_weight(dt),
            "date": dt,
            "district": r["district"] or "Unknown",
            "locality": r["locality"] or "Unknown",
            "confidence": r["location_confidence"] or "Unknown"
        })

print(f"Loaded {len(crimes)} valid geocoded incidents.")

def compute_raw_risk(q_lat, q_lon, radius=1000.0, incident_list=crimes):
    raw_risk = 0.0
    count = 0
    for c in incident_list:
        d = haversine(q_lat, q_lon, c["lat"], c["lon"])
        if d <= radius:
            delta_d = 1.0 - (d / radius)
            raw_risk += c["severity"] * delta_d * c["weight"]
            count += 1
    return raw_risk, count

# 1. Radial sweep along North direction from Centroid (0 to 2000m)
# 1 degree lat ~ 111,139 meters
meters_per_deg_lat = 111139.0
distances_m = [0, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950, 990, 1000, 1010, 1050, 1100, 1250, 1500, 1750, 2000]

radial_results = []
for d in distances_m:
    # move North by d meters
    q_lat = CENTROID[0] + (d / meters_per_deg_lat)
    q_lon = CENTROID[1]
    raw_r, cnt = compute_raw_risk(q_lat, q_lon, 1000.0)
    
    z_100 = min(100.0, 100.0 * raw_r / 100.0)
    z_500 = min(100.0, 100.0 * raw_r / 500.0)
    z_1000 = min(100.0, 100.0 * raw_r / 1000.0)
    z_2500 = min(100.0, 100.0 * raw_r / 2500.0)
    z_5000 = min(100.0, 100.0 * raw_r / 5000.0)
    
    radial_results.append({
        "distance_m": d,
        "raw_risk": round(raw_r, 4),
        "incident_count": cnt,
        "Z_R100": round(z_100, 2),
        "Z_R500": round(z_500, 2),
        "Z_R1000": round(z_1000, 2),
        "Z_R2500": round(z_2500, 2),
        "Z_R5000": round(z_5000, 2),
    })

# Write CSV
with open("results/radial_zone_sweep.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(radial_results[0].keys()))
    writer.writeheader()
    writer.writerows(radial_results)

# 2. Sensitivity Sweep across R_ref values
r_ref_values = [100, 500, 1000, 2500, 5000]

# Generate spatial grid across Vellore urban area
# 12.87 to 12.98 N, 79.08 to 79.18 E
grid_lats = np.linspace(12.87, 12.98, 25)
grid_lons = np.linspace(79.08, 79.18, 25)
grid_points = [(lat, lon) for lat in grid_lats for lon in grid_lons]

grid_raw_risks = []
for glat, glon in grid_points:
    rr, _ = compute_raw_risk(glat, glon, 1000.0)
    grid_raw_risks.append(rr)

grid_raw_risks = np.array(grid_raw_risks)
p50 = float(np.percentile(grid_raw_risks, 50))
p75 = float(np.percentile(grid_raw_risks, 75))
p90 = float(np.percentile(grid_raw_risks, 90))
p95 = float(np.percentile(grid_raw_risks, 95))
p99 = float(np.percentile(grid_raw_risks, 99))
max_raw = float(np.max(grid_raw_risks))

# R_ref sensitivity table: Z at centroid, 500m, 1000m, 1100m, plus grid mean, var, std
sensitivity_summary = []
for rref in r_ref_values:
    # At centroid
    z_0 = min(100.0, 100.0 * radial_results[0]["raw_risk"] / rref)
    # At 500m
    row_500 = next(r for r in radial_results if r["distance_m"] == 500)
    z_500 = min(100.0, 100.0 * row_500["raw_risk"] / rref)
    # At 1000m
    row_1000 = next(r for r in radial_results if r["distance_m"] == 1000)
    z_1000 = min(100.0, 100.0 * row_1000["raw_risk"] / rref)
    # At 1100m
    row_1100 = next(r for r in radial_results if r["distance_m"] == 1100)
    z_1100 = min(100.0, 100.0 * row_1100["raw_risk"] / rref)
    
    grid_z = np.minimum(100.0, 100.0 * grid_raw_risks / rref)
    sensitivity_summary.append({
        "R_ref": rref,
        "Z_centroid": round(z_0, 2),
        "Z_500m": round(z_500, 2),
        "Z_1000m": round(z_1000, 2),
        "Z_1100m": round(z_1100, 2),
        "Grid_Mean_Z": round(float(np.mean(grid_z)), 2),
        "Grid_Std_Z": round(float(np.std(grid_z)), 2),
        "Grid_Variance_Z": round(float(np.var(grid_z)), 2),
        "Pct_Saturated_Z100": round(float(np.mean(grid_z >= 100.0) * 100.0), 2)
    })

with open("results/sensitivity_sweep.json", "w") as f:
    json.dump({
        "raw_risk_percentiles": {
            "p50": round(p50, 4),
            "p75": round(p75, 4),
            "p90": round(p90, 4),
            "p95": round(p95, 4),
            "p99": round(p99, 4),
            "max": round(max_raw, 4)
        },
        "sensitivity_summary": sensitivity_summary
    }, f, indent=2)

# 3. Mitigation Evaluation
# (a) Co-location collapse: s_cell = s_max * (1 + ln n)
from collections import defaultdict
grouped_cells = defaultdict(list)
for c in crimes:
    grouped_cells[(round(c["lat"], 5), round(c["lon"], 5))].append(c)

collapsed_crimes = []
for (clat, clon), items in grouped_cells.items():
    n = len(items)
    s_max = max(item["severity"] for item in items)
    s_cell = s_max * (1.0 + math.log(n))
    # Recency weight: average or max recency
    avg_w = sum(item["weight"] for item in items) / n
    collapsed_crimes.append({
        "lat": clat,
        "lon": clon,
        "severity": s_cell,
        "weight": avg_w,
        "n_original": n
    })

# Compute radial with collapsed data and R_ref = 100
collapsed_radial = []
for d in distances_m:
    q_lat = CENTROID[0] + (d / meters_per_deg_lat)
    q_lon = CENTROID[1]
    raw_r, cnt = compute_raw_risk(q_lat, q_lon, 1000.0, collapsed_crimes)
    z_100 = min(100.0, 100.0 * raw_r / 100.0)
    collapsed_radial.append({
        "distance_m": d,
        "raw_risk_collapsed": round(raw_r, 4),
        "cells_within_1000m": cnt,
        "Z_collapsed_R100": round(z_100, 2)
    })

# (b) Separate District-level low-geocoding-confidence tier
# Filter out the 469 centroid incidents (leaving micro-place records)
micro_place_crimes = [c for c in crimes if not (round(c["lat"], 4) == 12.9165 and round(c["lon"], 4) == 79.1325)]

micro_radial = []
for d in distances_m:
    q_lat = CENTROID[0] + (d / meters_per_deg_lat)
    q_lon = CENTROID[1]
    raw_r, cnt = compute_raw_risk(q_lat, q_lon, 1000.0, micro_place_crimes)
    z_100 = min(100.0, 100.0 * raw_r / 100.0)
    micro_radial.append({
        "distance_m": d,
        "raw_risk_micro": round(raw_r, 4),
        "micro_incidents": cnt,
        "Z_micro_R100": round(z_100, 2)
    })

with open("results/mitigation_comparison.json", "w") as f:
    json.dump({
        "collapsed_cells_count": len(collapsed_crimes),
        "micro_place_crimes_count": len(micro_place_crimes),
        "collapsed_radial": collapsed_radial,
        "micro_radial": micro_radial
    }, f, indent=2)

print("Zone sweep and sensitivity analysis completed successfully.")
