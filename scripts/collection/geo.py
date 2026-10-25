"""Geocoding: locality gazetteer ONLY — coordinates are never fabricated.

Uses a curated gazetteer of Vellore-region localities (city/district places
from scope.py + a few extra anchors). If a locality is not in the gazetteer,
geocoding_status stays 'missing_locality' and lat/lon stay empty.
"""
from __future__ import annotations
import csv
from pathlib import Path

from scripts.collection.config import PROJECT_ROOT

# Curated gazetteer: locality -> (lat, lon, precision)
# Coordinates are town centroids from public knowledge; precision reflects
# that an incident is placed at the TOWN level, not the exact spot.
_GAZETTEER = {
    "vellore": (12.9165, 79.1325, "town"),
    "katpadi": (12.9698, 79.1376, "town"),
    "gudiyatham": (12.9459, 78.8736, "town"),
    "pernambut": (12.9762, 78.7169, "town"),
    "ambur": (12.7904, 78.7167, "town"),
    "vaniyambadi": (12.6819, 78.6199, "town"),
    "tirupattur": (12.4950, 78.5686, "town"),
    "tirupathur": (12.4950, 78.5686, "town"),
    "jolarpet": (12.5661, 78.5747, "town"),
    "natrampalli": (12.5333, 78.4833, "town"),
    "alangayam": (12.6310, 78.6340, "town"),
    "arcot": (12.9006, 79.3258, "town"),
    "ranipet": (12.9300, 79.2900, "town"),
    "walajapet": (12.9227, 79.3662, "town"),
    "sholingur": (13.1176, 79.4258, "town"),
    "sholinghur": (13.1176, 79.4258, "town"),
    "arakkonam": (13.0778, 79.6700, "town"),
    "melvisharam": (12.9333, 79.2667, "town"),
    "anaicut": (12.8833, 79.2167, "village"),
    "pallikonda": (12.9000, 78.9500, "town"),
    "gudiyattam": (12.9459, 78.8736, "town"),   # spelling variant
    "thiruvalam": (12.9833, 79.3333, "village"),
    "kaniyambadi": (12.8833, 79.0833, "town"),
    "bagayam": (12.9333, 79.1000, "suburb"),
    "thorapadi": (12.9000, 79.1167, "suburb"),
    "sathuvachari": (12.9333, 79.1500, "suburb"),
    " cleansenpakkam": None,  # guard: never match junk
}
del _GAZETTEER[" cleansenpakkam"]


def geocode(locality: str):
    """-> (lat, lon, status). Never guesses."""
    key = (locality or "").strip().lower()
    if not key:
        return "", "", "missing_locality"
    hit = _GAZETTEER.get(key)
    if not hit:
        # try suffix-stripped ("vellore fort" -> "vellore")
        for k, v in _GAZETTEER.items():
            if k and key.startswith(k + " "):
                hit = v
                break
    if not hit:
        return "", "", "unmapped_locality"
    lat, lon, prec = hit
    return lat, lon, f"geocoded_{prec}"


def geocode_incidents(incidents: list) -> dict:
    counts = {"geocoded": 0, "unmapped": 0, "missing": 0}
    for inc in incidents:
        lat, lon, status = geocode(inc.get("locality"))
        inc["latitude"], inc["longitude"] = lat, lon
        inc["geocoding_status"] = status
        if lat:
            counts["geocoded"] += 1
        elif status == "missing_locality":
            counts["missing"] += 1
        else:
            counts["unmapped"] += 1
    return counts
