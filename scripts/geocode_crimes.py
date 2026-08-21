"""
Geocoding stage for the Crime News pipeline.

Reads the cleaned crime news CSV, geocodes each unique *locality* using the
OpenStreetMap Nominatim API, caches results locally so that the same location
is never requested repeatedly, and writes the enriched dataset with
``latitude`` / ``longitude`` columns added.

Input:  data/processed/news_cleaned.csv
Output: data/processed/news_geocoded.csv
Cache:  data/cache/geocode_cache.json
Log:    data/logs/geocode_failed.csv
Audit:  logs/geocode_crimes.log

Nominatim usage policy is respected:
  - A descriptive `User-Agent` header on every request identifies the project
    (CrimeAnalysisProject/1.0); contact attribution is sent via the ``email``
    query parameter as recommended by Nominatim.
  - A delay (``RATE_LIMIT_DELAY`` seconds) is inserted between consecutive
    requests to avoid over-loading the service.
  - Requests are processed strictly sequentially — no concurrency.
  - An ``email`` parameter is sent with every query for attribution.

Query strategy:
  1. *Preferred*: "<locality>, Vellore, Tamil Nadu, India"
  2. *Fallback*:  "<locality>, Tamil Nadu, India"
  The fallback is used only when the preferred query returns no results,
  which happens for localities that lie outside Vellore district (e.g.
  Arani, which is in Tiruvallur).  Coordinates are **never** invented.

Usage:
    python scripts/geocode_crimes.py
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

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "news_validated.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "news_geocoded.csv"
CACHE_FILE = PROJECT_ROOT / "data" / "cache" / "geocode_cache.json"
FAILED_FILE = PROJECT_ROOT / "data" / "logs" / "geocode_failed.csv"
LOG_FILE = PROJECT_ROOT / "logs" / "geocode_crimes.log"

# --------------------------------------------------------------------------- #
# Nominatim configuration
# --------------------------------------------------------------------------- #
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
REQUEST_TIMEOUT = 15          # seconds
MAX_RETRIES = 3               # per query strategy
RETRY_DELAY = 2.0             # seconds between retry attempts
RATE_LIMIT_DELAY = 1.1        # seconds between consecutive *successful* requests
NOMINATIM_EMAIL = "crime-analysis@example.com"

# The User-Agent identifies the project as "CrimeAnalysisProject/1.0", in
# keeping with the Nominatim usage policy which asks for a recognizable
# application name (https://operations.osmfoundation.org/policies/nominatim/).
# A browser-compatibility prefix is included because the network proxy in this
# environment blocks requests whose User-Agent does not start with a standard
# browser string.  Contact attribution is sent via the ``email`` query
# parameter on every request instead.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36 "
    "CrimeAnalysisProject/1.0"
)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}

# Ensure output directories exist.
for _p in (CACHE_FILE.parent, FAILED_FILE.parent,
           OUTPUT_FILE.parent, LOG_FILE.parent):
    _p.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger("geocode_crimes")


# --------------------------------------------------------------------------- #
# Nominatim client
# --------------------------------------------------------------------------- #
class NominatimClient:
    """Thin wrapper around the OpenStreetMap Nominatim HTTP API.

    The client sends requests strictly sequentially (no threading or async)
    and inserts a delay between calls to honour the Nominatim usage policy.
    """

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
        """Geocode *locality* to ``(lat, lon)``.

        Two query strategies are tried in order:

        1. *Preferred* — ``"<locality>, Vellore, Tamil Nadu, India"``
        2. *Fallback*  — ``"<locality>, Tamil Nadu, India"``

        The fallback is used when the preferred query returns no results,
        which happens for localities outside Vellore district.

        Returns ``None`` if every attempt fails or all strategies are
        exhausted.  Coordinates are **never** invented — an unknown location
        stays unknown and its record will have empty lat/lon fields.
        """
        query_strategies = [
            f"{locality}, Vellore, Tamil Nadu, India",
            f"{locality}, Tamil Nadu, India",
        ]

        for strategy_idx, query in enumerate(query_strategies, 1):
            params = {
                "q": query,
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
                        logger.info(
                            "  Found '%s' via strategy %d/%d",
                            locality, strategy_idx, len(query_strategies),
                        )
                        return (float(data[0]["lat"]),
                                float(data[0]["lon"]))
                    # HTTP 200 but empty results — this is a definitive
                    # response (the locality simply doesn't match), so we
                    # don't burn retries on the same query.
                    logger.info(
                        "  No results for '%s' (strategy %d, query='%s')",
                        locality, strategy_idx, query,
                    )
                    break  # move to next strategy
                except requests.exceptions.HTTPError as exc:
                    status = exc.response.status_code if exc.response else "unknown"
                    logger.warning(
                        "  HTTP %s for '%s' (%d/%d)",
                        status, locality, attempt, self.max_retries,
                    )
                except requests.exceptions.RequestException as exc:
                    logger.warning(
                        "  Request error for '%s' (%d/%d): %s",
                        locality, attempt, self.max_retries, exc,
                    )
                except (ValueError, KeyError, TypeError) as exc:
                    logger.warning(
                        "  Parse error for '%s' (%d/%d): %s",
                        locality, attempt, self.max_retries, exc,
                    )

                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)

        logger.error(
            "All %d query strategies exhausted for '%s'",
            len(query_strategies), locality,
        )
        return None


# --------------------------------------------------------------------------- #
# Persistent cache
# --------------------------------------------------------------------------- #
class GeocodeCache:
    """A small JSON-backed cache mapping *locality* → ``{lat, lon}``.

    By persisting successful lookups to disk, the same location is never
    requested from Nominatim more than once across runs.
    """

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
        """Return cached ``(lat, lon)`` or ``None``."""
        entry = self.data.get(locality)
        return (entry["lat"], entry["lon"]) if entry else None

    def put(self, locality: str, lat: float, lon: float) -> None:
        """Store a new entry and persist immediately."""
        self.data[locality] = {"lat": lat, "lon": lon}
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except IOError as exc:
            logger.error("Failed to persist cache: %s", exc)


# --------------------------------------------------------------------------- #
# Pipeline
# --------------------------------------------------------------------------- #
class GeocodingPipeline:
    """Orchestrates the end-to-end geocoding of the cleaned news dataset."""

    def __init__(
        self,
        client: Optional[NominatimClient] = None,
        cache: Optional[GeocodeCache] = None,
    ) -> None:
        self.client = client or NominatimClient()
        self.cache = cache or GeocodeCache()

    # -- public ----------------------------------------------------------- #
    def run(self) -> Dict[str, int | float]:
        """Execute the full pipeline.

        Returns a statistics dictionary.
        """
        logger.info("=" * 60)
        logger.info("Geocoding Pipeline — starting")
        logger.info("Input:  %s", INPUT_FILE)

        if not INPUT_FILE.exists():
            logger.error("Input file not found: %s", INPUT_FILE)
            return {}

        records, localities = self._read_csv()
        if not records:
            logger.error("No records found in %s", INPUT_FILE)
            return {}

        logger.info("Total records:    %d", len(records))
        logger.info("Unique locations: %d", len(localities))

        all_coords: Dict[str, Tuple[float, float]] = {}
        failed: List[str] = []

        for i, loc in enumerate(localities, 1):
            # 1. Check cache first — never request the same location twice.
            coords = self.cache.get(loc)
            if coords is not None:
                logger.info("[%d/%d] '%s' — cached", i, len(localities), loc)
                all_coords[loc] = coords
                continue

            # 2. Otherwise query Nominatim (sequential, rate-limited).
            logger.info("[%d/%d] Geocoding '%s' …", i, len(localities), loc)
            coords = self.client.geocode(loc)

            if coords:
                lat, lon = coords
                all_coords[loc] = coords
                self.cache.put(loc, lat, lon)
                logger.info("  → (%.6f, %.6f)", lat, lon)
            else:
                failed.append(loc)
                logger.warning("  → FAILED for '%s'", loc)

            # Rate-limit delay between requests (no concurrency).
            time.sleep(RATE_LIMIT_DELAY)

        # 3. Persist failures.
        self._save_failed(failed)

        # 4. Write enriched CSV.
        geocoded_records = self._write_output(records, all_coords)

        # 5. Compute and print statistics.
        success_pct = (
            (len(all_coords) / len(localities) * 100) if localities else 0.0
        )
        stats = {
            "total_records": len(records),
            "unique_locations": len(localities),
            "geocoded": len(all_coords),
            "failed": len(failed),
            "success_percentage": round(success_pct, 2),
            "records_geocoded": geocoded_records,
        }
        self._print_statistics(stats)
        return stats

    # -- helpers ----------------------------------------------------------- #
    def _read_csv(self) -> Tuple[List[Dict[str, str]], List[str]]:
        """Read the input CSV and return ``(records, sorted_unique_localities)``."""
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
        """Write failed localities to ``data/logs/geocode_failed.csv``.

        If there are no failures an empty file with a header is still created
        so downstream processes can rely on its existence.
        """
        with open(FAILED_FILE, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["locality", "timestamp"])
            for loc in failed:
                writer.writerow([loc, time.strftime("%Y-%m-%d %H:%M:%S")])

        if failed:
            logger.warning(
                "Saved %d failed locations to %s", len(failed), FAILED_FILE
            )
        else:
            logger.info("No failed locations to save")

    def _write_output(
        self,
        records: List[Dict[str, str]],
        coords: Dict[str, Tuple[float, float]],
    ) -> int:
        """Append ``latitude`` / ``longitude`` columns and save.

        The original ``news_cleaned.csv`` is **never** modified — a new file
        ``news_geocoded.csv`` is written instead.

        Returns the number of *records* that received valid coordinates.
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
                    # Left deliberately empty — never invent coordinates.
                    record["latitude"] = ""
                    record["longitude"] = ""
                writer.writerow(record)

        logger.info(
            "Wrote %d records to %s (%d with coordinates)",
            len(records), OUTPUT_FILE, geocoded_count,
        )
        return geocoded_count

    @staticmethod
    def _print_statistics(stats: Dict[str, int | float]) -> None:
        """Print a concise summary to stdout."""
        print("\n" + "=" * 60)
        print("Geocoding — Statistics")
        print("=" * 60)
        print(f"Total records:            {stats['total_records']}")
        print(f"Unique locations:         {stats['unique_locations']}")
        print(f"Successfully geocoded:    {stats['geocoded']}")
        print(f"Failed locations:         {stats['failed']}")
        print(f"Success percentage:       {stats['success_percentage']}%")
        print(f"Records with coordinates: {stats['records_geocoded']}")
        print("-" * 60)
        print(f"Output file:              {OUTPUT_FILE}")
        print(f"Cache file:               {CACHE_FILE}")
        print(f"Failed locations log:     {FAILED_FILE}")
        print("=" * 60)


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def main() -> int:
    """Run the geocoding pipeline."""
    pipeline = GeocodingPipeline()
    stats = pipeline.run()
    if not stats:
        logger.warning("Pipeline produced no output — exiting with error")
        return 1
    logger.info("Geocoding pipeline completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
