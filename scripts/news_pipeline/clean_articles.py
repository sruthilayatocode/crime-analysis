"""
Crime News Data Processing Pipeline.

This script reads raw scraped news articles, removes duplicates and
non-crime articles, standardizes crime types, and exports a clean
crime dataset.

Input:
    data/raw/news/articles.json (or crime_articles.json if present)

Output:
    data/processed/news_cleaned.csv
    data/processed/news_cleaned.json

Usage:
    python scripts/news_pipeline/clean_articles.py

Author: Crime Analysis Project
License: MIT
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
RAW_NEWS_DIR: Path = PROJECT_ROOT / "data" / "raw" / "news"
PROCESSED_DIR: Path = PROJECT_ROOT / "data" / "processed"
OUTPUT_JSON: Path = PROCESSED_DIR / "news_cleaned.json"
OUTPUT_CSV: Path = PROCESSED_DIR / "news_cleaned.csv"
LOG_FILE: Path = PROJECT_ROOT / "logs" / "clean_articles.log"

# ---------------------------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------------------------

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger("clean_articles")


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class CleanedArticle:
    """Represents a cleaned crime article.

    Attributes:
        article_id: Unique hash-based ID for the article.
        title: Article headline.
        published_date: Publication date.
        source: News source name.
        url: Article URL.
        crime_type: Standardized crime type.
        district: District name.
        locality: Detected locality.
        description: Cleaned article text.
    """

    article_id: str
    title: str
    published_date: str
    source: str
    url: str
    crime_type: str
    district: str
    locality: str
    description: str


# ---------------------------------------------------------------------------
# Crime Type Standardizer
# ---------------------------------------------------------------------------

class CrimeTypeStandardizer:
    """Standardizes crime type labels.

    Maps various crime-related keywords to a canonical set of
    crime types.
    """

    # Standardized crime type mapping
    CRIME_TYPE_KEYWORDS: Dict[str, List[str]] = {
        "Murder": [
            "murder", "homicide", "killed", "death", "slain",
        ],
        "Theft": [
            "theft", "stolen", "burglary", "snatching", "snatcher",
        ],
        "Robbery": [
            "robbery", "robber", "dacoity", "heist",
        ],
        "Assault": [
            "assault", "attack", "beaten", "injured", "caned",
            "violence", "violent",
        ],
        "Sexual Assault": [
            "sexual assault", "rape", "molest", "harassment",
        ],
        "Cyber Crime": [
            "cyber crime", "cyber", "online scam", "digital arrest",
            "phishing", "hacking", "online fraud",
        ],
        "Drugs": [
            "drugs", "drug", "narcotic", "ganja", "cough syrup",
            "meth", "smuggling",
        ],
        "Kidnapping": [
            "kidnapping", "kidnap", "abduction", "abducted",
        ],
        "Extortion": [
            "extortion", "blackmail", "threat", "threatening",
        ],
        "Fraud": [
            "fraud", "scam", "cheated", "fake", "counterfeit",
            "racket",
        ],
        "Corruption": [
            "corruption", "bribery", "bribe",
        ],
        "Dowry": [
            "dowry", "dowry death",
        ],
        "Other": [],
    }

    @classmethod
    def standardize(cls, crime_type: str, text: str = "") -> str:
        """Standardize a crime type label.

        Takes a detected crime type and optionally article text,
        and maps it to a canonical crime type label.

        Args:
            crime_type: Detected crime type (e.g., 'Unknown').
            text: Article text used for keyword re-detection.

        Returns:
            Standardized crime type string.
        """
        # If crime_type is already a standard label, use it
        known_types = set(cls.CRIME_TYPE_KEYWORDS.keys())
        if crime_type in known_types:
            return crime_type

        # Otherwise, re-detect from text if provided
        if text:
            text_lower = text.lower()
            for std_type, keywords in cls.CRIME_TYPE_KEYWORDS.items():
                for keyword in keywords:
                    if keyword.lower() in text_lower:
                        return std_type

        return "Other"


# ---------------------------------------------------------------------------
# Data Cleaner (Core pipeline)
# ---------------------------------------------------------------------------

class NewsCleaner:
    """Processes raw news articles into a clean crime dataset.

    Attributes:
        raw_dir: Directory containing raw news files.
        processed_dir: Directory for output files.
        output_json: Path to the output JSON file.
        output_csv: Path to the output CSV file.
    """

    # Required crime keywords for filtering (same as scraper)
    CRIME_FILTER_KEYWORDS: List[str] = [
        "murder", "theft", "robbery", "assault", "rape",
        "police", "arrest", "fir", "cyber crime", "drugs",
        "smuggling", "violence", "kidnapping",
    ]

    # Vellore district localities (same as scraper)
    LOCALITY_KEYWORDS: List[str] = [
        "Vellore", "Katpadi", "Ranipet", "Arani", "Tirupattur",
        "Vaniyambadi", "Ambur", "Gudiyatham", "Pernambut",
        "Walajapet", "Arakkonam", "Sholinghur", "Anaicut",
        "K V Kuppam", "Kaniyambadi", "Madhanur", "Natrampalli",
    ]

    def __init__(
        self,
        raw_dir: Path = RAW_NEWS_DIR,
        processed_dir: Path = PROCESSED_DIR,
        output_json: Path = OUTPUT_JSON,
        output_csv: Path = OUTPUT_CSV,
    ) -> None:
        """Initialize the news cleaner.

        Args:
            raw_dir: Directory containing raw news files.
            processed_dir: Directory for output files.
            output_json: Path to output JSON file.
            output_csv: Path to output CSV file.
        """
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir
        self.output_json = output_json
        self.output_csv = output_csv
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def run(self) -> int:
        """Run the cleaning pipeline.

        Returns:
            Number of final cleaned records.
        """
        logger.info("=" * 70)
        logger.info("Crime News Data Processing Pipeline - Starting")
        logger.info("=" * 70)

        # Step 1: Load raw articles
        raw_articles = self._load_raw_articles()
        total_articles = len(raw_articles)
        logger.info("Total articles loaded: %d", total_articles)

        if not raw_articles:
            logger.error("No raw articles found to process")
            return 0

        # Step 2: Remove duplicates (by URL)
        unique_articles, duplicates_removed = self._remove_duplicates(
            raw_articles
        )
        logger.info(
            "Duplicate articles removed: %d", duplicates_removed
        )

        # Step 3: Remove non-crime articles
        crime_articles = self._filter_crime(unique_articles)
        logger.info(
            "Crime articles after filter: %d", len(crime_articles)
        )

        # Step 4: Standardize and build cleaned records
        cleaned_records = self._build_cleaned_records(crime_articles)
        logger.info(
            "Cleaned records built: %d", len(cleaned_records)
        )

        # Step 5: Save outputs
        self._save_json(cleaned_records)
        self._save_csv(cleaned_records)

        # Step 6: Print statistics
        self._print_statistics(
            total_articles=total_articles,
            crime_articles=len(crime_articles),
            duplicates_removed=duplicates_removed,
            final_records=len(cleaned_records),
        )

        return len(cleaned_records)

    def _load_raw_articles(self) -> List[Dict[str, Any]]:
        """Load raw articles from the news directory.

        Tries to read from `crime_articles.json` first (new format),
        then falls back to `articles.json` (old format).

        Returns:
            List of raw article dictionaries.
        """
        # Try new format first
        crime_file = self.raw_dir / "crime_articles.json"
        if crime_file.exists():
            try:
                with open(
                    crime_file, "r", encoding="utf-8"
                ) as f:
                    data = json.load(f)
                logger.info(
                    "Loaded %d articles from %s",
                    len(data), crime_file,
                )
                return data
            except (json.JSONDecodeError, IOError) as exc:
                logger.error(
                    "Failed to load %s: %s", crime_file, exc
                )

        # Fall back to old format
        articles_file = self.raw_dir / "articles.json"
        if articles_file.exists():
            try:
                with open(
                    articles_file, "r", encoding="utf-8"
                ) as f:
                    data = json.load(f)
                logger.info(
                    "Loaded %d articles from %s",
                    len(data), articles_file,
                )
                return data
            except (json.JSONDecodeError, IOError) as exc:
                logger.error(
                    "Failed to load %s: %s", articles_file, exc
                )

        logger.error(
            "No raw article files found in %s", self.raw_dir
        )
        return []

    @staticmethod
    def _remove_duplicates(
        articles: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Remove duplicate articles by URL.

        Args:
            articles: List of raw article dictionaries.

        Returns:
            Tuple of (unique_articles, duplicates_removed).
        """
        unique: List[Dict[str, Any]] = []
        seen_urls: Set[str] = set()
        duplicates = 0

        for article in articles:
            url = article.get("url", "") or ""
            if url in seen_urls:
                duplicates += 1
                continue
            seen_urls.add(url)
            unique.append(article)

        return unique, duplicates

    def _filter_crime(
        self, articles: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filter to crime-related articles only.

        Args:
            articles: List of raw article dictionaries.

        Returns:
            List of crime-related articles.
        """
        crime_articles = []
        for article in articles:
            # Build text from available fields
            title = article.get("title", "") or ""
            article_text = article.get("article_text", "") or ""
            detected_type = article.get(
                "detected_crime_type", ""
            ) or ""

            text = f"{title} {article_text}".lower()

            # Check if it's a crime article
            if self._is_crime_text(text):
                # Force re-detect crime type if needed
                if detected_type in ("", "Unknown"):
                    detected_type = (
                        CrimeTypeStandardizer.standardize(
                            "Unknown", f"{title} {article_text}"
                        )
                    )
                    article["detected_crime_type"] = detected_type
                crime_articles.append(article)

        return crime_articles

    def _is_crime_text(self, text_lower: str) -> bool:
        """Check if text contains crime-related keywords.

        Args:
            text_lower: Lowercased article text.

        Returns:
            ``True`` if text contains crime keywords.
        """
        for keyword in self.CRIME_FILTER_KEYWORDS:
            if keyword in text_lower:
                return True
        return False

    def _detect_locality(self, text: str) -> str:
        """Detect the locality from article text.

        Args:
            text: Article title + text.

        Returns:
            Detected locality, or 'Vellore' if not found.
        """
        text_lower = text.lower()
        for locality in self.LOCALITY_KEYWORDS:
            if locality.lower() in text_lower:
                return locality
        return "Vellore"

    @staticmethod
    def _generate_article_id(
        url: str, title: str
    ) -> str:
        """Generate a unique article ID.

        Uses SHA-256 hash of URL + title.

        Args:
            url: Article URL.
            title: Article title.

        Returns:
            Unique article ID string.
        """
        raw = f"{url}|{title}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def _build_cleaned_records(
        self, articles: List[Dict[str, Any]]
    ) -> List[CleanedArticle]:
        """Build cleaned article records.

        Args:
            articles: List of crime articles.

        Returns:
            List of :class:`CleanedArticle` objects.
        """
        records: List[CleanedArticle] = []

        for article in articles:
            title = article.get("title", "") or ""
            url = article.get("url", "") or ""
            source = article.get(
                "publication", ""
            ) or article.get("source", "") or ""
            published_date = article.get("published_date", "") or ""
            article_text = article.get("article_text", "") or ""
            district = article.get("district", "Vellore") or "Vellore"
            detected_type = article.get(
                "detected_crime_type", ""
            ) or "Unknown"

            # Standardize crime type
            crime_type = CrimeTypeStandardizer.standardize(
                detected_type, f"{title} {article_text}"
            )

            # Detect locality
            locality = self._detect_locality(
                f"{title} {article_text}"
            )

            # Build description (first 2000 chars, cleaned)
            description = self._clean_text(article_text)

            article_id = self._generate_article_id(url, title)

            records.append(
                CleanedArticle(
                    article_id=article_id,
                    title=title,
                    published_date=published_date,
                    source=source,
                    url=url,
                    crime_type=crime_type,
                    district=district,
                    locality=locality,
                    description=description,
                )
            )

        return records

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean and truncate article text.

        Args:
            text: Raw article text.

        Returns:
            Cleaned description text (max 2000 chars).
        """
        if not text:
            return ""
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()
        # Limit length for description field
        return text[:2000]

    def _save_json(
        self, records: List[CleanedArticle]
    ) -> None:
        """Save cleaned records to JSON.

        Args:
            records: List of cleaned article records.
        """
        try:
            data = [asdict(r) for r in records]
            with open(
                self.output_json, "w", encoding="utf-8"
            ) as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(
                "Saved %d records to %s",
                len(data), self.output_json,
            )
        except IOError as exc:
            logger.error("Failed to save JSON: %s", exc)

    def _save_csv(
        self, records: List[CleanedArticle]
    ) -> None:
        """Save cleaned records to CSV.

        Args:
            records: List of cleaned article records.
        """
        try:
            fieldnames = ["article_id", "title", "published_date",
                          "source", "url", "crime_type", "district",
                          "locality", "description"]
            with open(
                self.output_csv, "w", encoding="utf-8", newline=""
            ) as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for record in records:
                    writer.writerow(asdict(record))
            logger.info(
                "Saved %d records to %s",
                len(records), self.output_csv,
            )
        except (IOError, ValueError) as exc:
            logger.error("Failed to save CSV: %s", exc)

    @staticmethod
    def _print_statistics(
        total_articles: int,
        crime_articles: int,
        duplicates_removed: int,
        final_records: int,
    ) -> None:
        """Print the pipeline statistics.

        Args:
            total_articles: Total raw articles loaded.
            crime_articles: Number of crime articles.
            duplicates_removed: Number of duplicates removed.
            final_records: Number of final cleaned records.
        """
        print("\n" + "=" * 60)
        print("Statistics")
        print("=" * 60)
        print(f"Total articles:           {total_articles}")
        print(f"Crime articles:           {crime_articles}")
        print(f"Duplicate articles removed: {duplicates_removed}")
        print(f"Final records:            {final_records}")
        print("=" * 60)


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def main() -> int:
    """Main entry point for the cleaning pipeline.

    Returns:
        Exit code: ``0`` for success, ``1`` for failure.
    """
    cleaner = NewsCleaner()
    count = cleaner.run()

    if count > 0:
        logger.info("Cleaning pipeline completed successfully")
        return 0
    else:
        logger.warning("No records produced")
        return 1


if __name__ == "__main__":
    sys.exit(main())