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

        h = {
            "hotspot_id": i,
            "location": members[0]["locality"] or members[0]["district"] or "Unknown",
            "location_name": (
                members[0]["locality"] or members[0]["district"] or "Unknown"
            ),
            "crime_count": len(members),
            "incident_count": len(members),
            "latitude": float(lat),
            "longitude": float(lon),
            "centroid_latitude": float(lat),
            "centroid_longitude": float(lon),
            "average_latitude": float(lat),
            "average_longitude": float(lon),
            "weighted_risk_score": round(weighted, 4),
            "dominant_crime_type": dominant,
            "risk_level": "High" if len(members) >= 5 else ("Medium" if len(members) >= 3 else "Low"),
            "critical_count": int(risk_counts.get("Critical", 0)),
            "high_count": int(risk_counts.get("High", 0)),
            "medium_count": int(risk_counts.get("Medium", 0)),
            "low_count": int(risk_counts.get("Low", 0)),
            "unknown_count": int(risk_counts.get("Unknown", 0)),
        }
        hotspots.append(h)

    hotspots.sort(key=lambda h: (h["incident_count"], h["weighted_risk_score"]), reverse=True)
    return hotspots


import numpy as np
from collections import Counter, defaultdict
from sklearn.cluster import DBSCAN


def analyze_hotspots(crimes=None):
    """
    DBSCAN-based crime hotspot detection using Haversine distance metric.
    If crimes is None, queries all crime records with coordinates directly from SQLite.
    """
    if crimes is None:
        try:
            from database import db
            from models.crime import Crime

            crime_rows = (
                db.session.query(
                    Crime.id,
                    Crime.latitude,
                    Crime.longitude,
                    Crime.locality,
                    Crime.location_name,
                    Crime.district,
                    Crime.crime_type,
                    Crime.severity_score,
                    Crime.risk_level,
                )
                .filter(
                    Crime.latitude.isnot(None),
                    Crime.longitude.isnot(None),
                )
                .all()
            )
            crimes = [
                {
                    "id": row.id,
                    "latitude": row.latitude,
                    "longitude": row.longitude,
                    "locality": row.locality,
                    "location_name": row.location_name or row.locality or row.district,
                    "district": row.district,
                    "crime_type": row.crime_type,
                    "severity_score": row.severity_score,
                    "risk_level": row.risk_level,
                }
                for row in crime_rows
            ]
        except Exception:
            return []

    if not crimes:
        return []

    # Filter out missing, invalid, or out-of-range coordinates
    valid_records = []
    valid_coords = []
    for crime in crimes:
        lat_raw = crime.get("latitude")
        lng_raw = crime.get("longitude")
        if lat_raw is None or lng_raw is None or lat_raw == "" or lng_raw == "":
            continue
        try:
            lat = float(lat_raw)
            lng = float(lng_raw)
        except (TypeError, ValueError):
            continue

        if not (-90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0):
            continue

        valid_coords.append([lat, lng])
        valid_records.append(crime)

    if len(valid_records) < 2:
        return []

    # Epsilon = 1000 meters in radians (Earth radius = 6,371,000 meters)
    earth_radius = 6371000.0
    eps_rad = 1000.0 / earth_radius

    coords_rad = np.radians(valid_coords)
    db = DBSCAN(eps=eps_rad, min_samples=2, metric="haversine").fit(coords_rad)
    labels = db.labels_

    clusters = defaultdict(list)
    for idx, label in enumerate(labels):
        if label >= 0:  # Ignore noise (-1)
            clusters[label].append(valid_records[idx])

    if not clusters:
        return []

    hotspots = []
    # Sort clusters deterministically so largest/dense cluster gets cluster_id 0
    sorted_cluster_items = sorted(clusters.items(), key=lambda item: len(item[1]), reverse=True)

    for cluster_id, (orig_label, members) in enumerate(sorted_cluster_items):
        crime_count = len(members)
        latitudes = [float(m["latitude"]) for m in members]
        longitudes = [float(m["longitude"]) for m in members]

        centroid_lat = sum(latitudes) / crime_count
        centroid_lng = sum(longitudes) / crime_count

        if crime_count >= 5:
            risk_level = "High"
        elif crime_count >= 3:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        # Determine location name
        loc_names = [
            m.get("location_name") or m.get("locality") or m.get("location") or m.get("district")
            for m in members
            if m.get("location_name") or m.get("locality") or m.get("location") or m.get("district")
        ]
        location_name = Counter(loc_names).most_common(1)[0][0] if loc_names else "Vellore"

        ctypes = [m.get("crime_type") for m in members if m.get("crime_type")]
        dominant_type = Counter(ctypes).most_common(1)[0][0] if ctypes else "Theft"

        hotspots.append({
            "cluster_id": cluster_id,
            "hotspot_id": cluster_id + 1,
            "crime_count": crime_count,
            "incident_count": crime_count,
            "centroid_latitude": round(centroid_lat, 6),
            "centroid_longitude": round(centroid_lng, 6),
            "latitude": round(centroid_lat, 6),
            "longitude": round(centroid_lng, 6),
            "location": location_name,
            "location_name": location_name,
            "risk_level": risk_level,
            "dominant_crime_type": dominant_type,
        })

    hotspots.sort(key=lambda h: h["crime_count"], reverse=True)
    return hotspots


def get_hotspots_from_db():
    """
    Fetch hotspots directly from SQLite database using DBSCAN clustering.
    """
    return analyze_hotspots(None)
