"""
Crime News Geocoding Pipeline.

Reads cleaned crime dataset, extracts unique localities, geocodes
them using OpenStreetMap Nominatim API, and appends lat/lon columns.

Input:  data/processed/news_cleaned.csv
Output: data/processed/news_geocoded.csv
        data/cache/geocode_cache.json
        data/logs/geocode_failed.csv

Usage: python scripts/news_pipeline/geocode_articles.py
"""

from __future__ import annotations

import csv
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "news_cleaned.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "news_geocoded.csv"
CACHE_FILE = PROJECT_ROOT / "data" / "cache" / "geocode_cache.json"
FAILED_FILE = PROJECT_ROOT / "data" / "logs" / "geocode_failed.csv"
LOG_FILE = PROJECT_ROOT / "logs" / "geocode_articles.log"

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
REQUEST_TIMEOUT = 15
MAX_RETRIES = 3
RETRY_DELAY = 2.0
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36 "
    "CrimeAnalysisProject/1.0"
)
NOMINATIM_EMAIL = "crime-analysis@example.com"
RATE_LIMIT_DELAY = 1.1

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}

CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
FAILED_FILE.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger("geocode_articles")


class NominatimClient:
    """Client for OpenStreetMap Nominatim geocoding API."""

    def __init__(
        self,
        base_url: str = NOMINATIM_URL,
        timeout: int = REQUEST_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        retry_delay: float = RETRY_DELAY,
    ) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def geocode(self, locality: str) -> Optional[Tuple[float, float]]:
        """Geocode a locality to (lat, lon) using Nominatim.

        Uses context-aware query: 'Locality, Vellore, Tamil Nadu, India'
        """
        full_query = f"{locality}, Vellore, Tamil Nadu, India"
        params = {
            "q": full_query,
            "format": "json",
            "limit": 1,
            "addressdetails": 0,
            "email": NOMINATIM_EMAIL,
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(
                    self.base_url, params=params, timeout=self.timeout
                )
                resp.raise_for_status()
                data = resp.json()
                if data:
                    return (float(data[0]["lat"]), float(data[0]["lon"]))
                logger.warning("No results for '%s' (%d/%d)",
                               locality, attempt, self.max_retries)
            except requests.exceptions.HTTPError as exc:
                status = exc.response.status_code if exc.response else "unk"
                logger.warning("HTTP %s for '%s' (%d/%d)",
                               status, locality, attempt, self.max_retries)
            except requests.exceptions.RequestException as exc:
                logger.warning("Request failed '%s' (%d/%d): %s",
                               locality, attempt, self.max_retries, exc)
            except (ValueError, KeyError, TypeError) as exc:
                logger.warning("Parse error '%s' (%d/%d): %s",
                               locality, attempt, self.max_retries, exc)
            time.sleep(self.retry_delay)

        logger.error("All %d attempts failed for '%s'",
                     self.max_retries, locality)
        return None


class GeocodeCache:
    """Persistent cache for geocoding results."""

    def __init__(self, cache_file: Path = CACHE_FILE) -> None:
        self.cache_file = cache_file
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.data: Dict[str, Dict[str, float]] = self._load()

    def _load(self) -> Dict[str, Dict[str, float]]:
        if not self.cache_file.exists():
            return {}
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def get(self, locality: str) -> Optional[Tuple[float, float]]:
        entry = self.data.get(locality)
        return (entry["lat"], entry["lon"]) if entry else None

    def put(self, locality: str, lat: float, lon: float) -> None:
        self.data[locality] = {"lat": lat, "lon": lon}
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except IOError as exc:
            logger.error("Failed to save cache: %s", exc)


class GeocodingPipeline:
    """Geocodes localities from the cleaned crime dataset."""

    def __init__(
        self,
        client: Optional[NominatimClient] = None,
        cache: Optional[GeocodeCache] = None,
    ) -> None:
        self.client = client or NominatimClient()
        self.cache = cache or GeocodeCache()

    def run(self) -> int:
        """Run the geocoding pipeline.

        Returns number of successfully geocoded records.
        """
        logger.info("=" * 60)
        logger.info("Geocoding Pipeline - Starting")
        logger.info("Input: %s", INPUT_FILE)

        records, localities = self._read_csv()
        if not records:
            logger.error("No records found in %s", INPUT_FILE)
            return 0

        logger.info("Total articles: %d", len(records))
        logger.info("Unique localities: %d", len(localities))

        all_coords: Dict[str, Tuple[float, float]] = {}
        failed: List[str] = []
        response_times: List[float] = []

        for i, loc in enumerate(localities, 1):
            coords = self.cache.get(loc)
            if coords is not None:
                logger.info("[%d/%d] '%s' (cached)", i, len(localities), loc)
                all_coords[loc] = coords
                continue

            logger.info("[%d/%d] Geocoding '%s'...", i, len(localities), loc)
            start = time.time()
            coords = self.client.geocode(loc)
            elapsed = time.time() - start
            response_times.append(elapsed)

            if coords:
                all_coords[loc] = coords
                self.cache.put(loc, coords[0], coords[1])
                logger.info("  -> (%.6f, %.6f) in %.2fs",
                            coords[0], coords[1], elapsed)
            else:
                failed.append(loc)
                logger.warning("  -> FAILED for '%s'", loc)

            time.sleep(RATE_LIMIT_DELAY)

        self._save_failed(failed)
        geocoded_count = self._append_and_save(records, all_coords)

        avg_time = (
            sum(response_times) / len(response_times)
            if response_times else 0.0
        )
        self._print_statistics(
            total=len(localities),
            success=len(all_coords),
            failed=len(failed),
            avg_time=avg_time,
        )

        return geocoded_count

    def _read_csv(self) -> Tuple[List[Dict[str, str]], List[str]]:
        """Read CSV and extract unique localities.

        Returns:
            Tuple of (records, sorted unique localities).
        """
        if not INPUT_FILE.exists():
            logger.error("Input file not found: %s", INPUT_FILE)
            return [], []

        records: List[Dict[str, str]] = []
        locality_set: Set[str] = set()

        with open(INPUT_FILE, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
                loc = (row.get("locality", "") or "").strip()
                if loc:
                    locality_set.add(loc)

        return records, sorted(locality_set)

    def _save_failed(self, failed: List[str]) -> None:
        """Save failed geocoding locations to CSV.

        Args:
            failed: List of locality names that failed to geocode.
        """
        if not failed:
            logger.info("No failed locations to save")
            return

        with open(FAILED_FILE, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["locality", "timestamp"])
            for loc in failed:
                writer.writerow([loc, time.strftime("%Y-%m-%d %H:%M:%S")])
        logger.warning("Saved %d failed locations to %s",
                       len(failed), FAILED_FILE)

    def _append_and_save(
        self,
        records: List[Dict[str, str]],
        coords: Dict[str, Tuple[float, float]],
    ) -> int:
        """Append latitude/longitude columns and save output CSV.

        Args:
            records: List of input records (modified in place).
            coords: Mapping of locality to (lat, lon) coordinates.

        Returns:
            Number of records with valid coordinates.
        """
        if not records:
            return 0

        fieldnames = list(records[0].keys())
        for col in ("latitude", "longitude"):
            if col not in fieldnames:
                fieldnames.append(col)

        geocoded_count = 0
        with open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for record in records:
                loc = (record.get("locality", "") or "").strip()
                c = coords.get(loc)
                if c:
                    record["latitude"] = f"{c[0]:.6f}"
                    record["longitude"] = f"{c[1]:.6f}"
                    geocoded_count += 1
                else:
                    record["latitude"] = ""
                    record["longitude"] = ""
                writer.writerow(record)

        logger.info("Saved %d records to %s (%d geocoded)",
                     len(records), OUTPUT_FILE, geocoded_count)
        return geocoded_count

    @staticmethod
    def _print_statistics(
        total: int,
        success: int,
        failed: int,
        avg_time: float,
    ) -> None:
        """Print pipeline statistics."""
        print("\n" + "=" * 60)
        print("Statistics")
        print("=" * 60)
        print(f"Total locations:          {total}")
        print(f"Successfully geocoded:    {success}")
        print(f"Failed:                   {failed}")
        print(f"Average response time:    {avg_time:.2f}s")
        print(f"Output file:              {OUTPUT_FILE}")
        print(f"Failed locations log:     {FAILED_FILE}")
        print("=" * 60)


def main() -> int:
    """Main entry point."""
    pipeline = GeocodingPipeline()
    count = pipeline.run()
    if count > 0:
        logger.info("Geocoding pipeline completed successfully")
        return 0
    logger.warning("No records were geocoded")
    return 1


if __name__ == "__main__":
    sys.exit(main())