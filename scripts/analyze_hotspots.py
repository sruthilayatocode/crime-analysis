#!/usr/bin/env python
"""
scripts/analyze_hotspots.py
===========================
Generate ``data/analysis/crime_hotspots.csv`` from the verified crime
coordinates stored in the database.

Hotspots are produced by grouping the HIGH-confidence incident coordinates
(location_confidence = 'HIGH' AND latitude/longitude present) by their exact
(latitude, longitude) pair and aggregating. Coordinates are NEVER fabricated:
only rows that already carry verified coordinates are used.

Deterministic and repeatable: running this twice yields the same CSV. It reads
the SAME database the Flask app uses (backend/instance/crimesense.db), so the
backend /api/hotspots endpoint and this script stay in sync.

Usage:
    python scripts/analyze_hotspots.py
    python scripts/analyze_hotspots.py --db PATH   # override db file
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND = PROJECT_ROOT / "backend"
DEFAULT_DB = BACKEND / "instance" / "crimesense.db"
OUTPUT = PROJECT_ROOT / "data" / "analysis" / "crime_hotspots.csv"


def compute_hotspots(db_path):
    """Return aggregated hotspot dicts from the verified DB rows."""
    import sqlite3

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT latitude, longitude, locality, district, crime_type, "
        "severity_score, risk_level "
        "FROM crimes "
        "WHERE location_confidence = 'HIGH' "
        "  AND latitude IS NOT NULL AND longitude IS NOT NULL"
    ).fetchall()
    conn.close()

    groups = defaultdict(list)
    for r in rows:
        groups[(float(r["latitude"]), float(r["longitude"]))].append(dict(r))

    hotspots = []
    for (lat, lon), members in sorted(groups.items()):
        sev = [m["severity_score"] for m in members
               if m["severity_score"] is not None]
        weighted = sum(sev) / len(sev) if sev else 0.0
        risk_counts = Counter((m["risk_level"] or "Unknown") for m in members)
        ctype = Counter(m["crime_type"] for m in members)
        dominant = ctype.most_common(1)[0][0] if ctype else "Unknown"
        location_name = (
            members[0]["locality"] or members[0]["district"] or "Unknown"
        )
        hotspots.append({
            "latitude": lat,
            "longitude": lon,
            "location_name": location_name,
            "incident_count": len(members),
            "weighted_risk_score": round(weighted, 4),
            "dominant_crime_type": dominant,
            "critical_count": int(risk_counts.get("Critical", 0)),
            "high_count": int(risk_counts.get("High", 0)),
            "medium_count": int(risk_counts.get("Medium", 0)),
            "low_count": int(risk_counts.get("Low", 0)),
            "unknown_count": int(risk_counts.get("Unknown", 0)),
        })

    # hotspot_id is a stable 1..N index assigned in deterministic (lat,lon) order.
    fieldnames = [
        "hotspot_id", "latitude", "longitude", "location_name",
        "incident_count", "weighted_risk_score", "dominant_crime_type",
        "critical_count", "high_count", "medium_count", "low_count",
        "unknown_count",
    ]
    rows_out = []
    for i, hs in enumerate(hotspots, start=1):
        hs["hotspot_id"] = i
        rows_out.append(hs)
    return rows_out, fieldnames


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Generate crime_hotspots.csv from verified DB coordinates.")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Database file to read from.")
    parser.add_argument("--out", default=str(OUTPUT), help="Output CSV path.")
    args = parser.parse_args(argv)

    db_path = str(Path(args.db).resolve())
    out_path = Path(args.out)

    hotspots, fieldnames = compute_hotspots(db_path)

    os.makedirs(out_path.parent, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(hotspots)

    print(f"Wrote {len(hotspots)} hotspot(s) to {out_path} (from {db_path}).")
    return 0 if hotspots else 1


if __name__ == "__main__":
    sys.exit(main())
