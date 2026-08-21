"""
Fetch Reference Data from OpenStreetMap Overpass API.

This script fetches real geographic reference data for Vellore District
from OpenStreetMap using the Overpass API. It downloads:

    1. All localities (places) inside Vellore District
    2. All police stations inside Vellore District

The data is saved as CSV files in the ``data/reference/`` directory.

Features:
    - Retry handling with exponential backoff
    - Timeout handling for API requests
    - Progress logging at each step
    - Rate limiting between API calls
    - Deduplication of fetched records
    - CSV export with consistent column ordering

Usage:
    python scripts/reference_builder/fetch_reference_data.py

Author: Crime Analysis Project
License: MIT
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Resolve project root from this file's location:
#   scripts/reference_builder/fetch_reference_data.py -> project root
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR: Path = PROJECT_ROOT / "data" / "reference"
LOG_DIR: Path = PROJECT_ROOT / "logs"

# Overpass API settings
OVERPASS_URL: str = "https://overpass-api.de/api/interpreter"
AREA_NAME: str = "Vellore"

# Request settings
DEFAULT_TIMEOUT: int = 60          # seconds
MAX_RETRIES: int = 3
RETRY_DELAY: float = 5.0            # seconds between retries
RATE_LIMIT_DELAY: float = 2.0      # seconds between successful requests

# ---------------------------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------------------------

LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            LOG_DIR / "fetch_reference_data.log", encoding="utf-8"
        ),
    ],
)
logger = logging.getLogger("fetch_reference_data")


# ---------------------------------------------------------------------------
# Overpass API Client
# ---------------------------------------------------------------------------

class OverpassAPIClient:
    """Client for interacting with the Overpass API.

    Handles HTTP requests to the Overpass API with retry logic,
    timeout handling, and rate limiting.

    Attributes:
        url: Overpass API endpoint URL.
        timeout: Request timeout in seconds.
        max_retries: Maximum number of retry attempts.
        retry_delay: Base delay between retry attempts in seconds.
        rate_limit_delay: Delay between successful requests in seconds.
        session: Persistent ``requests.Session`` for connection pooling.
    """

    def __init__(
        self,
        url: str = OVERPASS_URL,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        retry_delay: float = RETRY_DELAY,
        rate_limit_delay: float = RATE_LIMIT_DELAY,
    ) -> None:
        """Initialize the Overpass API client.

        Args:
            url: Overpass API endpoint URL.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retry attempts.
            retry_delay: Base delay between retry attempts in seconds.
            rate_limit_delay: Delay between successful requests in seconds.
        """
        self.url = url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()
        logger.info(
            "OverpassAPIClient initialized (timeout=%ds, retries=%d, "
            "retry_delay=%.1fs, rate_limit=%.1fs)",
            timeout, max_retries, retry_delay, rate_limit_delay,
        )

    def fetch(self, query: str) -> Optional[Dict[str, Any]]:
        """Execute an Overpass QL query and return the JSON response.

        Implements retry logic with exponential backoff for transient
        errors (timeouts, connection errors, HTTP 429/5xx responses).

        Args:
            query: Overpass QL query string.

        Returns:
            Parsed JSON response as a dictionary, or ``None`` if all
            retry attempts fail.
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    "Sending Overpass API request (attempt %d/%d)",
                    attempt, self.max_retries,
                )
                response = self.session.post(
                    self.url,
                    data={"data": query},
                    timeout=self.timeout,
                    headers={
                        "User-Agent": (
                            "CrimeAnalysis/1.0 "
                            "(OpenStreetMap Data Fetcher)"
                        ),
                    },
                )
                response.raise_for_status()

                data: Dict[str, Any] = response.json()
                element_count = len(data.get("elements", []))
                logger.info(
                    "Overpass API returned %d elements", element_count
                )

                # Rate limiting between requests
                if self.rate_limit_delay > 0:
                    logger.debug(
                        "Rate limiting: sleeping %.1fs",
                        self.rate_limit_delay,
                    )
                    time.sleep(self.rate_limit_delay)

                return data

            except requests.exceptions.Timeout:
                logger.warning(
                    "Request timed out (attempt %d/%d)",
                    attempt, self.max_retries,
                )
            except requests.exceptions.ConnectionError as exc:
                logger.warning(
                    "Connection error (attempt %d/%d): %s",
                    attempt, self.max_retries, exc,
                )
            except requests.exceptions.HTTPError as exc:
                status_code = (
                    exc.response.status_code
                    if exc.response is not None
                    else "unknown"
                )
                logger.warning(
                    "HTTP error %s (attempt %d/%d)",
                    status_code, attempt, self.max_retries,
                )
                # Handle 429 Too Many Requests with longer backoff
                if status_code == 429:
                    wait_time = self.retry_delay * attempt * 2
                    logger.warning(
                        "Rate limited by server. Waiting %.1fs",
                        wait_time,
                    )
                    time.sleep(wait_time)
                    continue
            except requests.exceptions.RequestException as exc:
                logger.warning(
                    "Request failed (attempt %d/%d): %s",
                    attempt, self.max_retries, exc,
                )
            except ValueError as exc:
                logger.error(
                    "Failed to parse JSON response: %s", exc
                )
                return None

            # Retry delay with exponential backoff
            if attempt < self.max_retries:
                backoff = self.retry_delay * attempt
                logger.info(
                    "Retrying in %.1fs (exponential backoff)...", backoff
                )
                time.sleep(backoff)

        logger.error(
            "All %d retry attempts exhausted", self.max_retries
        )
        return None


# ---------------------------------------------------------------------------
# Reference Data Fetcher
# ---------------------------------------------------------------------------

class ReferenceDataFetcher:
    """Fetches reference data for Vellore District from OpenStreetMap.

    Builds Overpass QL queries to fetch localities and police stations
    within the Vellore District area, and parses the results into
    structured records.

    Attributes:
        client: :class:`OverpassAPIClient` instance for API communication.
        area_name: Name of the area to search within.
    """

    def __init__(
        self,
        client: OverpassAPIClient,
        area_name: str = AREA_NAME,
    ) -> None:
        """Initialize the reference data fetcher.

        Args:
            client: :class:`OverpassAPIClient` instance for API
                communication.
            area_name: Name of the area to search within
                (e.g., ``"Vellore"``).
        """
        self.client = client
        self.area_name = area_name
        logger.info(
            "ReferenceDataFetcher initialized for area: '%s'", area_name
        )

    def fetch_localities(self) -> List[Dict[str, Any]]:
        """Fetch all localities (places) in Vellore District.

        Queries the Overpass API for all nodes, ways, and relations
        with a ``place`` tag within the Vellore area.

        Returns:
            List of locality records, each with keys:
            ``name``, ``latitude``, ``longitude``, ``type``.
        """
        query = f"""
        [out:json][timeout:60];
        area[name="{self.area_name}"]->.searchArea;
        (
          node["place"](area.searchArea);
          way["place"](area.searchArea);
          relation["place"](area.searchArea);
        );
        out center;
        """
        logger.info("Fetching localities from Overpass API...")
        data = self.client.fetch(query)
        if not data:
            logger.error(
                "Failed to fetch localities from Overpass API"
            )
            return []

        elements = data.get("elements", [])
        logger.info(
            "Parsing %d locality elements...", len(elements)
        )
        localities = self._parse_localities(elements)
        logger.info("Parsed %d valid localities", len(localities))
        return localities

    def fetch_police_stations(self) -> List[Dict[str, Any]]:
        """Fetch all police stations in Vellore District.

        Queries the Overpass API for all nodes, ways, and relations
        with ``amenity=police`` within the Vellore area.

        Returns:
            List of police station records, each with keys:
            ``station_name``, ``latitude``, ``longitude``, ``address``.
        """
        query = f"""
        [out:json][timeout:60];
        area[name="{self.area_name}"]->.searchArea;
        (
          node["amenity"="police"](area.searchArea);
          way["amenity"="police"](area.searchArea);
          relation["amenity"="police"](area.searchArea);
        );
        out center;
        """
        logger.info("Fetching police stations from Overpass API...")
        data = self.client.fetch(query)
        if not data:
            logger.error(
                "Failed to fetch police stations from Overpass API"
            )
            return []

        elements = data.get("elements", [])
        logger.info(
            "Parsing %d police station elements...", len(elements)
        )
        stations = self._parse_police_stations(elements)
        logger.info("Parsed %d valid police stations", len(stations))
        return stations

    def _parse_localities(
        self, elements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Parse Overpass API elements into locality records.

        Args:
            elements: List of element dictionaries from the Overpass API.

        Returns:
            List of locality records with keys: ``name``,
            ``latitude``, ``longitude``, ``type``.
        """
        localities: List[Dict[str, Any]] = []
        skipped = 0

        for el in elements:
            tags = el.get("tags", {})
            name = tags.get("name")

            if not name:
                skipped += 1
                continue

            # Elements may have direct lat/lon or center lat/lon
            lat = el.get("lat") or el.get("center", {}).get("lat")
            lon = el.get("lon") or el.get("center", {}).get("lon")

            if lat is None or lon is None:
                skipped += 1
                continue

            place_type = tags.get("place", "unknown")
            localities.append(
                {
                    "name": name,
                    "latitude": round(float(lat), 6),
                    "longitude": round(float(lon), 6),
                    "type": place_type,
                }
            )

        if skipped > 0:
            logger.info(
                "Skipped %d elements (missing name or coordinates)",
                skipped,
            )

        return localities

    def _parse_police_stations(
        self, elements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Parse Overpass API elements into police station records.

        Args:
            elements: List of element dictionaries from the Overpass API.

        Returns:
            List of police station records with keys:
            ``station_name``, ``latitude``, ``longitude``, ``address``.
        """
        stations: List[Dict[str, Any]] = []
        skipped = 0

        for el in elements:
            tags = el.get("tags", {})

            # Try 'name', then 'operator', then default
            name = (
                tags.get("name")
                or tags.get("operator")
                or "Police Station"
            )

            lat = el.get("lat") or el.get("center", {}).get("lat")
            lon = el.get("lon") or el.get("center", {}).get("lon")

            if lat is None or lon is None:
                skipped += 1
                continue

            address = self._build_address(tags)

            stations.append(
                {
                    "station_name": name,
                    "latitude": round(float(lat), 6),
                    "longitude": round(float(lon), 6),
                    "address": address,
                }
            )

        if skipped > 0:
            logger.info(
                "Skipped %d elements (missing coordinates)", skipped
            )

        return stations

    @staticmethod
    def _build_address(tags: Dict[str, Any]) -> str:
        """Build a human-readable address from OSM address tags.

        Attempts to construct a full address from individual OSM
        address components (``addr:housenumber``, ``addr:street``,
        etc.). Falls back to ``addr:full`` or an empty string.

        Args:
            tags: OSM tags dictionary.

        Returns:
            Comma-separated address string, or empty string if no
            address tags are available.
        """
        # Try addr:full first
        if tags.get("addr:full"):
            return str(tags["addr:full"])

        # Build from components
        parts: List[str] = []
        for key in (
            "addr:housenumber",
            "addr:street",
            "addr:suburb",
            "addr:city",
            "addr:state",
        ):
            value = tags.get(key)
            if value:
                parts.append(str(value))

        if parts:
            return ", ".join(parts)

        # Fall back to description or empty string
        return tags.get("description", "")


# ---------------------------------------------------------------------------
# Data Processor
# ---------------------------------------------------------------------------

class DataProcessor:
    """Processes and exports reference data.

    Handles deduplication of records and CSV export with consistent
    column ordering.

    Attributes:
        output_dir: Directory where CSV files are saved.
    """

    def __init__(self, output_dir: Path = OUTPUT_DIR) -> None:
        """Initialize the data processor.

        Args:
            output_dir: Directory where CSV files are saved.
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(
            "DataProcessor initialized (output_dir=%s)", self.output_dir
        )

    def deduplicate(
        self,
        records: List[Dict[str, Any]],
        key_columns: List[str],
    ) -> List[Dict[str, Any]]:
        """Remove duplicate records based on key columns.

        Coordinates are rounded to 4 decimal places (approximately 11
        meters) before deduplication to merge nearby duplicates.

        Args:
            records: List of record dictionaries.
            key_columns: Column names to use for deduplication.

        Returns:
            Deduplicated list of records.
        """
        if not records:
            logger.info("No records to deduplicate")
            return []

        df = pd.DataFrame(records)
        initial_count = len(df)

        # Round coordinates for deduplication (~11 meters)
        for col in ("latitude", "longitude"):
            if col in df.columns:
                df[col] = df[col].round(4)

        df = df.drop_duplicates(subset=key_columns, keep="first")
        final_count = len(df)

        if initial_count != final_count:
            logger.info(
                "Deduplicated: %d -> %d records (removed %d duplicates)",
                initial_count,
                final_count,
                initial_count - final_count,
            )
        else:
            logger.info("No duplicates found (%d records)", final_count)

        return df.to_dict("records")

    def export_csv(
        self,
        records: List[Dict[str, Any]],
        filename: str,
        columns: Optional[List[str]] = None,
    ) -> Optional[Path]:
        """Export records to a CSV file.

        Args:
            records: List of record dictionaries.
            filename: Name of the output CSV file.
            columns: Optional list of column names to include, in the
                order they should appear in the CSV.

        Returns:
            Path to the exported CSV file, or ``None`` if no records
            were provided.
        """
        if not records:
            logger.warning(
                "No records to export for '%s'", filename
            )
            return None

        filepath = self.output_dir / filename
        df = pd.DataFrame(records)

        if columns:
            df = df[columns]

        df.to_csv(filepath, index=False, encoding="utf-8")
        logger.info(
            "Exported %d records to %s", len(df), filepath
        )
        return filepath


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def main() -> int:
    """Main entry point for the reference data fetcher.

    Fetches localities and police stations for Vellore District from
    OpenStreetMap and saves them as CSV files in
    ``data/reference/``.

    Returns:
        Exit code: ``0`` for success, ``1`` for failure.
    """
    logger.info("=" * 70)
    logger.info("Reference Data Fetcher - Starting")
    logger.info("Area: %s", AREA_NAME)
    logger.info("Output directory: %s", OUTPUT_DIR)
    logger.info("Overpass API: %s", OVERPASS_URL)
    logger.info("=" * 70)

    # Initialize components
    client = OverpassAPIClient()
    fetcher = ReferenceDataFetcher(client, area_name=AREA_NAME)
    processor = DataProcessor(output_dir=OUTPUT_DIR)

    # ------------------------------------------------------------------
    # Step 1: Fetch localities
    # ------------------------------------------------------------------
    logger.info("-" * 40)
    logger.info("STEP 1: Fetching localities")
    logger.info("-" * 40)
    localities = fetcher.fetch_localities()

    if localities:
        localities = processor.deduplicate(
            localities,
            key_columns=["name", "latitude", "longitude"],
        )
        processor.export_csv(
            localities,
            filename="vellore_localities.csv",
            columns=["name", "latitude", "longitude", "type"],
        )
    else:
        logger.warning(
            "No localities found - skipping CSV export"
        )

    # ------------------------------------------------------------------
    # Step 2: Fetch police stations
    # ------------------------------------------------------------------
    logger.info("-" * 40)
    logger.info("STEP 2: Fetching police stations")
    logger.info("-" * 40)
    stations = fetcher.fetch_police_stations()

    if stations:
        stations = processor.deduplicate(
            stations,
            key_columns=["station_name", "latitude", "longitude"],
        )
        processor.export_csv(
            stations,
            filename="vellore_police_stations.csv",
            columns=["station_name", "latitude", "longitude", "address"],
        )
    else:
        logger.warning(
            "No police stations found - skipping CSV export"
        )

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    logger.info("=" * 70)
    logger.info("Summary")
    logger.info("=" * 70)
    logger.info("Localities fetched:      %d", len(localities))
    logger.info("Police stations fetched: %d", len(stations))

    if localities or stations:
        logger.info(
            "Reference data fetch completed successfully"
        )
        return 0
    else:
        logger.error(
            "No data was fetched - check network connectivity "
            "and API availability"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())