#!/usr/bin/env python3
"""
proximity_alert.py
==================
Proximity-based crime alert module for the Vellore crime-analysis project.

Given a user's current latitude/longitude and a search radius (km), this
module finds nearby VERIFIED crime locations (HIGH-confidence geographic
data only), computes Haversine great-circle distances, classifies a
transparent alert level, and writes:
    data/analysis/proximity_alert_results.csv
    data/reports/proximity_alert_report.txt

Data integrity rules observed here:
  * Only verified / HIGH-confidence geographic locations are used.
  * No coordinates are invented, perturbed, or moved.
  * UNKNOWN / LOW-confidence or district-level coordinates are NEVER used
    as exact nearby crime locations.
  * The source records (news_geocoded_v2.csv, news_scored_final.csv,
    crime_hotspots.csv, verified_location_summary.csv) are never modified.
  * When verified geographic information is insufficient, the module says
    so explicitly instead of claiming "no crimes exist nearby".

Usage (CLI):
    python scripts/proximity_alert.py --latitude 13.0435 --longitude 79.2404 --radius 2
"""

from __future__ import annotations

import argparse
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
ANALYSIS_DIR = PROJECT_ROOT / "data" / "analysis"
REPORT_DIR = PROJECT_ROOT / "data" / "reports"

VERIFIED_FILE = ANALYSIS_DIR / "verified_location_summary.csv"
MAP_POINTS_FILE = ANALYSIS_DIR / "hotspot_map_points.csv"

OUTPUT_CSV = ANALYSIS_DIR / "proximity_alert_results.csv"
REPORT_FILE = REPORT_DIR / "proximity_alert_report.txt"

DEFAULT_RADIUS_KM = 2.0
EARTH_RADIUS_KM = 6371.0

# Risk levels ordered from most to least severe.
RISK_ORDER = ["Critical", "High", "Medium", "Low"]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def to_float(value, default=0.0) -> float:
    """Robust float conversion (returns default for empty/invalid input)."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def load_csv(path):
    """Read a CSV into a list of dicts (empty list if the file is absent)."""
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Great-circle distance between two coordinate pairs, in kilometres.

    Uses the Haversine formula (arc-based distance), never a Euclidean
    approximation on raw latitude/longitude degrees.

        a = sin^2(dlat/2) + cos(lat1) * cos(lat2) * sin^2(dlon/2)
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = EARTH_RADIUS_KM * c

    All angles are converted to radians first.
    """
    rlat1, rlon1, rlat2, rlon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = sin(dlat / 2) ** 2 + cos(rlat1) * cos(rlat2) * sin(dlon / 2) ** 2
    a = min(1.0, max(0.0, a))  # guard against tiny floating-point drift
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return EARTH_RADIUS_KM * c


def highest_risk_level(risks):
    """Return the most severe risk level present in a list of risk strings."""
    for level in RISK_ORDER:
        if level in risks:
            return level
    return "Unknown"


# --------------------------------------------------------------------------- #
# Verified crime locations
# --------------------------------------------------------------------------- #
def build_verified_from_map_points(rows):
    """Derive unique verified locations from HIGH-confidence map points,
    grouping by exact (latitude, longitude) coordinate (never moved)."""
    groups = defaultdict(list)
    for r in rows:
        lat_s = (r.get("latitude") or "").strip()
        lon_s = (r.get("longitude") or "").strip()
        if not lat_s or not lon_s:
            continue
        groups[(lat_s, lon_s)].append(r)

    locations = []
    for (lat_s, lon_s), members in groups.items():
        sev = [to_float(m.get("severity_score", "")) for m in members]
        risks = [(m.get("risk_level", "") or "Unknown") for m in members]
        ctypes = Counter((m.get("crime_type", "Unknown") or "Unknown") for m in members)
        weighted = sum(sev) / len(sev) if sev else 0.0
        locations.append({
            "location_name": members[0].get("locality", "") or (lat_s + "," + lon_s),
            "latitude": lat_s,
            "longitude": lon_s,
            "incident_count": len(members),
            "weighted_risk_score": round(weighted, 2),
            "critical_count": risks.count("Critical"),
            "high_count": risks.count("High"),
            "medium_count": risks.count("Medium"),
            "low_count": risks.count("Low"),
            "unknown_count": sum(1 for v in risks if v not in RISK_ORDER),
            "dominant_crime_type": ctypes.most_common(1)[0][0] if ctypes else "Unknown",
            "highest_risk_level": highest_risk_level(risks),
        })
    return locations


def load_verified_locations():
    """
    Load verified crime locations.

    Prefers data/analysis/verified_location_summary.csv.  When that file is
    not present (e.g. the spatial-analysis stage has not yet run to write it),
    fall back to deriving unique locations from the HIGH-confidence
    data/analysis/hotspot_map_points.csv.  Returns (locations, source_name).
    """
    rows = load_csv(VERIFIED_FILE)
    if rows:
        locations = []
        for r in rows:
            locations.append({
                "location_name": r.get("location_name", ""),
                "latitude": (r.get("latitude") or "").strip(),
                "longitude": (r.get("longitude") or "").strip(),
                "incident_count": int(to_float(r.get("incident_count"))),
                "weighted_risk_score": round(to_float(r.get("weighted_risk_score")), 2),
                "critical_count": int(to_float(r.get("critical_count"))),
                "high_count": int(to_float(r.get("high_count"))),
                "medium_count": int(to_float(r.get("medium_count"))),
                "low_count": int(to_float(r.get("low_count"))),
                "unknown_count": int(to_float(r.get("unknown_count"))),
                "dominant_crime_type": r.get("dominant_crime_type", ""),
                "highest_risk_level": r.get("highest_risk_level", ""),
            })
        return locations, str(VERIFIED_FILE)

    locations = build_verified_from_map_points(load_csv(MAP_POINTS_FILE))
    return locations, str(MAP_POINTS_FILE) + " (derived: verified_location_summary.csv not present)"


# --------------------------------------------------------------------------- #
# Alert classification
# --------------------------------------------------------------------------- #
def location_alert_level(loc):
    """
    Classify the alert contribution of one verified location.

    Rules (deterministic, no ML):
      CRITICAL -> the location contains at least one Critical incident
      HIGH     -> the location contains at least one High incident
      MEDIUM   -> the location contains at least one Medium incident
      LOW      -> the location contains only Low incidents
      NONE     -> no risk-incident data available
    """
    if int(loc["critical_count"]) > 0:
        return "CRITICAL"
    if int(loc["high_count"]) > 0:
        return "HIGH"
    if int(loc["medium_count"]) > 0:
        return "MEDIUM"
    if int(loc["low_count"]) > 0:
        return "LOW"
    return "NONE"


def overall_alert_level(levels):
    """Return the most severe alert level among a set of nearby locations."""
    rank = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "NONE": 0}
    if not levels:
        return "NONE"
    best = max(levels, key=lambda x: rank.get(x, 0))
    return best


def find_nearby(user_lat, user_lon, radius_km, verified_locations):
    """
    Find verified crime locations within `radius_km` of the user.

    Returns a list of dicts, each with the location fields plus distance_km,
    sorted by distance ascending.
    """
    nearby = []
    for loc in verified_locations:
        try:
            lat = float(loc["latitude"])
            lon = float(loc["longitude"])
        except (ValueError, TypeError):
            continue
        dist = haversine_km(user_lat, user_lon, lat, lon)
        if dist <= radius_km:
            entry = dict(loc)
            entry["distance_km"] = round(dist, 3)
            entry["alert_level"] = location_alert_level(loc)
            nearby.append(entry)
    nearby.sort(key=lambda e: e["distance_km"])
    return nearby


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #
FIELDS = [
    "location_name", "latitude", "longitude", "distance_km",
    "incident_count", "weighted_risk_score", "highest_risk_level",
    "dominant_crime_type", "critical_count", "high_count", "medium_count",
    "low_count",
]


def write_results_csv(nearby):
    """Write data/analysis/proximity_alert_results.csv for the current run."""
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(nearby)


def make_report(user_lat, user_lon, radius_km, source_name, verified,
                nearby, overall):
    """Build the textual proximity-alert report."""
    L = []
    L.append("=" * 70)
    L.append("CRIME PROXIMITY ALERT REPORT")
    L.append("Generated: %s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    L.append("=" * 70)
    L.append("")
    L.append("USER LOCATION")
    L.append("-" * 40)
    L.append("Latitude:  %.6f" % user_lat)
    L.append("Longitude: %.6f" % user_lon)
    L.append("Search radius: %.1f km" % radius_km)
    L.append("")
    L.append("DATA SOURCE")
    L.append("-" * 40)
    L.append("Verified locations used: %s" % source_name)
    L.append("Total verified crime locations known: %d" % len(verified))
    L.append("Only HIGH-confidence geographic records are treated as exact" +
             " nearby crime locations.")
    L.append("")
    L.append("DISTANCE METHOD")
    L.append("-" * 40)
    L.append("Haversine great-circle distance (kilometres):")
    L.append("  a = sin^2(dlat/2) + cos(lat1)*cos(lat2)*sin^2(dlon/2)")
    L.append("  c = 2*atan2(sqrt(a), sqrt(1-a));  dist = 6371.0 * c")
    L.append("Euclidean distance on raw degrees is never used.")
    L.append("")
    L.append("NEARBY VERIFIED CRIME LOCATIONS (%d found within %.1f km)"
             % (len(nearby), radius_km))
    L.append("-" * 40)
    if nearby:
        for e in nearby:
            L.append("  %s (%.3f km away)" % (e["location_name"], e["distance_km"]))
            L.append("    lat=%.6f lon=%.6f" % (float(e["latitude"]), float(e["longitude"])))
            L.append("    incidents=%d weighted_risk=%.2f highest_risk=%s" %
                     (e["incident_count"], e["weighted_risk_score"], e["highest_risk_level"]))
            L.append("    dominant_crime=%s  Critical=%d High=%d Medium=%d Low=%d" %
                     (e["dominant_crime_type"], e["critical_count"], e["high_count"],
                      e["medium_count"], e["low_count"]))
            L.append("    location_alert=%s" % e["alert_level"])
    else:
        L.append("  NONE")
    L.append("")
    L.append("OVERALL ALERT LEVEL")
    L.append("-" * 40)
    L.append("Result: %s" % overall)
    L.append("Alert classification (deterministic, no ML):")
    L.append("  CRITICAL -> a nearby verified location has Critical incidents")
    L.append("  HIGH     -> a nearby verified location has High risk incidents")
    L.append("  MEDIUM   -> a nearby verified location has Medium risk incidents")
    L.append("  LOW      -> only Low risk incidents nearby")
    L.append("  NONE     -> no verified crime location within the radius")
    L.append("")
    L.append("DATA LIMITATION")
    L.append("-" * 40)
    if nearby:
        L.append("  %d verified crime location(s) found within %.1f km." %
                 (len(nearby), radius_km))
        L.append("  This reflects only HIGH-confidence geographic data.")
    else:
        L.append("  No verified crime location was found within %.1f km of the" % radius_km)
        L.append("  user's position. This means there is INSUFFICIENT verified")
        L.append("  geographic information nearby; it does NOT mean no crime exists.")
    L.append("  Only the %d verified location(s) above are treated as exact nearby" % len(nearby))
    L.append("  crime locations; all other records lack verified coordinates.")
    L.append("")
    L.append("ALERT LOGIC DOCUMENTATION")
    L.append("-" * 40)
    L.append("1. Load verified crime locations (HIGH-confidence only).")
    L.append("2. Compute Haversine distance from user to every verified location.")
    L.append("3. Keep locations with distance <= radius_km.")
    L.append("4. Sort by distance ascending.")
    L.append("5. Overall alert = strongest level among nearby locations.")
    L.append("")
    L.append("=" * 70)
    L.append("END OF REPORT")
    L.append("=" * 70)
    return "\n".join(L)


def write_report(user_lat, user_lon, radius_km, source_name, verified,
                 nearby, overall):
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    text = make_report(user_lat, user_lon, radius_km, source_name, verified,
                       nearby, overall)
    REPORT_FILE.write_text(text, encoding="utf-8")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Crime proximity alert for verified crime locations.")
    parser.add_argument("--latitude", type=float, required=True,
                        help="User's current latitude")
    parser.add_argument("--longitude", type=float, required=True,
                        help="User's current longitude")
    parser.add_argument("--radius", type=float, default=DEFAULT_RADIUS_KM,
                        help="Search radius in km (default: %.1f)" % DEFAULT_RADIUS_KM)
    return parser.parse_args(argv)


def run(user_lat, user_lon, radius_km=DEFAULT_RADIUS_KM, verbose=True):
    verified, source = load_verified_locations()
    nearby = find_nearby(user_lat, user_lon, radius_km, verified)

    if nearby:
        overall = overall_alert_level([e["alert_level"] for e in nearby])
    else:
        overall = "NONE"

    write_results_csv(nearby)
    write_report(user_lat, user_lon, radius_km, source, verified, nearby, overall)

    if verbose:
        print("=" * 60)
        print("PROXIMITY ALERT RESULT")
        print("=" * 60)
        print("User location:")
        print("  Latitude:  %.6f" % user_lat)
        print("  Longitude: %.6f" % user_lon)
        print("  Search radius: %.1f km" % radius_km)
        print()
        print("Verified crime locations known: %d" % len(verified))
        print("  (source: %s)" % source)
        print()
        print("Nearby verified crime locations (%d found within %.1f km):"
              % (len(nearby), radius_km))
        if nearby:
            for e in nearby:
                print("  %-14s %.3f km  incidents=%d risk=%.2f highest=%s alert=%s"
                      % (e["location_name"], e["distance_km"],
                         e["incident_count"], e["weighted_risk_score"],
                         e["highest_risk_level"], e["alert_level"]))
        else:
            print("  NONE")
        print()
        print("Overall alert level: %s" % overall)
        print("=" * 60)

    return {"user": (user_lat, user_lon), "radius_km": radius_km,
            "verified_count": len(verified), "nearby": nearby,
            "overall_level": overall}


def main(argv=None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    run(args.latitude, args.longitude, args.radius)
    return 0


if __name__ == "__main__":
    sys.exit(main())