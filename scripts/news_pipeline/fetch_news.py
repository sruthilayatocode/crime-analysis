"""
Multi-source Crime News Scraper for Vellore District.

This script scrapes crime-related news articles directly from multiple
Indian news websites using requests and BeautifulSoup. It targets
approximately 300 high-quality crime articles for the Vellore District.

Sources:
    - The Hindu Tamil Nadu
    - Times of India Vellore
    - DT Next
    - New Indian Express Tamil Nadu
    - Deccan Chronicle

Features:
    - Direct website scraping (no Google News RSS)
    - Article link detection
    - Full article text extraction
    - Crime type detection
    - Location detection
    - Duplicate removal
    - JSON and CSV output
    - Failed page logging
    - Retry logic with exponential backoff
    - Continues scraping even if one website fails

Output:
    data/raw/news/articles.json
    data/raw/news/articles.csv

Usage:
    python scripts/news_pipeline/fetch_news.py

Author: Crime Analysis Project
License: MIT
"""

from __future__ import annotations

import csv
import json
import logging
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR: Path = PROJECT_ROOT / "data" / "raw" / "news"
OUTPUT_JSON: Path = OUTPUT_DIR / "crime_articles.json"
OUTPUT_CSV: Path = OUTPUT_DIR / "crime_articles.csv"
LOG_DIR: Path = PROJECT_ROOT / "logs"
LOG_FILE: Path = LOG_DIR / "news_scraper.log"
FAILED_LOG: Path = OUTPUT_DIR / "failed_pages.log"

REQUEST_TIMEOUT: int = 30
MAX_RETRIES: int = 3
RETRY_DELAY: float = 3.0
RATE_LIMIT_DELAY: float = 1.0
TARGET_ARTICLES: int = 300

HEADERS: Dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# ---------------------------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------------------------

LOG_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger("news_scraper")


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class Article:
    """Represents a scraped news article.

    Attributes:
        title: Article headline.
        url: Full URL of the article.
        publication: News source name.
        published_date: Publication date string.
        article_text: Full extracted text content.
        detected_crime_type: Detected crime category.
        detected_location: Detected location mention.
        district: District name (default 'Vellore').
        state: State name (default 'Tamil Nadu').
        accused_name: Detected accused person name (if available).
        victim_name: Detected victim person name (if available).
    """

    title: str
    url: str
    publication: str
    published_date: str
    article_text: str = ""
    detected_crime_type: str = ""
    detected_location: str = ""
    district: str = "Vellore"
    state: str = "Tamil Nadu"
    accused_name: str = ""
    victim_name: str = ""


# ---------------------------------------------------------------------------
# HTML Fetcher (HTTP layer with retry logic)
# ---------------------------------------------------------------------------

class HTMLFetcher:
    """Fetches HTML pages with retry and timeout handling.

    Attributes:
        timeout: HTTP request timeout in seconds.
        max_retries: Maximum number of retry attempts.
        retry_delay: Base delay between retry attempts in seconds.
        session: Persistent ``requests.Session``.
    """

    def __init__(
        self,
        timeout: int = REQUEST_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        retry_delay: float = RETRY_DELAY,
    ) -> None:
        """Initialize the HTML fetcher.

        Args:
            timeout: HTTP request timeout in seconds.
            max_retries: Maximum number of retry attempts.
            retry_delay: Base delay between retry attempts in seconds.
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def fetch(self, url: str) -> Optional[str]:
        """Fetch HTML content from a URL with retries.

        Args:
            url: URL to fetch.

        Returns:
            HTML content as string, or ``None`` if all retries fail.
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(
                    url, timeout=self.timeout, allow_redirects=True
                )
                response.raise_for_status()
                return response.text
            except requests.exceptions.Timeout:
                logger.warning(
                    "Timeout fetching %s (attempt %d/%d)",
                    url, attempt, self.max_retries,
                )
            except requests.exceptions.ConnectionError as exc:
                logger.warning(
                    "Connection error %s (attempt %d/%d): %s",
                    url, attempt, self.max_retries, exc,
                )
            except requests.exceptions.HTTPError as exc:
                status = (
                    exc.response.status_code
                    if exc.response is not None
                    else "unknown"
                )
                logger.warning(
                    "HTTP %s for %s (attempt %d/%d)",
                    status, url, attempt, self.max_retries,
                )
            except requests.exceptions.RequestException as exc:
                logger.warning(
                    "Request failed %s (attempt %d/%d): %s",
                    url, attempt, self.max_retries, exc,
                )

            if attempt < self.max_retries:
                backoff = self.retry_delay * attempt
                logger.info(
                    "Retrying %s in %.1fs...", url, backoff
                )
                time.sleep(backoff)

        logger.error("All retries exhausted for %s", url)
        return None


# ---------------------------------------------------------------------------
# Source Configurations
# ---------------------------------------------------------------------------

@dataclass
class SourceConfig:
    """Configuration for a news source website.

    Attributes:
        name: Publication name.
        base_url: Base URL of the website.
        listing_urls: URLs of listing/search pages to scrape.
        article_link_pattern: Regex pattern to identify article URLs.
        title_selector: CSS selector for article title.
        date_selector: CSS selector for publication date.
        content_selector: CSS selector for article content.
    """

    name: str
    base_url: str
    listing_urls: List[str]
    article_link_pattern: str
    title_selector: str = "h1"
    date_selector: str = "time"
    content_selector: str = "article"


SOURCES: List[SourceConfig] = [
    SourceConfig(
        name="The Hindu",
        base_url="https://www.thehindu.com",
        listing_urls=[
            "https://www.thehindu.com/news/national/tamil-nadu/",
            "https://www.thehindu.com/topic/crime/",
        ],
        article_link_pattern=r"https://www\.thehindu\.com/news/"
        r"national/tamil-nadu/[a-z0-9\-]+/article\d+\.ece",
        title_selector="h1",
        date_selector="time",
        content_selector="div.article-body",
    ),
    SourceConfig(
        name="Times of India",
        base_url="https://timesofindia.indiatimes.com",
        listing_urls=[
            "https://timesofindia.indiatimes.com/city/vellore",
        ],
        article_link_pattern=r"https://timesofindia\.indiatimes\.com/"
        r"city/vellore/[a-z0-9\-]+/articleshow/\d+\.cms",
        title_selector="h1",
        date_selector="time",
        content_selector="div._s30J",
    ),
    SourceConfig(
        name="DT Next",
        base_url="https://www.dtnext.in",
        listing_urls=[
            "https://www.dtnext.in/news/tamilnadu/",
        ],
        article_link_pattern=r"https://www\.dtnext\.in/.*",  # broad pattern
        title_selector="h1",
        date_selector="time",
        content_selector="article",
    ),
    SourceConfig(
        name="New Indian Express",
        base_url="https://www.newindianexpress.com",
        listing_urls=[
            "https://www.newindianexpress.com/states/tamil-nadu/",
        ],
        article_link_pattern=r"https://www\.newindianexpress\.com/"
        r"states/tamil-nadu/\d{4}/\w+/[a-z0-9\-]+\.html",
        title_selector="h1",
        date_selector="time",
        content_selector="div.content-area",
    ),
    SourceConfig(
        name="Deccan Chronicle",
        base_url="https://www.deccanchronicle.com",
        listing_urls=[
            "https://www.deccanchronicle.com/nation/in-other-news",
            "https://www.deccanchronicle.com/nation/crime",
        ],
        article_link_pattern=r"https://www\.deccanchronicle\.com/.*",
        title_selector="h1",
        date_selector="time",
        content_selector="div.article-body",
    ),
]


# ---------------------------------------------------------------------------
# Article Parser (Single article parsing)
# ---------------------------------------------------------------------------

class ArticleParser:
    """Parses HTML content into Article objects.

    Attributes:
        fetcher: :class:`HTMLFetcher` instance for fetching article pages.
    """

    def __init__(self, fetcher: HTMLFetcher) -> None:
        """Initialize the article parser.

        Args:
            fetcher: :class:`HTMLFetcher` instance.
        """
        self.fetcher = fetcher

    def parse_article(
        self, url: str, source: SourceConfig
    ) -> Optional[Article]:
        """Fetch and parse a single article from its URL.

        Args:
            url: Article URL.
            source: :class:`SourceConfig` for the source website.

        Returns:
            :class:`Article` object, or ``None`` if parsing fails.
        """
        html = self.fetcher.fetch(url)
        if not html:
            return None

        soup = BeautifulSoup(html, "lxml")

        # Extract title
        title = self._extract_title(soup, source)
        if not title:
            logger.debug("No title found for %s", url)
            return None

        # Extract published date
        published_date = self._extract_date(soup, source)

        # Extract article text
        article_text = self._extract_text(soup, source)
        if not article_text:
            logger.debug("No article text found for %s", url)
            return None

        # Detect crime type, location, and names
        full_text = f"{title} {article_text}"
        crime_type = CrimeDetector.detect_crime_type(full_text)
        location = CrimeDetector.detect_location(full_text)
        accused_name, victim_name = CrimeDetector.extract_names(full_text)

        return Article(
            title=title,
            url=url,
            publication=source.name,
            published_date=published_date,
            article_text=article_text,
            detected_crime_type=crime_type,
            detected_location=location,
            accused_name=accused_name,
            victim_name=victim_name,
        )

    @staticmethod
    def _extract_title(
        soup: BeautifulSoup, source: SourceConfig
    ) -> str:
        """Extract the article title.

        Args:
            soup: Parsed HTML.
            source: Source configuration.

        Returns:
            Title string, or empty string if not found.
        """
        el = soup.select_one(source.title_selector)
        if el:
            return el.get_text(strip=True)
        # Fallback: <title> tag
        if soup.title:
            return soup.title.get_text(strip=True)
        return ""

    @staticmethod
    def _extract_date(
        soup: BeautifulSoup, source: SourceConfig
    ) -> str:
        """Extract the publication date.

        Args:
            soup: Parsed HTML.
            source: Source configuration.

        Returns:
            Date string, or empty string if not found.
        """
        el = soup.select_one(source.date_selector)
        if el:
            # Try datetime attribute first
            dt = el.get("datetime")
            if dt:
                return dt
            return el.get_text(strip=True)
        # Look for common date patterns
        patterns = [
            r"\b\d{4}-\d{2}-\d{2}\b",
            r"\b\d{1,2}\s+(January|February|March|April|May|June|"
            r"July|August|September|October|November|December)\s+\d{4}\b",
            r"\b\d{1,2}/\d{1,2}/\d{4}\b",
        ]
        page_text = soup.get_text()
        for pattern in patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                return match.group(0)
        return ""

    @staticmethod
    def _extract_text(
        soup: BeautifulSoup, source: SourceConfig
    ) -> str:
        """Extract the main article text.

        Args:
            soup: Parsed HTML.
            source: Source configuration.

        Returns:
            Article text string, or empty string if not found.
        """
        content_el = soup.select_one(source.content_selector)
        if content_el:
            paragraphs = content_el.find_all("p")
            if paragraphs:
                return " ".join(
                    p.get_text(strip=True) for p in paragraphs
                )
            return content_el.get_text(strip=True)

        # Fallback: all <p> tags
        paragraphs = soup.find_all("p")
        if paragraphs:
            text = " ".join(
                p.get_text(strip=True) for p in paragraphs
            )
            # Remove navigation/footer noise
            text = re.sub(r"\s+", " ", text)
            return text[:10000]
        return ""


# ---------------------------------------------------------------------------
# Crime Detector (Rule-based crime type & location detection)
# ---------------------------------------------------------------------------

class CrimeDetector:
    """Detects crime type, location, and names from article text.

    Uses keyword matching against a predefined list of crime
    categories and Vellore district localities. Also extracts
    accused and victim names using regex patterns.
    """

    # Required crime keywords for filtering
    CRIME_FILTER_KEYWORDS: List[str] = [
        "murder", "theft", "robbery", "assault", "rape",
        "police", "arrest", "fir", "cyber crime", "drugs",
        "smuggling", "violence", "kidnapping",
    ]

    # High-priority Vellore district localities
    PRIORITY_LOCALITIES: List[str] = [
        "Vellore", "Katpadi", "Gudiyatham", "Ambur",
        "Pernambut", "Anaicut", "Arakkonam", "Ranipet",
        "Walajah",
    ]

    # All Vellore district localities
    LOCALITY_KEYWORDS: List[str] = [
        "Vellore", "Katpadi", "Ranipet", "Arani", "Tirupattur",
        "Vaniyambadi", "Ambur", "Gudiyatham", "Pernambut",
        "Walajapet", "Arakkonam", "Sholinghur", "Anaicut",
        "K V Kuppam", "Kaniyambadi", "Madhanur", "Natrampalli",
    ]

    # Crime type mapping
    CRIME_TYPE_MAP: Dict[str, List[str]] = {
        "Murder": ["murder", "killed", "homicide", "death"],
        "Theft": ["theft", "stolen", "burglary", "robbery"],
        "Assault": ["assault", "attack", "beaten", "injured"],
        "Sexual Assault": [
            "sexual assault", "rape", "molest", "harassment",
        ],
        "Fraud": ["fraud", "scam", "cheated", "fake", "counterfeit"],
        "Cybercrime": [
            "cyber crime", "online scam", "digital arrest",
            "phishing", "hacking",
        ],
        "Drugs": ["drugs", "narcotic", "smuggling", "ganja"],
        "Kidnapping": ["kidnapping", "abduction", "abducted"],
        "Extortion": ["extortion", "blackmail", "threat"],
        "Corruption": ["corruption", "bribery", "bribe"],
        "Dowry": ["dowry", "dowry death"],
        "Other": [],
    }

    # Name extraction patterns
    NAME_PATTERNS: List[str] = [
        # "X (age 45)" or "X (45)"
        r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\s*\(\s*(?:aged?\s*)?\d{1,3}\s*\)",
        # "X, 45, a resident of"
        r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)*),\s*\d{1,3},?\s+(?:a\s+)?resident",
        # "X, a 45-year-old"
        r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)*),\s*a\s+\d{1,3}-year-old",
        # "X (45) was arrested"
        r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\s*\(\s*\d{1,3}\s*\)\s+was\s+arrested",
    ]

    @classmethod
    def is_crime_article(cls, text: str) -> bool:
        """Check if an article contains crime-related keywords.

        Args:
            text: Article title + article text.

        Returns:
            ``True`` if the article contains crime keywords.
        """
        text_lower = text.lower()
        for keyword in cls.CRIME_FILTER_KEYWORDS:
            if keyword in text_lower:
                return True
        return False

    @classmethod
    def is_vellore_article(cls, text: str) -> bool:
        """Check if an article mentions a Vellore district locality.

        Args:
            text: Article title + article text.

        Returns:
            ``True`` if the article mentions a Vellore locality.
        """
        text_lower = text.lower()
        for locality in cls.LOCALITY_KEYWORDS:
            if locality.lower() in text_lower:
                return True
        return False

    @classmethod
    def detect_crime_type(cls, text: str) -> str:
        """Detect the crime type from article text.

        Args:
            text: Article title + article text.

        Returns:
            Detected crime type string, or 'Unknown' if not detected.
        """
        text_lower = text.lower()
        for crime_type, keywords in cls.CRIME_TYPE_MAP.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return crime_type
        return "Unknown"

    @classmethod
    def detect_location(cls, text: str) -> str:
        """Detect the location from article text.

        Args:
            text: Article title + article text.

        Returns:
            Detected location string, or 'Vellore' if not detected.
        """
        text_lower = text.lower()
        for locality in cls.LOCALITY_KEYWORDS:
            if locality.lower() in text_lower:
                return locality
        return "Vellore"

    @classmethod
    def extract_names(cls, text: str) -> Tuple[str, str]:
        """Extract accused and victim names from article text.

        Uses regex patterns to find person names with age or
        resident information.

        Args:
            text: Article title + article text.

        Returns:
            Tuple of ``(accused_name, victim_name)``.
        """
        accused = ""
        victim = ""

        # Look for accused patterns
        accused_patterns = [
            r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\s*\((\d{1,3})\)\s*was\s+arrested",
            r"arrested\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)",
            r"held\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)",
        ]
        for pattern in accused_patterns:
            match = re.search(pattern, text)
            if match:
                accused = match.group(1)
                break

        # Look for victim patterns
        victim_patterns = [
            r"victim\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)",
            r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\s*\((\d{1,3})\)\s*was\s+killed",
            r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\s*\((\d{1,3})\)\s*died",
        ]
        for pattern in victim_patterns:
            match = re.search(pattern, text)
            if match:
                victim = match.group(1)
                break

        return accused, victim


# ---------------------------------------------------------------------------
# News Scraper (Orchestrator)
# ---------------------------------------------------------------------------

class NewsScraper:
    """Orchestrates multi-source news scraping.

    Scrapes listing pages for article links, fetches each article,
    removes duplicates, and saves results to JSON and CSV.

    Attributes:
        fetcher: :class:`HTMLFetcher` instance.
        parser: :class:`ArticleParser` instance.
        sources: List of :class:`SourceConfig`.
        target_articles: Target number of articles to collect.
    """

    def __init__(
        self,
        fetcher: Optional[HTMLFetcher] = None,
        parser: Optional[ArticleParser] = None,
        sources: Optional[List[SourceConfig]] = None,
        target_articles: int = TARGET_ARTICLES,
    ) -> None:
        """Initialize the news scraper.

        Args:
            fetcher: :class:`HTMLFetcher` instance.
            parser: :class:`ArticleParser` instance.
            sources: List of :class:`SourceConfig`.
            target_articles: Target number of articles.
        """
        self.fetcher = fetcher or HTMLFetcher()
        self.parser = parser or ArticleParser(self.fetcher)
        self.sources = sources or SOURCES
        self.target_articles = target_articles

    def run(self) -> int:
        """Run the multi-source scraping pipeline.

        Returns:
            Number of crime articles successfully scraped and saved.
        """
        logger.info("=" * 70)
        logger.info("Crime Dataset Generator - Starting")
        logger.info("Target articles: %d", self.target_articles)
        logger.info("=" * 70)

        all_articles: List[Article] = []
        seen_urls: Set[str] = set()
        failed_pages: List[str] = []

        for source in self.sources:
            logger.info("-" * 60)
            logger.info(
                "Scraping source: %s", source.name
            )
            logger.info("-" * 60)

            try:
                source_articles = self._scrape_source(
                    source, seen_urls, failed_pages
                )
            except Exception as exc:
                logger.error(
                    "Source %s failed: %s - continuing",
                    source.name, exc,
                )
                source_articles = []

            all_articles.extend(source_articles)
            logger.info(
                "Total articles so far: %d", len(all_articles)
            )

            if len(all_articles) >= self.target_articles:
                logger.info(
                    "Reached target of %d articles - stopping",
                    self.target_articles,
                )
                break

        # Remove duplicates (by URL)
        unique_articles = self._deduplicate(all_articles)
        duplicates_removed = len(all_articles) - len(unique_articles)

        # Filter to crime articles only
        crime_articles = [
            a for a in unique_articles
            if CrimeDetector.is_crime_article(
                f"{a.title} {a.article_text}"
            )
        ]

        # Prioritize Vellore articles (sort Vellore first)
        crime_articles.sort(
            key=lambda a: not CrimeDetector.is_vellore_article(
                f"{a.title} {a.article_text}"
            )
        )

        vellore_count = sum(
            1 for a in crime_articles
            if CrimeDetector.is_vellore_article(
                f"{a.title} {a.article_text}"
            )
        )

        # Log failed pages
        self._log_failed_pages(failed_pages)

        # Save results
        if crime_articles:
            self._save_json(crime_articles)
            self._save_csv(crime_articles)
            logger.info(
                "Saved %d crime articles", len(crime_articles)
            )
        else:
            logger.warning("No crime articles were collected")

        self._print_summary(
            total_scraped=len(all_articles),
            crime_count=len(crime_articles),
            vellore_count=vellore_count,
            duplicates_removed=duplicates_removed,
        )

        return len(crime_articles)

    def _scrape_source(
        self,
        source: SourceConfig,
        seen_urls: Set[str],
        failed_pages: List[str],
    ) -> List[Article]:
        """Scrape a single source website.

        Args:
            source: Source configuration.
            seen_urls: Set of already-seen article URLs.
            failed_pages: List to append failed page URLs to.

        Returns:
            List of :class:`Article` objects.
        """
        articles: List[Article] = []
        article_links: List[str] = []

        # Collect article links from all listing pages
        for listing_url in source.listing_urls:
            logger.info("Fetching listing: %s", listing_url)
            html = self.fetcher.fetch(listing_url)
            if not html:
                failed_pages.append(listing_url)
                continue

            soup = BeautifulSoup(html, "lxml")
            links = self._find_article_links(soup, source)
            logger.info(
                "Found %d candidate article links on %s",
                len(links), listing_url,
            )
            article_links.extend(links)
            time.sleep(RATE_LIMIT_DELAY)

        # Parse each article
        for i, url in enumerate(article_links, 1):
            if url in seen_urls:
                continue

            logger.info(
                "[%d/%d] Parsing article: %s",
                i, len(article_links), url[:100],
            )

            article = self.parser.parse_article(url, source)
            if article:
                seen_urls.add(url)
                articles.append(article)
                logger.info(
                    "  [OK] %s - %s",
                    article.title[:80],
                    article.detected_crime_type,
                )
            else:
                logger.info("  [FAILED] %s", url[:100])
                failed_pages.append(url)

            time.sleep(RATE_LIMIT_DELAY)

        return articles

    @staticmethod
    def _find_article_links(
        soup: BeautifulSoup, source: SourceConfig
    ) -> List[str]:
        """Find article links in a listing page.

        Args:
            soup: Parsed listing page HTML.
            source: Source configuration.

        Returns:
            List of article URLs.
        """
        pattern = re.compile(source.article_link_pattern)
        links: List[str] = []
        seen: Set[str] = set()

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            # Resolve relative URLs
            if href.startswith("/"):
                href = source.base_url + href
            elif not href.startswith("http"):
                continue

            if pattern.match(href) and href not in seen:
                seen.add(href)
                links.append(href)

        return links

    @staticmethod
    def _deduplicate(articles: List[Article]) -> List[Article]:
        """Remove duplicate articles by URL.

        Args:
            articles: List of articles.

        Returns:
            List of unique articles.
        """
        unique: List[Article] = []
        seen_urls: Set[str] = set()
        for article in articles:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                unique.append(article)
        return unique

    @staticmethod
    def _log_failed_pages(failed_pages: List[str]) -> None:
        """Log failed page URLs to a file.

        Args:
            failed_pages: List of failed page URLs.
        """
        if not failed_pages:
            return
        try:
            with open(
                FAILED_LOG, "w", encoding="utf-8"
            ) as f:
                for url in failed_pages:
                    f.write(f"{url}\n")
            logger.warning(
                "Logged %d failed pages to %s",
                len(failed_pages), FAILED_LOG,
            )
        except IOError as exc:
            logger.error("Failed to log failed pages: %s", exc)

    def _save_json(self, articles: List[Article]) -> None:
        """Save articles to a JSON file.

        Args:
            articles: List of articles.
        """
        try:
            data = [asdict(a) for a in articles]
            with open(
                OUTPUT_JSON, "w", encoding="utf-8"
            ) as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("Saved %d articles to %s", len(data), OUTPUT_JSON)
        except IOError as exc:
            logger.error("Failed to save JSON: %s", exc)

    def _save_csv(self, articles: List[Article]) -> None:
        """Save articles to a CSV file.

        Args:
            articles: List of articles.
        """
        try:
            fieldnames = list(
                asdict(articles[0]).keys()
            ) if articles else []
            with open(
                OUTPUT_CSV, "w", encoding="utf-8", newline=""
            ) as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for article in articles:
                    writer.writerow(asdict(article))
            logger.info(
                "Saved %d articles to %s", len(articles), OUTPUT_CSV
            )
        except (IOError, ValueError) as exc:
            logger.error("Failed to save CSV: %s", exc)

    @staticmethod
    def _print_summary(
        total_scraped: int,
        crime_count: int,
        vellore_count: int,
        duplicates_removed: int,
    ) -> None:
        """Print the final summary.

        Args:
            total_scraped: Total articles scraped.
            crime_count: Number of crime articles.
            vellore_count: Number of Vellore crime articles.
            duplicates_removed: Number of duplicate articles removed.
        """
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)
        print(f"Total Articles Scraped:     {total_scraped}")
        print(f"Crime Articles:             {crime_count}")
        print(f"Vellore Crime Articles:     {vellore_count}")
        print(f"Duplicate Articles Removed: {duplicates_removed}")
        print(f"Output JSON:                {OUTPUT_JSON}")
        print(f"Output CSV:                 {OUTPUT_CSV}")
        print(f"Failed pages log:           {FAILED_LOG}")
        print("=" * 60)


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def main() -> int:
    """Main entry point for the multi-source news scraper.

    Returns:
        Exit code: ``0`` for success, ``1`` for failure.
    """
    scraper = NewsScraper()
    count = scraper.run()

    if count > 0:
        logger.info("Scraping completed successfully")
        return 0
    else:
        logger.warning("No articles collected")
        return 1


if __name__ == "__main__":
    sys.exit(main())