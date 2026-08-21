#!/usr/bin/env python3
"""
analyze_hotspots.py
===================
Crime hotspot analysis for the Vellore crime-analysis project.

Reads data/processed/news_geocoded_v2.csv and joins severity_score
and risk_level from data/processed/news_scored_final.csv via
article_id.  Produces spatial hotspots (DBSCAN), locality summaries,
temporal trends, and a textual report.

Data integrity rules observed here:
  * Source records are never deleted (input rows == output analyses).
  * No coordinates are invented: UNKNOWN/LOW confidence coordinates
    are never promoted to HIGH for spatial clustering.
  * severity_score / risk_level come from news_scored_final.csv; they
    are never recomputed in this script.
  * The Arani cache coordinate (13.331040, 80.083573) is known to be
    incorrect (it falls in the Bay of Bengal) and is excluded.
"""

from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from datetime import datetime
from math import atan2, cos, radians, sin, sqrt
from pathlib import Path

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
PROJECT_ROOT = Path(__file__).resolve().parent.parent
GEO_FILE = PROJECT_ROOT / "data" / "processed" / "news_geocoded_v2.csv"
SCORED_FILE = PROJECT_ROOT / "data" / "processed" / "news_scored_final.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "analysis"
REPORT_DIR = PROJECT_ROOT / "data" / "reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# DBSCAN clustering parameters
DBSCAN_EPSILON_KM = 1.5
DBSCAN_MIN_SAMPLES = 3

# Vellore district bounding box (approx.)
LAT_MIN, LAT_MAX = 12.5, 13.5
LON_MIN, LON_MAX = 78.5, 79.8

EARTH_RADIUS_KM = 6371.0
# --------------------------------------------------------------------------- #
# Data loading / severity join
# --------------------------------------------------------------------------- #
def load_csv(path):
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def join_scored_data(geo_rows):
    scored = {}
    if SCORED_FILE.exists():
        for r in load_csv(SCORED_FILE):
            scored[r.get("article_id", "")] = r
    joined = []
    for g in geo_rows:
        merged = dict(g)
        s = scored.get(g.get("article_id", ""))
        merged["severity_score"] = s.get("severity_score", "") if s else g.get("severity_score", "")
        merged["risk_level"] = s.get("risk_level", "") if s else g.get("risk_level", "")
        joined.append(merged)
    return joined


# --------------------------------------------------------------------------- #
# Geometry helpers
# --------------------------------------------------------------------------- #
def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two coordinate pairs in kilometres."""
    rlat1, rlon1, rlat2, rlon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = sin(dlat / 2) ** 2 + cos(rlat1) * cos(rlat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return EARTH_RADIUS_KM * c


def dbscan(points, eps_km: float, min_samples: int):
    """
    Density-based spatial clustering using Haversine distance.

    Parameters
    ----------
    points : list of (lat, lon) tuples.
    eps_km : epsilon radius in kilometres.
    min_samples : minimum points required to form a cluster.

    Returns
    -------
    list of int : cluster id per point; -1 marks noise / non-cluster.
    """
    n = len(points)
    labels = [-1] * n
    cluster_id = 0
    for i in range(n):
        if labels[i] != -1:
            continue  # already visited / assigned
        neighbours = []
        for j in range(n):
            if i == j:
                continue
            dist = haversine_km(
                points[i][0], points[i][1],
                points[j][0], points[j][1],
            )
            if dist <= eps_km:
                neighbours.append(j)
        if len(neighbours) < min_samples:
            labels[i] = -1  # noise
            continue
        cluster_id += 1
        labels[i] = cluster_id
        seed_set = set(neighbours)
        seed_set.discard(i)
        while seed_set:
            j = seed_set.pop()
            if labels[j] == -1:
                labels[j] = cluster_id
    return labels


def severity_weight(score_str) -> float:
    """Convert a severity_score to a float (0.0 when empty/invalid)."""
    try:
        return float(score_str)
    except (ValueError, TypeError):
        return 0.0


# --------------------------------------------------------------------------- #
# Core analysis
# --------------------------------------------------------------------------- #
def run_hotspot_analysis(rows):
    total = len(rows)
    has_coords = [r for r in rows if r.get("latitude", "").strip() and r.get("longitude", "").strip()]
    no_coords = [r for r in rows if not r.get("latitude", "").strip() or not r.get("longitude", "").strip()]
    conf_dist = Counter(r.get("location_confidence", "UNKNOWN") for r in rows)
    loc_dist = Counter(r.get("locality", "") or "" for r in rows)
    ctype_dist = Counter(r.get("crime_type", "Unknown") for r in rows)

    spatial_points = []
    spatial_indices = []
    for idx, r in enumerate(rows):
        conf = r.get("location_confidence", "")
        lat_str = r.get("latitude", "").strip()
        lon_str = r.get("longitude", "").strip()
        if conf == "HIGH" and lat_str and lon_str:
            try:
                lat = float(lat_str)
                lon = float(lon_str)
            except ValueError:
                continue
            if LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX:
                spatial_points.append((lat, lon))
                spatial_indices.append(idx)

    cluster_labels = dbscan(spatial_points, DBSCAN_EPSILON_KM, DBSCAN_MIN_SAMPLES)
    hotspot_members = defaultdict(list)
    for ci, label in enumerate(cluster_labels):
        if label != -1:
            orig_idx = spatial_indices[ci]
            hotspot_members[label].append(rows[orig_idx])

    hotspots = []
    for hid, members in sorted(hotspot_members.items()):
        lats = [float(m["latitude"]) for m in members]
        lons = [float(m["longitude"]) for m in members]
        sev = [severity_weight(m.get("severity_score", "")) for m in members]
        risks = [m.get("risk_level", "") for m in members]
        ctypes = Counter(m.get("crime_type", "") for m in members)
        weighted = sum(sev) / len(sev) if sev else 0.0
        hotspots.append({
            "hotspot_id": hid,
            "latitude": round(sum(lats) / len(lats), 6),
            "longitude": round(sum(lons) / len(lons), 6),
            "incident_count": len(members),
            "weighted_risk_score": round(weighted, 2),
            "dominant_crime_type": ctypes.most_common(1)[0][0] if ctypes else "Unknown",
            "critical_count": risks.count("Critical"),
            "high_count": risks.count("High"),
            "medium_count": risks.count("Medium"),
            "low_count": risks.count("Low"),
            "unknown_count": len([v for v in risks if v not in ("Critical", "High", "Medium", "Low")]),
        })
    hotspots.sort(key=lambda h: h["incident_count"], reverse=True)

    locality_groups = defaultdict(list)
    for r in rows:
        locality_groups[r.get("locality", "") or ""].append(r)
    locality_summary = []
    for loc, members in locality_groups.items():
        risks = [m.get("risk_level", "") for m in members]
        sev = [severity_weight(m.get("severity_score", "")) for m in members]
        weighted = sum(sev) / len(sev) if sev else 0.0
        locality_summary.append({
            "locality": loc or "unknown",
            "total_incidents": len(members),
            "Critical": risks.count("Critical"),
            "High": risks.count("High"),
            "Medium": risks.count("Medium"),
            "Low": risks.count("Low"),
            "Unknown": len([v for v in risks if v not in ("Critical", "High", "Medium", "Low")]),
            "weighted_risk_score": round(weighted, 2),
        })
    locality_summary.sort(key=lambda l: l["weighted_risk_score"], reverse=True)

    crime_by_loc_type = defaultdict(lambda: defaultdict(int))
    for r in rows:
        loc = r.get("locality", "") or ""
        ctype = r.get("crime_type", "Unknown")
        crime_by_loc_type[loc][ctype] += 1

    monthly = defaultdict(lambda: defaultdict(int))
    for r in rows:
        date_str = r.get("published_date", "")
        try:
            month = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z").strftime("%Y-%m")
        except ValueError:
            month = date_str[:7] if len(date_str) >= 7 else "unknown"
        ctype = r.get("crime_type", "Unknown")
        monthly[month][ctype] += 1
    temporal = []
    for month in sorted(monthly.keys()):
        for ctype, count in sorted(monthly[month].items()):
            temporal.append({"month": month, "crime_type": ctype, "count": count})

    map_points = []
    for r in rows:
        if r.get("location_confidence", "") == "HIGH" and r.get("latitude", "").strip() and r.get("longitude", "").strip():
            map_points.append({
                "article_id": r.get("article_id", ""),
                "title": r.get("title", ""),
                "crime_type": r.get("crime_type", ""),
                "published_date": r.get("published_date", ""),
                "locality": r.get("locality", ""),
                "latitude": r.get("latitude", ""),
                "longitude": r.get("longitude", ""),
                "location_confidence": "HIGH",
                "severity_score": r.get("severity_score", ""),
                "risk_level": r.get("risk_level", ""),
            })

    suspicious = []
    for r in rows:
        lat_str = r.get("latitude", "").strip()
        lon_str = r.get("longitude", "").strip()
        if lat_str and lon_str:
            try:
                lat, lon = float(lat_str), float(lon_str)
            except ValueError:
                continue
            if not (LAT_MIN <= lat <= LAT_MAX) or not (LON_MIN <= lon <= LON_MAX):
                suspicious.append({
                    "article_id": r.get("article_id", "")[:8],
                    "title": r.get("title", "")[:60],
                    "latitude": lat_str,
                    "longitude": lon_str,
                    "reason": "outside Vellore district bounds",
                })

    return {
        "rows": rows, "total": total, "has_coords": has_coords,
        "no_coords": no_coords, "conf_dist": conf_dist,
        "loc_dist": loc_dist, "ctype_dist": ctype_dist,
        "spatial_points": spatial_points,
        "hotspots": hotspots, "locality_summary": locality_summary,
        "crime_by_loc_type": dict(crime_by_loc_type),
        "temporal": temporal, "map_points": map_points,
        "suspicious": suspicious,
    }


# --------------------------------------------------------------------------- #
# Output writers
# --------------------------------------------------------------------------- #
def write_csv(path, data_rows, fieldnames):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(data_rows)


def write_outputs(results):
    hotspot_fields = [
        "hotspot_id", "latitude", "longitude", "incident_count",
        "weighted_risk_score", "dominant_crime_type",
        "critical_count", "high_count", "medium_count", "low_count",
        "unknown_count",
    ]
    write_csv(OUTPUT_DIR / "crime_hotspots.csv", results["hotspots"], hotspot_fields)

    loc_fields = [
        "locality", "total_incidents", "Critical", "High", "Medium",
        "Low", "Unknown", "weighted_risk_score",
    ]
    write_csv(OUTPUT_DIR / "locality_crime_summary.csv", results["locality_summary"], loc_fields)

    crime_loc_fields = ["locality", "crime_type", "count"]
    crime_loc_rows = []
    for loc, ctype_counts in results["crime_by_loc_type"].items():
        for ctype, count in sorted(ctype_counts.items()):
            crime_loc_rows.append({
                "locality": loc or "unknown",
                "crime_type": ctype,
                "count": count,
            })
    write_csv(OUTPUT_DIR / "crime_by_locality_and_type.csv", crime_loc_rows, crime_loc_fields)

    write_csv(OUTPUT_DIR / "crime_temporal_trends.csv", results["temporal"],
              ["month", "crime_type", "count"])

    map_fields = [
        "article_id", "title", "crime_type", "published_date", "locality",
        "latitude", "longitude", "location_confidence", "severity_score",
        "risk_level",
    ]
    write_csv(OUTPUT_DIR / "hotspot_map_points.csv", results["map_points"], map_fields)


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def generate_report(results):
    total = results["total"]
    no_coords = results["no_coords"]
    conf_dist = results["conf_dist"]
    loc_dist = results["loc_dist"]
    ctype_dist = results["ctype_dist"]
    spatial_points = results["spatial_points"]
    hotspots = results["hotspots"]
    locality_summary = results["locality_summary"]
    suspicious = results["suspicious"]
    temporal = results["temporal"]
    months = sorted(set(t["month"] for t in temporal))

    L = []
    L.append("=" * 70)
    L.append("CRIME HOTSPOT ANALYSIS REPORT")
    L.append("Generated: %s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    L.append("=" * 70)
    L.append("")
    L.append("1. DATA SUMMARY")
    L.append("-" * 40)
    L.append("Total input records: %d" % results["total"])
    L.append("Records with coordinates: %d" % (results["total"] - len(no_coords)))
    L.append("Records without coordinates: %d" % len(no_coords))
    L.append("")
    L.append("Location confidence distribution:")
    for level in ("HIGH", "LOW", "UNKNOWN"):
        L.append("  %s: %d" % (level, conf_dist.get(level, 0)))
    L.append("")
    L.append("Locality distribution:")
    for loc, count in sorted(loc_dist.items(), key=lambda x: (-x[1], str(x[0]))):
        L.append("  %s: %d" % ((loc if loc else "(empty/unknown)"), count))
    L.append("")
    L.append("Crime type distribution:")
    for ctype, count in sorted(ctype_dist.items(), key=lambda x: (-x[1], x[0])):
        L.append("  %s: %d" % (ctype, count))
    L.append("")
    L.append("2. DBSCAN SPATIAL CLUSTERING")
    L.append("-" * 40)
    L.append("Algorithm: DBSCAN (Haversine distance)")
    L.append("Epsilon (radius): %.1f km" % DBSCAN_EPSILON_KM)
    L.append("Min samples: %d" % DBSCAN_MIN_SAMPLES)
    L.append("Spatial points used (HIGH confidence only): %d" % len(spatial_points))
    L.append("Bounds validated: lat %.1f-%.1f, lon %.1f-%.1f" % (LAT_MIN, LAT_MAX, LON_MIN, LON_MAX))
    L.append("Hotspots detected: %d" % len(hotspots))
    L.append("")
    L.append("Hotspot details:")
    for h in hotspots:
        L.append("  #%d: %d incidents, risk=%.2f, crime=%s, lat=%.6f, lon=%.6f"
                 % (h["hotspot_id"], h["incident_count"], h["weighted_risk_score"],
                    h["dominant_crime_type"], h["latitude"], h["longitude"]))
        L.append("    Critical=%d, High=%d, Medium=%d, Low=%d, Unknown=%d"
                 % (h["critical_count"], h["high_count"], h["medium_count"],
                    h["low_count"], h["unknown_count"]))
    L.append("")
    L.append("3. RISK WEIGHTING")
    L.append("-" * 40)
    L.append("weighted_risk_score = mean(severity_score) per hotspot")
    L.append("Severity scores joined from news_scored_final.csv")
    L.append("")
    L.append("4. LOCALITY CRIME RANKING (by weighted_risk_score)")
    L.append("-" * 40)
    for loc in locality_summary:
        if not loc["locality"]:
            continue
        L.append("  %s: %d incidents, risk=%.2f" % (loc["locality"], loc["total_incidents"], loc["weighted_risk_score"]))
        L.append("    Critical=%d, High=%d, Medium=%d, Low=%d, Unknown=%d"
                 % (loc["Critical"], loc["High"], loc["Medium"], loc["Low"], loc["Unknown"]))
    L.append("")
    L.append("5. DOMINANT CRIME TYPES")
    L.append("-" * 40)
    for ctype, count in sorted(ctype_dist.items(), key=lambda x: (-x[1], x[0])):
        L.append("  %s: %d" % (ctype, count))
    L.append("")
    L.append("6. TEMPORAL TRENDS")
    L.append("-" * 40)
    L.append("Months covered: %s" % (", ".join(months) if months else "none"))
    for month in months:
        md = [t for t in temporal if t["month"] == month]
        tm = sum(t["count"] for t in md)
        L.append("  %s: %d total incidents" % (month, tm))
        for t in md:
            L.append("    %s: %d" % (t["crime_type"], t["count"]))
    L.append("")
    L.append("7. SUSPICIOUS / INCORRECT COORDINATES")
    L.append("-" * 40)
    if suspicious:
        L.append("WARNING: %d record(s) with out-of-bounds coordinates:" % len(suspicious))
        for s in suspicious:
            L.append("  aid=%s, lat=%s, lon=%s, reason=%s"
                     % (s["article_id"], s["latitude"], s["longitude"], s["reason"]))
    else:
        L.append("No suspicious coordinates detected.")
    L.append("  Note: known-incorrect Arani cache coord (13.331040, 80.083573)")
    L.append("  was excluded from clustering (falls in Bay of Bengal).")
    L.append("")
    L.append("8. RECORDS WITHOUT COORDINATES")
    L.append("-" * 40)
    L.append("Records without latitude/longitude: %d" % len(no_coords))
    L.append("Retained in all non-spatial analyses; excluded from clustering.")
    L.append("")
    L.append("9. LIMITATIONS")
    L.append("-" * 40)
    L.append("- %d of %d records lack specific geographic coordinates." % (len(no_coords), results["total"]))
    L.append("- Spatial clustering uses only HIGH-confidence points (%d records)." % len(spatial_points))
    L.append("- Locality/risk analysis uses ALL records (%d)." % results["total"])
    L.append("- Hotspot precision is limited by source article geo-specificity.")
    L.append("")
    L.append("=" * 70)
    L.append("END OF REPORT")
    L.append("=" * 70)
    return "\n".join(L)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    if not GEO_FILE.exists():
        print("ERROR: %s not found." % GEO_FILE)
        return 1
    geo_rows = load_csv(GEO_FILE)
    rows = join_scored_data(geo_rows)
    results = run_hotspot_analysis(rows)
    write_outputs(results)

    report = generate_report(results)
    report_path = REPORT_DIR / "hotspot_analysis_report.txt"
    report_path.write_text(report, encoding="utf-8")

    print("=" * 60)
    print("HOTSPOT ANALYSIS COMPLETE")
    print("=" * 60)
    print("Total input records: %d" % results["total"])
    print("Spatial records used (HIGH conf): %d" % len(results["spatial_points"]))
    print("Hotspots detected: %d" % len(results["hotspots"]))
    print()
    print("Top 10 hotspots:")
    for h in results["hotspots"][:10]:
        print("  #%d: %d incidents, risk=%.2f, crime=%s, lat=%.6f, lon=%.6f"
              % (h["hotspot_id"], h["incident_count"], h["weighted_risk_score"],
                 h["dominant_crime_type"], h["latitude"], h["longitude"]))
    print()
    print("Top localities (by weighted_risk_score):")
    shown = 0
    for loc in results["locality_summary"]:
        if not loc["locality"]:
            continue
        print("  %s: %d incidents, risk=%.2f" % (loc["locality"], loc["total_incidents"], loc["weighted_risk_score"]))
        shown += 1
        if shown >= 10:
            break
    print()
    print("Output files:")
    print("  data/analysis/crime_hotspots.csv")
    print("  data/analysis/locality_crime_summary.csv")
    print("  data/analysis/crime_by_locality_and_type.csv")
    print("  data/analysis/crime_temporal_trends.csv")
    print("  data/analysis/hotspot_map_points.csv")
    print("  data/reports/hotspot_analysis_report.txt")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())