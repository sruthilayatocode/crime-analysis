"""
hotspot_service.py
==================
Core service for analyzing and aggregating verified crime hotspots directly from SQLite DB.
All data is queried dynamically from the database with zero static CSV/JSON files.
"""

from collections import Counter, defaultdict


def get_hotspots_from_db():
    """
    Aggregate verified HIGH-confidence crime coordinates from SQLite into hotspots.
    Queries the database directly. Zero caching, immediate response to updates.
    """
    try:
        from database import db
        from models.crime import Crime

        verified = (
            db.session.query(
                Crime.latitude,
                Crime.longitude,
                Crime.locality,
                Crime.district,
                Crime.crime_type,
                Crime.severity_score,
                Crime.risk_level,
            )
            .filter(
                Crime.location_confidence.in_(["HIGH", "high"]),
                Crime.latitude.isnot(None),
                Crime.longitude.isnot(None),
            )
            .all()
        )
    except Exception:
        return []

    groups = defaultdict(list)
    for lat, lon, locality, district, ctype, sev, risk in verified:
        groups[(round(float(lat), 6), round(float(lon), 6))].append({
            "locality": locality,
            "district": district,
            "crime_type": ctype,
            "severity_score": sev,
            "risk_level": risk,
        })

    hotspots = []
    for i, (key, members) in enumerate(sorted(groups.items()), start=1):
        lat, lon = key
        sev = [m["severity_score"] for m in members if m["severity_score"] is not None]
        weighted = sum(sev) / len(sev) if sev else 0.0
        risk_counts = Counter((m["risk_level"] or "Unknown").capitalize() for m in members)
        ctype = Counter(m["crime_type"] for m in members)
        dominant = ctype.most_common(1)[0][0] if ctype else "Unknown"

        hotspots.append({
            "hotspot_id": i,
            "latitude": float(lat),
            "longitude": float(lon),
            "location_name": (
                members[0]["locality"] or members[0]["district"] or "Unknown"
            ),
            "incident_count": len(members),
            "weighted_risk_score": round(weighted, 4),
            "dominant_crime_type": dominant,
            "critical_count": int(risk_counts.get("Critical", 0)),
            "high_count": int(risk_counts.get("High", 0)),
            "medium_count": int(risk_counts.get("Medium", 0)),
            "low_count": int(risk_counts.get("Low", 0)),
            "unknown_count": int(risk_counts.get("Unknown", 0)),
        })

    hotspots.sort(key=lambda h: (h["incident_count"], h["weighted_risk_score"]), reverse=True)
    return hotspots


def analyze_hotspots(crimes=None):
    """
    Analyze crime records and group them by location.
    If crimes is None, queries verified hotspots directly from the database.
    """
    if crimes is None:
        return get_hotspots_from_db()

    location_groups = defaultdict(list)
    for crime in crimes:
        location = crime.get("location") or crime.get("locality") or "Unknown"
        location_groups[location].append(crime)

    hotspots = []
    for location, crime_records in location_groups.items():
        crime_count = len(crime_records)
        average_latitude = sum(
            float(crime.get("latitude", 0) or 0) for crime in crime_records
        ) / crime_count
        average_longitude = sum(
            float(crime.get("longitude", 0) or 0) for crime in crime_records
        ) / crime_count

        if crime_count >= 5:
            risk_level = "High"
        elif crime_count >= 3:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        hotspots.append({
            "location": location,
            "crime_count": crime_count,
            "average_latitude": round(average_latitude, 6),
            "average_longitude": round(average_longitude, 6),
            "risk_level": risk_level,
        })

    hotspots.sort(key=lambda h: h["crime_count"], reverse=True)
    return hotspots