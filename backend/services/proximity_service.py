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


def _validate_coordinate(latitude, longitude):
    """Validate latitude and longitude coordinates."""
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (TypeError, ValueError):
        return None

    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
        return None

    return (lat, lon)


def calculate_distance_km(latitude_1, longitude_1, latitude_2, longitude_2):
    """Distance in kilometres between two coordinates."""
    c1 = _validate_coordinate(latitude_1, longitude_1)
    c2 = _validate_coordinate(latitude_2, longitude_2)
    if c1 is None or c2 is None:
        return None
    try:
        return haversine_km(c1[0], c1[1], c2[0], c2[1])
    except Exception:
        return None


def calculate_distance(latitude_1, longitude_1, latitude_2, longitude_2):
    """Distance in metres between two coordinates."""
    km = calculate_distance_km(latitude_1, longitude_1, latitude_2, longitude_2)
    return km * 1000.0 if km is not None else None



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


def find_nearby_crimes(
    crimes,
    latitude,
    longitude,
    radius_km,
    limit=None
):
    """
    Filter crime records to those located within radius_km of the given coordinates.
    """
    if radius_km is None or radius_km <= 0:
        return []

    nearby_crimes = []
    for crime in crimes:
        crime_latitude = crime.get("latitude") if isinstance(crime, dict) else getattr(crime, "latitude", None)
        crime_longitude = crime.get("longitude") if isinstance(crime, dict) else getattr(crime, "longitude", None)

        if crime_latitude is None or crime_longitude is None:
            continue

        distance_km = calculate_distance_km(
            latitude,
            longitude,
            crime_latitude,
            crime_longitude
        )

        if distance_km is None or distance_km > radius_km:
            continue

        if isinstance(crime, dict):
            nearby_crime = dict(crime)
        else:
            nearby_crime = crime.to_dict() if hasattr(crime, "to_dict") else vars(crime)

        nearby_crime["distance_km"] = distance_km
        nearby_crimes.append(nearby_crime)

    nearby_crimes.sort(key=lambda c: c["distance_km"])
    if limit is not None and limit > 0:
        nearby_crimes = nearby_crimes[:limit]

    return nearby_crimes


def _validate_coordinate(latitude, longitude):
    """Validate latitude and longitude coordinates."""
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (TypeError, ValueError):
        return None

    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
        return None

    return (lat, lon)


def find_nearest_hotspot(hotspots, latitude, longitude):
    """Return the hotspot closest to the given coordinates, or None when no hotspots exist."""
    coord = _validate_coordinate(latitude, longitude)
    if coord is None or not hotspots:
        return None

    nearest_hotspot = None
    nearest_distance = None

    for hotspot in hotspots:
        hotspot_lat = hotspot.get("centroid_latitude") if isinstance(hotspot, dict) else getattr(hotspot, "centroid_latitude", None)
        hotspot_lon = hotspot.get("centroid_longitude") if isinstance(hotspot, dict) else getattr(hotspot, "centroid_longitude", None)

        if hotspot_lat is None or hotspot_lon is None:
            continue

        distance_meters = calculate_distance(latitude, longitude, hotspot_lat, hotspot_lon)
        if distance_meters is None:
            continue

        if nearest_distance is None or distance_meters < nearest_distance:
            nearest_distance = distance_meters
            nearest_hotspot = hotspot

    return nearest_hotspot


def find_nearby_hotspots(hotspots, latitude, longitude, radius_km, limit=None):
    """Filter hotspots to those within radius_km of the given coordinates."""
    if radius_km is None or radius_km <= 0 or not hotspots:
        return []

    coord = _validate_coordinate(latitude, longitude)
    if coord is None:
        return []

    nearby = []
    for hotspot in hotspots:
        hotspot_lat = hotspot.get("centroid_latitude") if isinstance(hotspot, dict) else getattr(hotspot, "centroid_latitude", None)
        hotspot_lon = hotspot.get("centroid_longitude") if isinstance(hotspot, dict) else getattr(hotspot, "centroid_longitude", None)

        if hotspot_lat is None or hotspot_lon is None:
            continue

        distance_km = calculate_distance_km(latitude, longitude, hotspot_lat, hotspot_lon)
        if distance_km is None or distance_km > radius_km:
            continue

        item = dict(hotspot) if isinstance(hotspot, dict) else vars(hotspot)
        item["distance_km"] = distance_km
        nearby.append(item)

    nearby.sort(key=lambda h: h["distance_km"])
    if limit is not None and limit > 0:
        nearby = nearby[:limit]

    return nearby
