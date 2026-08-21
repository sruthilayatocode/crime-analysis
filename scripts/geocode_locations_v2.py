#!/usr/bin/env python
"""
Strict location extraction and geocoding for validated Vellore crime news.

This pass does not modify the validated dataset. It writes a new geocoded v2
CSV and a review file for records whose incident location cannot be trusted.
"""

from __future__ import annotations

import csv
import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "news_validated.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "news_geocoded_v2.csv"
REVIEW_FILE = PROJECT_ROOT / "data" / "logs" / "location_review.csv"
CACHE_FILE = PROJECT_ROOT / "data" / "cache" / "geocode_cache_v2.json"
LOG_FILE = PROJECT_ROOT / "logs" / "geocode_locations_v2.log"

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
REQUEST_TIMEOUT = 15
MAX_RETRIES = 3
RETRY_DELAY = 2.0
RATE_LIMIT_DELAY = 1.1
NOMINATIM_EMAIL = "crime-analysis@example.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36 "
        "CrimeAnalysisProject/1.0"
    ),
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}

for path in (OUTPUT_FILE.parent, REVIEW_FILE.parent, CACHE_FILE.parent, LOG_FILE.parent):
    path.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger("geocode_locations_v2")


EXACT_PATTERNS = [
    ("Katpadi railway station", r"\bkatpadi railway station\b"),
    ("Vellore Fort", r"\bvellore fort\b"),
    ("Vellore GH", r"\bvellore gh\b"),
    ("Pallikonda", r"\bpallikonda\b"),
    ("Katpadi", r"\bkatpadi\b"),
]

DISTRICT_ONLY_PATTERNS = [
    r"\bvellore district\b",
    r"\btamil nadu'?s vellore\b",
    r"\bin vellore\b",
    r"\bnear vellore\b",
]

AMBIGUOUS_CONTEXT_PATTERNS = [
    r"\bfrom vellore\b",
    r"\bvellore (?:man|woman|doctor|trio|women|lady|youth|sp|police|court|jail|prison)\b",
    r"\bcmc vellore\b",
    r"\bvellore central prison\b",
    r"\bvellore jail\b",
    r"\bvellore prison\b",
]

KNOWN_OUTSIDE_VELLORE_DISTRICT = {
    "arani",
    "ambur",
    "ranipet",
    "tirupattur",
    "tiruppattur",
}


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def combined_text(row: Dict[str, str]) -> str:
    return normalize_text("%s %s" % (row.get("title", ""), row.get("description", "")))


def load_cache() -> Dict[str, Dict[str, object]]:
    if not CACHE_FILE.exists():
        return {}
    try:
        with CACHE_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_cache(cache: Dict[str, Dict[str, object]]) -> None:
    with CACHE_FILE.open("w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, sort_keys=True)


def determine_location(row: Dict[str, str]) -> Tuple[str, str, str, str, str]:
    """Return locality, confidence, source, verified flag, review reason."""
    text = combined_text(row)
    text_l = text.lower()
    existing = normalize_text(row.get("locality", ""))

    if existing.lower() in KNOWN_OUTSIDE_VELLORE_DISTRICT:
        return "", "UNKNOWN", "", "False", "ambiguous_or_outside_vellore_district:%s" % existing
    for outside_name in sorted(KNOWN_OUTSIDE_VELLORE_DISTRICT, key=len, reverse=True):
        match = re.search(r"\b%s\b" % re.escape(outside_name), text_l)
        if match:
            source = text[max(0, match.start() - 60):match.end() + 60]
            return "", "UNKNOWN", normalize_text(source), "False", "ambiguous_or_outside_vellore_district:%s" % outside_name

    for locality, pattern in EXACT_PATTERNS:
        match = re.search(pattern, text_l)
        if match:
            source = text[max(0, match.start() - 60):match.end() + 60]
            return locality, "HIGH", normalize_text(source), "True", ""

    for pattern in AMBIGUOUS_CONTEXT_PATTERNS:
        match = re.search(pattern, text_l)
        if match:
            source = text[max(0, match.start() - 60):match.end() + 60]
            return "", "UNKNOWN", normalize_text(source), "False", "ambiguous_context"

    for pattern in DISTRICT_ONLY_PATTERNS:
        match = re.search(pattern, text_l)
        if match:
            source = text[max(0, match.start() - 60):match.end() + 60]
            return "", "LOW", normalize_text(source), "False", "district_or_broad_location_only"

    if "vellore" in text_l:
        return "", "LOW", "Vellore mentioned without exact incident locality", "False", "district_or_broad_location_only"

    return "", "UNKNOWN", "", "False", "locality_not_extracted"


def is_vellore_district_result(locality: str, item: Dict[str, object]) -> Tuple[bool, str]:
    display = str(item.get("display_name", ""))
    address = item.get("address") if isinstance(item.get("address"), dict) else {}
    address_text = " ".join(str(v) for v in address.values()).lower()
    display_l = display.lower()
    locality_l = locality.lower()
    searchable = "%s %s" % (display_l, address_text)

    if locality_l in KNOWN_OUTSIDE_VELLORE_DISTRICT:
        return False, "known_outside_vellore_district"
    if "tamil nadu" not in display_l and "tamil nadu" not in address_text:
        return False, "outside_tamil_nadu"
    if "vellore" not in display_l and "vellore" not in address_text:
        return False, "nominatim_result_not_in_vellore_district"
    if locality_l == "vellore gh":
        if not re.search(r"\b(gh|government hospital|general hospital)\b", searchable):
            return False, "nominatim_result_too_broad_for_vellore_gh"
    elif locality_l == "katpadi railway station":
        if "katpadi" not in searchable or not re.search(r"\b(railway|station|junction)\b", searchable):
            return False, "nominatim_result_too_broad_for_katpadi_railway_station"
    else:
        tokens = [t for t in re.findall(r"[a-z]+", locality_l) if t not in {"vellore", "district"}]
        if tokens and not all(t in searchable for t in tokens):
            return False, "nominatim_result_does_not_match_locality"
    return True, display


def geocode_locality(locality: str, cache: Dict[str, Dict[str, object]]) -> Tuple[Optional[float], Optional[float], bool, str]:
    cache_key = "%s, Vellore district, Tamil Nadu, India" % locality
    cached = cache.get(cache_key)
    if cached:
        cached_item = {
            "display_name": cached.get("source", ""),
            "address": {"state": "Tamil Nadu", "district": "Vellore"},
        }
        cached_ok, cached_reason = is_vellore_district_result(locality, cached_item)
        if not cached_ok:
            cached["latitude"] = None
            cached["longitude"] = None
            cached["verified"] = False
            cached["source"] = cached_reason
            save_cache(cache)
            return None, None, False, cached_reason
        if cached.get("latitude") is None or cached.get("longitude") is None:
            return None, None, bool(cached["verified"]), str(cached["source"])
        return (
            float(cached["latitude"]),
            float(cached["longitude"]),
            bool(cached["verified"]),
            str(cached["source"]),
        )

    params = {
        "q": cache_key,
        "format": "json",
        "limit": 3,
        "addressdetails": 1,
        "email": NOMINATIM_EMAIL,
    }

    last_reason = "geocoding_failed"
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(
                NOMINATIM_URL, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            for item in data:
                ok, reason = is_vellore_district_result(locality, item)
                if not ok:
                    last_reason = reason
                    continue
                lat = float(item["lat"])
                lon = float(item["lon"])
                cache[cache_key] = {
                    "latitude": lat,
                    "longitude": lon,
                    "verified": True,
                    "source": reason,
                }
                save_cache(cache)
                return lat, lon, True, reason
            break
        except requests.exceptions.RequestException as exc:
            last_reason = "request_error:%s" % exc
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
        except (TypeError, ValueError, KeyError) as exc:
            last_reason = "parse_error:%s" % exc
            break

    cache[cache_key] = {
        "latitude": None,
        "longitude": None,
        "verified": False,
        "source": last_reason,
    }
    save_cache(cache)
    return None, None, False, last_reason


def main() -> int:
    logger.info("=" * 60)
    logger.info("Strict location geocoding v2 - starting")
    logger.info("Input:  %s", INPUT_FILE)
    logger.info("Output: %s", OUTPUT_FILE)
    logger.info("Review: %s", REVIEW_FILE)

    with INPUT_FILE.open("r", encoding="utf-8", newline="") as f:
        records = list(csv.DictReader(f))

    cache = load_cache()
    geocoded: Dict[str, Tuple[Optional[float], Optional[float], bool, str]] = {}
    output_rows: List[Dict[str, str]] = []
    review_rows: List[Dict[str, str]] = []
    rejected_coordinates = 0

    for row in records:
        locality, confidence, source, verified, review_reason = determine_location(row)
        lat: Optional[float] = None
        lon: Optional[float] = None

        if locality:
            if locality not in geocoded:
                logger.info("Geocoding '%s' with Vellore district qualifier", locality)
                geocoded[locality] = geocode_locality(locality, cache)
                time.sleep(RATE_LIMIT_DELAY)
            lat, lon, coord_verified, geo_source = geocoded[locality]
            if coord_verified and lat is not None and lon is not None:
                verified = "True"
                source = source or geo_source
            else:
                verified = "False"
                review_reason = geo_source or "geocoding_failed"
                rejected_coordinates += 1

        out = dict(row)
        out["locality"] = locality
        out["location_confidence"] = confidence
        out["location_source"] = source
        out["location_verified"] = verified
        out["latitude"] = "" if lat is None else "%.6f" % lat
        out["longitude"] = "" if lon is None else "%.6f" % lon
        output_rows.append(out)

        if review_reason or not locality or not out["latitude"] or verified != "True":
            review = {
                "article_id": row.get("article_id", ""),
                "title": row.get("title", ""),
                "original_locality": row.get("locality", ""),
                "resolved_locality": locality,
                "location_confidence": confidence,
                "location_verified": verified,
                "review_reason": review_reason or "coordinates_not_verified",
                "location_source": source,
                "latitude": out["latitude"],
                "longitude": out["longitude"],
            }
            review_rows.append(review)

    fieldnames = list(records[0].keys()) if records else []
    for col in ("location_confidence", "location_source", "location_verified", "latitude", "longitude"):
        if col not in fieldnames:
            fieldnames.append(col)

    with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(output_rows)

    review_fields = [
        "article_id", "title", "original_locality", "resolved_locality",
        "location_confidence", "location_verified", "review_reason",
        "location_source", "latitude", "longitude",
    ]
    with REVIEW_FILE.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=review_fields)
        writer.writeheader()
        writer.writerows(review_rows)

    total = len(output_rows)
    unique_localities = sorted({r["locality"] for r in output_rows if r["locality"]})
    exact_records = sum(1 for r in output_rows if r["location_confidence"] == "HIGH")
    district_only = sum(1 for r in output_rows if r["location_confidence"] == "LOW")
    ambiguous = sum(1 for r in output_rows if r["location_confidence"] == "UNKNOWN")
    verified_coords = sum(1 for r in output_rows if r["latitude"] and r["longitude"] and r["location_verified"] == "True")

    print("=" * 60)
    print("Location Geocoding v2 Results")
    print("=" * 60)
    print("Total records:          %d" % total)
    print("Unique localities:      %d (%s)" % (len(unique_localities), ", ".join(unique_localities) or "none"))
    print("Exact-locality records: %d" % exact_records)
    print("District-only records:  %d" % district_only)
    print("Ambiguous records:      %d" % ambiguous)
    print("Verified coordinates:   %d" % verified_coords)
    print("Rejected coordinates:   %d" % rejected_coordinates)
    print("Output file:            %s" % OUTPUT_FILE)
    print("Review file:            %s" % REVIEW_FILE)
    print("=" * 60)

    logger.info("Strict location geocoding v2 completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
