"""
routes.py
=========
API route definitions for the CrimeSense backend.

Endpoints exposed to the frontend:
  * GET /health                     - service & database health
  * GET /crimes                     - all crimes (with optional filters)
  * GET /crimes/{article_id}        - a single crime by primary key
  * GET /crimes/locality/{locality} - crimes at a specific locality
  * GET /crimes/crime-type/{ctype}  - crimes of a specific crime type
  * GET /crimes/risk-level/{risk}   - crimes at a specific risk level
  * GET /localities                 - distinct localities with counts
  * GET /crime-types                - distinct crime types with counts
  * GET /risk-levels                - distinct risk levels with counts
  * GET /hotspots                   - statistical hotspot data
  * GET /proximity                  - nearby verified crime locations
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

from fastapi import APIRouter, Query

from . import db

PROJECT_ROOT = Path(__file__).resolve().parent.parent
HOTSPOTS_FILE = PROJECT_ROOT / "data" / "analysis" / "crime_hotspots.csv"
EARTH_RADIUS_KM = 6371.0

router = APIRouter()


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance between two coordinate pairs in kilometres."""
    rlat1, rlon1, rlat2, rlon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    a = min(1.0, max(0.0, a))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_KM * c


def _load_hotspots():
    """Read statistical hotspots from data/analysis/crime_hotspots.csv."""
    if not HOTSPOTS_FILE.exists():
        return []
    with HOTSPOTS_FILE.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _verified_locations():
    """
    Build unique verified crime locations from HIGH-confidence rows that
    have coordinates in the database.  Never invents coordinates.
    """
    rows = db.query(
        "SELECT * FROM crime_incidents "
        "WHERE location_confidence = 'HIGH' AND latitude IS NOT NULL "
        "AND longitude IS NOT NULL"
    )
    groups = {}
    for r in rows:
        key = (r["latitude"], r["longitude"])
        groups.setdefault(key, []).append(r)

    locs = []
    for (lat, lon), members in groups.items():
        sev = [float(m["severity_score"]) for m in members if m["severity_score"] is not None]
        risks = [m["risk_level"] or "Unknown" for m in members]
        weighted = sum(sev) / len(sev) if sev else 0.0
        highest = next((lv for lv in ("Critical", "High", "Medium", "Low")
                        if lv in risks), "Unknown")
        locs.append({
            "location_name": members[0]["locality"] or "%s, %s" % (lat, lon),
            "latitude": lat,
            "longitude": lon,
            "incident_count": len(members),
            "weighted_risk_score": round(weighted, 2),
            "highest_risk_level": highest,
            "critical_count": risks.count("Critical"),
            "high_count": risks.count("High"),
            "medium_count": risks.count("Medium"),
            "low_count": risks.count("Low"),
        })
    return locs


# --------------------------------------------------------------------------- #
# Health / metadata
# --------------------------------------------------------------------------- #
@router.get("/health", tags=["service"])
def health():
    return {
        "status": "ok",
        "service": "crimesense-api",
        "database": str(db.DB_PATH),
        "total_crimes": db.total_rows(),
    }


@router.get("/localities", tags=["crimes"])
def list_localities():
    return db.query(
        "SELECT locality, COUNT(*) AS count FROM crime_incidents "
        "GROUP BY locality ORDER BY count DESC, locality"
    )


@router.get("/crime-types", tags=["crimes"])
def list_crime_types():
    return db.query(
        "SELECT crime_type, COUNT(*) AS count FROM crime_incidents "
        "GROUP BY crime_type ORDER BY count DESC, crime_type"
    )


@router.get("/risk-levels", tags=["crimes"])
def list_risk_levels():
    return db.query(
        "SELECT risk_level, COUNT(*) AS count FROM crime_incidents "
        "GROUP BY risk_level ORDER BY count DESC, risk_level"
    )


# --------------------------------------------------------------------------- #
# Crime queries
# --------------------------------------------------------------------------- #
@router.get("/crimes", tags=["crimes"])
def get_crimes(
    locality: str | None = None,
    crime_type: str | None = None,
    risk_level: str | None = None,
    has_coordinates: bool = False,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    conditions = []
    params = []
    if locality:
        conditions.append("locality = ?")
        params.append(locality)
    if crime_type:
        conditions.append("crime_type = ?")
        params.append(crime_type)
    if risk_level:
        conditions.append("risk_level = ?")
        params.append(risk_level)
    if has_coordinates:
        conditions.append("latitude IS NOT NULL AND longitude IS NOT NULL")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    total = _count_crimes(conditions, params)
    sql = "SELECT * FROM crime_incidents %s ORDER BY published_date DESC LIMIT ? OFFSET ?" % where
    rows = db.query(sql, tuple(params + [limit, offset]))
    return {"total": total, "limit": limit, "offset": offset, "crimes": rows}


def _count_crimes(conditions, params):
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = "SELECT COUNT(*) AS n FROM crime_incidents %s" % where
    return db.query_one(sql, tuple(params))["n"]


@router.get("/crimes/locality/{locality}", tags=["crimes"])
def get_crimes_by_locality(locality: str):
    return {"locality": locality,
            "crimes": db.query(
                "SELECT * FROM crime_incidents WHERE locality = ? "
                "ORDER BY published_date DESC", (locality,))}


@router.get("/crimes/crime-type/{crime_type}", tags=["crimes"])
def get_crimes_by_type(crime_type: str):
    return {"crime_type": crime_type,
            "crimes": db.query(
                "SELECT * FROM crime_incidents WHERE crime_type = ? "
                "ORDER BY published_date DESC", (crime_type,))}


@router.get("/crimes/risk-level/{risk_level}", tags=["crimes"])
def get_crimes_by_risk(risk_level: str):
    return {"risk_level": risk_level,
            "crimes": db.query(
                "SELECT * FROM crime_incidents WHERE risk_level = ? "
                "ORDER BY published_date DESC", (risk_level,))}


@router.get("/crimes/{article_id}", tags=["crimes"])
def get_crime(article_id: str):
    row = db.query_one("SELECT * FROM crime_incidents WHERE article_id = ?",
                       (article_id,))
    if row is None:
        return {"error": "not_found", "article_id": article_id, "crime": None}
    return {"article_id": article_id, "crime": row}


# --------------------------------------------------------------------------- #
# Hotspot data
# --------------------------------------------------------------------------- #
@router.get("/hotspots", tags=["hotspots"])
def get_hotspots():
    hotspots = _load_hotspots()
    return {"count": len(hotspots), "hotspots": hotspots}


# --------------------------------------------------------------------------- #
# Proximity
# --------------------------------------------------------------------------- #
@router.get("/proximity", tags=["proximity"])
def get_proximity(
    lat: float = Query(..., description="User latitude"),
    lon: float = Query(..., description="User longitude"),
    radius: float = Query(2.0, ge=0.1, le=50, description="Search radius in km"),
):
    verified = _verified_locations()
    nearby = []
    for loc in verified:
        dist = _haversine_km(lat, lon, float(loc["latitude"]), float(loc["longitude"]))
        if dist <= radius:
            entry = dict(loc)
            entry["distance_km"] = round(dist, 3)
            nearby.append(entry)
    nearby.sort(key=lambda e: e["distance_km"])

    rank = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
    if nearby:
        worst = max(rank.get(e["highest_risk_level"], 0) for e in nearby)
        level = next((k for k, v in rank.items() if v == worst), "NONE")
    else:
        level = "NONE"

    return {
        "user_location": {"latitude": lat, "longitude": lon},
        "search_radius_km": radius,
        "verified_locations_total": len(verified),
        "nearby_count": len(nearby),
        "overall_alert_level": level,
        "nearby": nearby,
    }