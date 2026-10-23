from collections import defaultdict
from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_KM = 6371.0



def haversine_km(
    latitude_1,
    longitude_1,
    latitude_2,
    longitude_2
):
    """
    Great-circle distance between two coordinates in km.
    """
    lat1, lon1, lat2, lon2 = map(
        radians,
        (
            float(latitude_1),
            float(longitude_1),
            float(latitude_2),
            float(longitude_2),
        ),
    )

    a = (
        sin((lat2 - lat1) / 2) ** 2
        + cos(lat1) * cos(lat2)
        * sin((lon2 - lon1) / 2) ** 2
    )

    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))


def load_verified_locations():
    """
    Load verified (HIGH-confidence) crime locations directly from the
    database, grouped by exact coordinate.

    Records with NULL coordinates or non-HIGH confidence are excluded.
    """
    try:
        from models.crime import Crime
        from database import db

        verified_records = (
            Crime.query.filter(
                Crime.location_confidence == "HIGH",
                Crime.latitude.isnot(None),
                Crime.longitude.isnot(None),
            ).all()
        )
    except Exception:
        return []

    groups = defaultdict(list)
    for c in verified_records:
        key = (round(c.latitude, 6), round(c.longitude, 6))
        groups[key].append(c)

    locations = []
    severity_order = ["Critical", "High", "Medium", "Low", "Unknown"]

    for (lat, lon), records in groups.items():
        risk_counts = defaultdict(int)
        for r in records:
            lvl = r.risk_level or (r.severity.capitalize() if r.severity else "Unknown")
            risk_counts[lvl] += 1

        highest_risk = next(
            (level for level in severity_order if risk_counts.get(level)),
            "Unknown",
        )

        crime_types = defaultdict(int)
        for r in records:
            ctype = r.crime_type or "General"
            crime_types[ctype] += 1
        dominant = max(crime_types.items(), key=lambda kv: kv[1])[0]

        locations.append({
            "location_name": records[0].locality or "Verified Location",
            "latitude": float(lat),
            "longitude": float(lon),
            "incident_count": len(records),
            "risk_counts": dict(risk_counts),
            "highest_risk_level": highest_risk,
            "dominant_crime_type": dominant,
        })

    return locations


def find_nearby_verified_locations(
    user_latitude,
    user_longitude,
    radius_km=2.0
):
    """
    Return verified crime locations within radius_km of the
    user, sorted by distance (nearest first).
    """
    nearby = []
    for location in load_verified_locations():
        distance = haversine_km(
            user_latitude,
            user_longitude,
            location["latitude"],
            location["longitude"],
        )
        if distance <= radius_km:
            entry = dict(location)
            entry["distance_km"] = round(distance, 3)
            nearby.append(entry)

    nearby.sort(key=lambda item: item["distance_km"])
    return nearby


def determine_alert_level(nearby_locations):
    """
    Transparent rule-based alert level (no ML):
    the most severe risk level present among nearby
    verified locations.
    """
    if not nearby_locations:
        return "NONE"

    severity_order = [
        "CRITICAL", "HIGH", "MEDIUM", "LOW"
    ]
    present = {
        (loc["highest_risk_level"] or "").upper()
        for loc in nearby_locations
    }
    return next(
        (
            level for level in severity_order
            if level in present
        ),
        "LOW",
    )


# ----------------------------------------------------------------------
# Legacy functions kept for backwards compatibility
# ----------------------------------------------------------------------

from math import atan2, degrees  # noqa: E402


def calculate_distance(
    latitude_1,
    longitude_1,
    latitude_2,
    longitude_2
):
    """
    Legacy helper: distance in meters (Haversine).
    """
    return round(
        haversine_km(
            latitude_1,
            longitude_1,
            latitude_2,
            longitude_2,
        ) * 1000,
        2
    )


def check_proximity(
    user_latitude,
    user_longitude,
    hotspot_latitude,
    hotspot_longitude,
    alert_radius=500
):
    """
    Legacy helper: single-point proximity check in meters.
    """
    distance = calculate_distance(
        user_latitude,
        user_longitude,
        hotspot_latitude,
        hotspot_longitude
    )

    is_nearby = distance <= alert_radius

    return {
        "distance_meters": distance,
        "alert_radius_meters": alert_radius,
        "is_nearby": is_nearby
    }