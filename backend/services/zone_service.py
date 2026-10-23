"""
zone_service.py
===============
Core service for geographic zone risk assessment and proximity scoring.

Features:
- Bounding-box pre-filtering on database coordinates for sub-millisecond retrieval.
- Exact Haversine great-circle distance computation in meters.
- Multi-factor risk scoring: sum(severity_score * distance_decay * recency_weight).
- 0-100 score normalization mapped to RED, YELLOW, GREEN zones using zone_config.
- Aggregation of top 3 crime types, nearest incident distance, and most severe recent incident.
- Graceful low-confidence fallback for areas with zero crime data.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from math import asin, cos, radians, sin, sqrt
from typing import Any, Dict, List, Optional, Tuple, Union

from dateutil import parser as date_parser

try:
    from zone_config import (
        DEFAULT_RADIUS_METERS,
        LIMITED_DATA_NOTE,
        MAX_SCORE,
        MIN_SCORE,
        RECENCY_CONFIG,
        SAFETY_TIPS,
        ZONE_THRESHOLDS,
    )
except ImportError:
    from backend.zone_config import (
        DEFAULT_RADIUS_METERS,
        LIMITED_DATA_NOTE,
        MAX_SCORE,
        MIN_SCORE,
        RECENCY_CONFIG,
        SAFETY_TIPS,
        ZONE_THRESHOLDS,
    )

EARTH_RADIUS_METERS = 6371000.0


def haversine_distance_meters(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """
    Compute great-circle distance between two geographic coordinates in meters.
    """
    phi1, phi2 = radians(lat1), radians(lat2)
    delta_phi = radians(lat2 - lat1)
    delta_lambda = radians(lon2 - lon1)

    a = (
        sin(delta_phi / 2.0) ** 2
        + cos(phi1) * cos(phi2) * sin(delta_lambda / 2.0) ** 2
    )
    # Clamp to 1.0 to avoid domain errors from float inaccuracies
    c = 2.0 * asin(sqrt(min(1.0, max(0.0, a))))
    return EARTH_RADIUS_METERS * c


def get_bounding_box(
    lat: float,
    lng: float,
    radius_meters: float,
) -> Dict[str, float]:
    """
    Compute a conservative bounding box (min_lat, max_lat, min_lng, max_lng)
    around a center point to pre-filter candidate coordinates via database index.
    """
    # 1 degree of latitude is approximately 111,139 meters
    lat_delta = (radius_meters / 111139.0) * 1.05
    rad_lat = radians(lat)
    cos_lat = max(abs(cos(rad_lat)), 0.01)
    lng_delta = (radius_meters / (111139.0 * cos_lat)) * 1.05

    return {
        "min_lat": lat - lat_delta,
        "max_lat": lat + lat_delta,
        "min_lng": lng - lng_delta,
        "max_lng": lng + lng_delta,
    }


def parse_datetime(date_val: Any) -> Optional[datetime]:
    """
    Robustly parse date strings or datetime objects to UTC datetime.
    """
    if date_val is None:
        return None
    if isinstance(date_val, datetime):
        if date_val.tzinfo is None:
            return date_val.replace(tzinfo=timezone.utc)
        return date_val.astimezone(timezone.utc)

    text = str(date_val).strip()
    if not text:
        return None

    try:
        dt = date_parser.parse(text)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def calculate_recency_weight(
    date_val: Any,
    reference_time: Optional[datetime] = None,
) -> Tuple[float, float]:
    """
    Compute recency weight and epoch timestamp for an incident.
    - Newer than 6 months (~182.5 days): 1.0
    - 6 to 24 months (~182.5 to 730 days): 0.7
    - Older than 24 months (> 730 days): 0.4
    - Unknown date: default 0.4

    Returns:
        (recency_weight, epoch_timestamp)
    """
    dt = parse_datetime(date_val)
    if dt is None:
        return RECENCY_CONFIG["DEFAULT_WEIGHT"], 0.0

    if reference_time is None:
        ref_dt = datetime.now(timezone.utc)
    else:
        ref_dt = (
            reference_time.replace(tzinfo=timezone.utc)
            if reference_time.tzinfo is None
            else reference_time.astimezone(timezone.utc)
        )

    diff_seconds = (ref_dt - dt).total_seconds()
    diff_days = diff_seconds / 86400.0

    if diff_days <= RECENCY_CONFIG["NEW_THRESHOLD_DAYS"]:
        weight = RECENCY_CONFIG["WEIGHT_NEW"]
    elif diff_days <= RECENCY_CONFIG["MEDIUM_THRESHOLD_DAYS"]:
        weight = RECENCY_CONFIG["WEIGHT_MEDIUM"]
    else:
        weight = RECENCY_CONFIG["WEIGHT_OLD"]

    return weight, dt.timestamp()


def classify_zone(score: float) -> str:
    """
    Map normalized 0-100 risk score to zone label:
    - >= 60: RED
    - 30 to 59: YELLOW
    - < 30: GREEN
    """
    if score >= ZONE_THRESHOLDS["RED"]:
        return "RED"
    elif score >= ZONE_THRESHOLDS["YELLOW"]:
        return "YELLOW"
    else:
        return "GREEN"


def calculate_zone_risk(
    lat: float,
    lng: float,
    radius: float = DEFAULT_RADIUS_METERS,
    reference_time: Optional[datetime] = None,
    candidate_crimes: Optional[List[Any]] = None,
) -> Dict[str, Any]:
    """
    Main zone calculation logic.

    Args:
        lat: Latitude of query location (-90 to 90).
        lng: Longitude of query location (-180 to 180).
        radius: Search radius in meters (defaults to 1000m).
        reference_time: Optional datetime reference (useful for deterministic tests).
        candidate_crimes: Optional list of crimes (dicts or model instances).
                         If None, queries the database with bounding-box prefilter.

    Returns:
        Structured zone analysis response dict.
    """
    radius = float(radius) if radius is not None else DEFAULT_RADIUS_METERS
    if radius <= 0:
        radius = DEFAULT_RADIUS_METERS

    # Fetch candidate crimes if not explicitly provided
    if candidate_crimes is None:
        try:
            from database import db
            from models.crime import Crime

            bbox = get_bounding_box(lat, lng, radius)
            candidate_crimes = (
                Crime.query.filter(
                    Crime.latitude.isnot(None),
                    Crime.longitude.isnot(None),
                    Crime.latitude.between(bbox["min_lat"], bbox["max_lat"]),
                    Crime.longitude.between(bbox["min_lng"], bbox["max_lng"]),
                ).all()
            )
        except Exception:
            candidate_crimes = []

    incidents_within_radius: List[Dict[str, Any]] = []
    raw_score = 0.0
    crime_types_counter: Counter = Counter()

    for item in candidate_crimes:
        # Support both SQLAlchemy model instances and dicts
        if isinstance(item, dict):
            c_lat = item.get("latitude")
            c_lng = item.get("longitude")
            title = item.get("title")
            pub_date = item.get("published_date") or item.get("crime_date")
            source_url = item.get("url") or item.get("source_url") or item.get("source")
            crime_type = item.get("crime_type") or "Unknown"
            sev = item.get("severity_score")
        else:
            c_lat = getattr(item, "latitude", None)
            c_lng = getattr(item, "longitude", None)
            title = getattr(item, "title", None)
            pub_date = getattr(item, "published_date", None) or getattr(item, "crime_date", None)
            source_url = getattr(item, "url", None) or getattr(item, "source", None)
            crime_type = getattr(item, "crime_type", None) or "Unknown"
            sev = getattr(item, "severity_score", None)

        if c_lat is None or c_lng is None:
            continue

        try:
            c_lat_f = float(c_lat)
            c_lng_f = float(c_lng)
        except (ValueError, TypeError):
            continue

        dist = haversine_distance_meters(lat, lng, c_lat_f, c_lng_f)
        if dist > radius:
            continue

        # Severity score fallback
        severity_score = float(sev) if sev is not None else 5.0

        # Distance decay: linear drop-off 1 - (d / radius)
        distance_decay = max(0.0, 1.0 - (dist / radius))

        # Recency weight: 1.0 (<6 mo), 0.7 (6-24 mo), 0.4 (>24 mo)
        recency_weight, timestamp = calculate_recency_weight(pub_date, reference_time)

        # Incident risk contribution
        incident_risk = severity_score * distance_decay * recency_weight
        raw_score += incident_risk

        crime_types_counter[crime_type] += 1

        incidents_within_radius.append({
            "distance": dist,
            "severity_score": severity_score,
            "timestamp": timestamp,
            "title": title,
            "date": pub_date,
            "source_url": source_url,
            "crime_type": crime_type,
            "incident_risk": incident_risk,
        })

    incident_count = len(incidents_within_radius)

    # Edge case: No data exists within radius
    if incident_count == 0:
        return {
            "zone": "GREEN",
            "score": 0.0,
            "incident_count": 0,
            "top_3_crime_types": [],
            "top_crime_types": [],
            "nearest_incident_distance": None,
            "most_severe_recent_incident": None,
            "nearby_incidents": [],
            "safety_tip": SAFETY_TIPS["GREEN_LOW_CONFIDENCE"],
            "confidence": "low",
            "note": LIMITED_DATA_NOTE,
            "radius": round(radius, 1),
            "lat": lat,
            "lng": lng,
        }

    # Normalization: Clamp to [MIN_SCORE, MAX_SCORE] and round to 1 decimal place
    normalized_score = min(MAX_SCORE, max(MIN_SCORE, round(raw_score, 1)))
    zone = classify_zone(normalized_score)

    # Top 3 crime types by occurrence count
    top_3_crime_types = [ct for ct, _ in crime_types_counter.most_common(3)]

    # Nearest incident distance
    nearest_dist = round(min(inc["distance"] for inc in incidents_within_radius), 1)

    # Most severe recent incident:
    # Sort primarily by severity_score descending, secondarily by timestamp descending
    incidents_within_radius.sort(
        key=lambda inc: (inc["severity_score"], inc["timestamp"]),
        reverse=True,
    )
    best = incidents_within_radius[0]
    most_severe_recent_incident = {
        "title": best["title"] or "Incident Record",
        "date": best["date"],
        "source_url": best["source_url"],
        "severity_score": round(best["severity_score"], 1),
        "crime_type": best["crime_type"],
    }

    safety_tip = SAFETY_TIPS.get(zone, SAFETY_TIPS["GREEN"])

    # Build nearby_incidents list: up to 5 closest incidents for the UI
    by_distance = sorted(incidents_within_radius, key=lambda inc: inc["distance"])
    nearby_incidents = [
        {
            "crime_type": inc["crime_type"],
            "date": str(inc["date"]) if inc["date"] is not None else None,
            "distance_m": round(inc["distance"], 0),
            "severity_score": round(inc["severity_score"], 1),
            "title": inc["title"] or "Incident Record",
        }
        for inc in by_distance[:5]
    ]

    return {
        "zone": zone,
        "score": normalized_score,
        "incident_count": incident_count,
        "top_3_crime_types": top_3_crime_types,
        "top_crime_types": top_3_crime_types,
        "nearest_incident_distance": nearest_dist,
        "most_severe_recent_incident": most_severe_recent_incident,
        "nearby_incidents": nearby_incidents,
        "safety_tip": safety_tip,
        "confidence": "high",
        "note": None,
        "radius": round(radius, 1),
        "lat": lat,
        "lng": lng,
    }
