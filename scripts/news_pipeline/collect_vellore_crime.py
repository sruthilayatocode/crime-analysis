#!/usr/bin/env python
"""
Vellore-Specific Crime News Collection Pipeline.
==================================================
Improves on the existing generic news scraper by performing TARGETED
search-query based collection of crime news specifically from Vellore
district, Tamil Nadu.

This stage collects candidate crime articles using Google News RSS search
queries that combine:
  - "Vellore" with crime terms (e.g. "Vellore murder", "Vellore theft")
  - Vellore-district localities with crime terms (e.g. "Ambur robbery",
    "Katpadi kidnapping")

Only articles whose actual incident occurred in Vellore district are retained
in the final validated output. Articles are NOT retained merely because:
  - Vellore is mentioned in passing
  - a person from Vellore is mentioned
  - Vellore police are investigating an incident elsewhere
  - the article is about Tamil Nadu generally

Architecture:
  - Reuses the existing news_pipeline patterns (requests + BeautifulSoup,
    HTTPFetcher with retry logic, rule-based filtering).
  - Reuses the validation logic from scripts/validate_data.py.

Outputs:
  data/raw/vellore_crime_raw.csv                  (raw collected candidates)
  data/processed/vellore_crime_validated.csv      (validated Vellore crime)
  data/reports/vellore_collection_report.txt      (collection report)

Usage:
  python scripts/news_pipeline/collect_vellore_crime.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import re
import sys
import time
from datetime import datetime
from html import unescape
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import quote_plus
from xml.etree import ElementTree as ET

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent

RAW_OUTPUT: Path = PROJECT_ROOT / "data" / "raw" / "vellore_crime_raw.csv"
VALIDATED_OUTPUT: Path = PROJECT_ROOT / "data" / "processed" / "vellore_crime_validated.csv"
REPORT_OUTPUT: Path = PROJECT_ROOT / "data" / "reports" / "vellore_collection_report.txt"
LOG_FILE: Path = PROJECT_ROOT / "logs" / "collect_vellore_crime.log"
LOCALITY_CONFIG: Path = PROJECT_ROOT / "data" / "reference" / "vellore_localities_config.json"

GOOGLE_NEWS_RSS_URL: str = "https://news.google.com/rss/search"
REQUEST_TIMEOUT: int = 15
MAX_RETRIES: int = 2  # 1 initial + 1 retry = at most 2 attempts
RETRY_DELAY: float = 2.0

RATE_LIMIT_DELAY: float = 0.5

MAX_CANDIDATES: int = 300
MAX_RUNTIME_SECONDS: int = 600  # ~10 minutes

HEADERS: Dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36 "
        "CrimeAnalysisVellore/1.0"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# ---------------------------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------------------------

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger("collect_vellore_crime")

# ---------------------------------------------------------------------------
# Search Configuration
# ---------------------------------------------------------------------------

CRIME_TERMS: List[str] = [
    "crime", "murder", "theft", "robbery", "burglary", "assault",
    "kidnapping", "cyber crime", "fraud", "drug crime", "sexual assault",
    "arrest", "criminal case", "attack", "stolen", "snatching",
    "extortion", "police",
]

LOCALITIES: List[str] = [
    "Vellore", "Katpadi", "Arani", "Ranipet", "Tiruppattur", "Ambur",
    "Sathyamangalam", "Pallikonda", "Kaveripattinam", "Perambur",
    "Nathavasi", "Vaniyambadi", "Gudiyatham", "Pernambut", "Arakkonam",
    "Sholinghur", "Anaicut", "Natrampalli",
]

LOCALITY_CRIME_TERMS: List[str] = [
    "crime", "murder", "theft", "robbery", "assault", "kidnapping",
    "drug", "arrest",
]

def generate_queries() -> List[str]:
    """Generate Google News search queries targeting Vellore district."""
    queries: List[str] = []
    for term in CRIME_TERMS:
        queries.append("Vellore %s" % term)
    for term in CRIME_TERMS:
        queries.append("Vellore district %s" % term)
    for locality in LOCALITIES:
        for term in LOCALITY_CRIME_TERMS:
            queries.append("%s %s" % (locality, term))
    seen: Set[str] = set()
    unique: List[str] = []
    for q in queries:
        key = q.lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(q)
    return unique


def build_rss_url(query: str) -> str:
    """Build the Google News RSS URL for a search query."""
    q = quote_plus(query)
    return "%s?q=%s&hl=en-IN&gl=IN&ceid=IN:en" % (GOOGLE_NEWS_RSS_URL, q)


class HTTPFetcher:
    """Fetches URLs with retry and timeout handling (reuses existing pattern)."""

    def __init__(self, timeout: int = REQUEST_TIMEOUT,
                 max_retries: int = MAX_RETRIES,
                 retry_delay: float = RETRY_DELAY) -> None:
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def fetch(self, url: str) -> Optional[str]:
        """Fetch content from a URL with retries. Returns text or None."""
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(
                    url, timeout=self.timeout, allow_redirects=True
                )
                response.raise_for_status()
                return response.text
            except requests.exceptions.Timeout:
                logger.warning(
                    "Timeout %s (attempt %d/%d)", url[:120], attempt, self.max_retries
                )
            except requests.exceptions.ConnectionError as exc:
                logger.warning("Connection error %s: %s", url[:120], exc)
            except requests.exceptions.HTTPError as exc:
                status = (exc.response.status_code
                          if exc.response is not None else "unknown")
                logger.warning("HTTP error %s on %s", status, url[:120])
            except requests.exceptions.SSLError as exc:
                logger.warning("SSL error %s: %s", url[:120], exc)
            except Exception as exc:
                logger.warning("Error %s: %s", url[:120], exc)
            if attempt < self.max_retries:
                time.sleep(self.retry_delay * attempt)
        logger.error(
            "Failed to fetch %s after %d attempts", url[:120], self.max_retries
        )
        return None


# ---------------------------------------------------------------------------
# RSS Parsing Helpers
# ---------------------------------------------------------------------------

def _extract_source_from_title(title: str) -> str:
    """Extract the source name appended to a Google News title."""
    m = re.search(r"\s-\s([^\-]+)$", title)
    if m:
        return m.group(1).strip()
    return ""


def _strip_source_suffix(title: str) -> str:
    """Remove a trailing source suffix (e.g. ' - The Hindu') from a title."""
    return re.sub(r"\s-\s[^\-]+$", "", title).strip()


def _extract_description_text(desc_html: str) -> str:
    """Convert the HTML description snippet to plain text."""
    if not desc_html:
        return ""
    soup = BeautifulSoup(desc_html, "lxml")
    text = soup.get_text(separator=" ", strip=True)
    return unescape(text)


def parse_rss(xml_content: str, query: str) -> List[Dict[str, str]]:
    """Parse a Google News RSS XML string into a list of article dicts."""
    items: List[Dict[str, str]] = []
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as exc:
        logger.warning("Failed to parse RSS for '%s': %s", query, exc)
        return items

    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        source = (item.findtext("source") or "").strip()
        desc_html = (item.findtext("description") or "").strip()

        if not title or not link:
            continue

        if not source:
            source = _extract_source_from_title(title)
        clean_title = _strip_source_suffix(title)
        desc_text = _extract_description_text(desc_html)

        items.append({
            "title": clean_title,
            "url": link,  # Google News RSS link (functional in browser)
            "published_date": pub_date,
            "source": source,
            "description": desc_text,
            "collection_query": query,
        })
    return items


# ---------------------------------------------------------------------------
# Article Standardization & Crime Detection
# ---------------------------------------------------------------------------

def make_article_id(title: str, url: str) -> str:
    """Generate a stable article_id from the title and URL."""
    raw = "%s|%s" % (title.strip().lower(), url.strip())
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def detect_crime_type(text: str) -> str:
    """Rule-based crime type detection from article title + description."""
    t = str(text).lower()
    mapping = [
        ("Murder", ["murder", "homicide", "killed", "murdered", "death"]),
        ("Robbery", ["robbery", "robber", "dacoity", "heist"]),
        ("Theft", ["theft", "stolen", "burglary", "snatching", "snatcher", "thief"]),
        ("Assault", ["assault", "attack", "beaten", "injured", "thrash"]),
        ("Sexual Assault", ["sexual assault", "rape", "molest", "molestation"]),
        ("Kidnapping", ["kidnap", "abduct", "abduction"]),
        ("Fraud", ["fraud", "scam", "cheated", "fake", "counterfeit", "cheating"]),
        ("Cyber Crime", ["cyber crime", "cybercrime", "online scam", "phishing",
                          "hacking", "cyber fraud", "digital arrest"]),
        ("Drug Offence", ["drug", "narcotic", "ganja", "mdma", "meth",
                           "cocaine", "cannabis", "cough syrup"]),
        ("Extortion", ["extort", "blackmail", "threat"]),
        ("Vehicle Theft", ["vehicle theft", "stolen car", "stolen bike",
                            "two-wheeler theft"]),
        ("Domestic Violence", ["domestic violence", "dowry", "wife beating"]),
        ("Harassment", ["harassment", "stalking", "intimidation"]),
        ("Chain Snatching", ["chain snatching", "snatching"]),
        ("Vandalism", ["vandalism", "property damage"]),
        ("Smuggling", ["smuggling", "contraband"]),
        ("Other", ["police", "arrest", "criminal case", "fir", "crime"]),
    ]
    for label, kws in mapping:
        for kw in kws:
            if kw in t:
                return label
    return "Other"


def detect_locality(text: str) -> str:
    """Detect which Vellore locality is mentioned in the article text."""
    t = str(text).lower()
    for loc in sorted(LOCALITIES, key=len, reverse=True):
        if loc.lower() in t:
            return loc
    return ""


def standardize_article(raw: Dict[str, str]) -> Dict[str, str]:
    """Build a standardized article record from a raw RSS item."""
    title = raw.get("title", "")
    url = raw.get("url", "")
    desc = raw.get("description", "")
    query = raw.get("collection_query", "")
    full_text = "%s %s" % (title, desc)

    crime_type = detect_crime_type(full_text)
    locality = detect_locality(full_text)

    return {
        "article_id": make_article_id(title, url),
        "title": title,
        "published_date": raw.get("published_date", ""),
        "source": raw.get("source", ""),
        "url": url,
        "crime_type": crime_type,
        "district": "Vellore",  # tentative; validated later
        "locality": locality or "",
        "description": desc[:2000],
        "collection_query": query,
    }


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def normalize_title(title: str) -> str:
    """Normalize a title for near-duplicate comparison."""
    t = title.lower()
    t = re.sub(r"[^a-z0-9\s]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _titles_similar(t1: str, t2: str) -> bool:
    """Check if two titles are near-duplicates (high overlap)."""
    a = normalize_title(t1)
    b = normalize_title(t2)
    if not a or not b:
        return False
    if a == b:
        return True
    if a in b or b in a:
        return True
    ta = set(a.split())
    tb = set(b.split())
    if not ta or not tb:
        return False
    overlap = len(ta & tb) / max(len(ta), len(tb))
    return overlap >= 0.7


def deduplicate(articles: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], int]:
    """Remove duplicate URLs and near-duplicate titles.

    Returns (unique_articles, duplicates_removed).
    """
    unique: List[Dict[str, str]] = []
    seen_urls: Set[str] = set()
    seen_titles: List[str] = []
    removed = 0

    for art in articles:
        url = (art.get("url") or "").strip().lower()
        title = (art.get("title") or "").strip()

        if url in seen_urls:
            removed += 1
            continue

        if title:
            is_dup = False
            for existing in seen_titles:
                if _titles_similar(title, existing):
                    is_dup = True
                    break
            if is_dup:
                removed += 1
                continue

        seen_urls.add(url)
        seen_titles.append(title)
        unique.append(art)
    return unique, removed


def write_csv(path: Path, rows: List[Dict[str, str]], fieldnames: List[str]) -> None:
    """Write dictionaries to CSV using the supplied field order."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_localities_from_config() -> Set[str]:
    """Load the Vellore-district locality set from the config file."""
    names: Set[str] = set()
    try:
        with open(LOCALITY_CONFIG, "r", encoding="utf-8") as f:
            config = json.load(f)
        for loc in config.get("localities", []):
            names.add(loc["name"].lower())
            for alias in loc.get("aliases", []):
                names.add(alias.lower())
    except Exception as exc:
        logger.warning("Could not load locality config: %s", exc)
    for loc in LOCALITIES:
        names.add(loc.lower())
    return names


def apply_validation(articles: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]],
                                                               List[Dict[str, str]],
                                                               Dict[str, int]]:
    """Apply strict crime + Vellore relevance validation to collected articles.

    Reuses the validation logic from scripts/validate_data.py.

    Returns (validated_articles, excluded_articles, stats).
    """
    import pandas as pd
    from scripts.validate_data import validate_record

    vellore_localities = load_localities_from_config()

    validated: List[Dict[str, str]] = []
    excluded: List[Dict[str, str]] = []
    stats: Dict[str, int] = {"non_crime": 0, "non_vellore": 0,
                             "location_unverified": 0}

    for art in articles:
        row = pd.Series({
            "title": art.get("title", ""),
            "description": art.get("description", ""),
            "locality": art.get("locality", ""),
            "district": art.get("district", ""),
        })
        res = validate_record(row, vellore_localities)

        art = dict(art)
        art["is_crime_relevant"] = res["is_crime_relevant"]
        art["location_verified"] = res["location_verified"]
        art["relevance_reason"] = res["exclusion_reason"]

        if res["is_crime_relevant"] and res["is_vellore_relevant"]:
            if res["corrected_locality"]:
                art["locality"] = res["corrected_locality"]
            validated.append(art)
        else:
            excluded.append(art)
            if not res["is_crime_relevant"]:
                stats["non_crime"] += 1
            else:
                stats["non_vellore"] += 1
                if not res["location_verified"]:
                    stats["location_unverified"] += 1

    return validated, excluded, stats


def main() -> int:
    """Main entry point for the Vellore-specific crime collection pipeline."""
    print("=" * 70)
    print("VELLORE-SPECIFIC CRIME NEWS COLLECTION")
    print("=" * 70)
    print()

    # 1. Generate search queries
    queries = generate_queries()
    print("Generated %d search queries" % len(queries))
    print("  Sample: %s" % queries[:5])
    print()

    fetcher = HTTPFetcher()

    # 2. Collect candidate articles from all queries with runtime guard
    raw_items: List[Dict[str, str]] = []
    failed_queries: List[str] = []
    query_count = 0
    run_start = time.time()

    for i, query in enumerate(queries, 1):
        # Check runtime limit
        elapsed = time.time() - run_start
        if elapsed > MAX_RUNTIME_SECONDS:
            logger.warning("Runtime limit of %d seconds reached, stopping",
                          MAX_RUNTIME_SECONDS)
            print(f"Runtime limit of {MAX_RUNTIME_SECONDS}s reached, stopping gracefully")
            break

        query_count += 1
        url = build_rss_url(query)

        # Log progress with required format
        logger.info("[query %d/%d] [source Google News]",
                     query_count, len(queries))
        print(f"[query {query_count}/{len(queries)}] Query: {query}")

        xml_content = fetcher.fetch(url)
        if not xml_content:
            logger.error("[errors] Failed to fetch RSS for: %s", query)
            print(f"[errors] Failed to fetch RSS for: {query}")
            failed_queries.append(query)
            continue

        parsed = parse_rss(xml_content, query)
        item_count = len(parsed)
        logger.info("[articles discovered] %d for '%s'", item_count, query)
        logger.info("[articles fetched] total so far: %d", len(raw_items) + item_count)
        raw_items.extend(parsed)
        logger.info("[articles retained after this query: %d]", len(raw_items))
        print("  -> %d items for '%s'" % (item_count, query))
        time.sleep(RATE_LIMIT_DELAY)

        # Check MAX_CANDIDATES guard
        if len(raw_items) >= MAX_CANDIDATES:
            logger.warning("Reached MAX_CANDIDATES=%d, stopping query collection",
                          MAX_CANDIDATES)
            print(f"[errors] Reached MAX_CANDIDATES={MAX_CANDIDATES}, stopping")
            break

    print()
    print("Total raw RSS items collected: %d" % len(raw_items))
    print("Queries that failed: %d" % len(failed_queries))
    print()

    # 3. Standardize articles
    standardized = [standardize_article(r) for r in raw_items]

    # 4. Deduplicate
    unique, duplicates_removed = deduplicate(standardized)
    print("After de-duplication: %d candidates (removed %d duplicates)"
          % (len(unique), duplicates_removed))
    print()

    # 5. Save raw collection
    raw_fieldnames = ["article_id", "title", "published_date", "source", "url",
                      "crime_type", "district", "locality", "description",
                      "collection_query"]
    write_csv(RAW_OUTPUT, unique, raw_fieldnames)
    print("Raw candidates saved: %s" % RAW_OUTPUT)
    print()

    # 6. Run validation
    validated, excluded, stats = apply_validation(unique)

    # 7. Save validated dataset
    valid_fieldnames = raw_fieldnames + ["relevance_reason"]
    write_csv(VALIDATED_OUTPUT, validated, valid_fieldnames)

    # 8. Generate report
    write_report(REPORT_OUTPUT, queries, candidates_total=len(unique),
                 duplicates_removed=duplicates_removed,
                 validated=validated, excluded=excluded, stats=stats)

    # 9. Print summary
    print("=" * 70)
    print("COLLECTION SUMMARY")
    print("=" * 70)
    print("Total candidates collected:   %d" % len(unique))
    print("Duplicates removed:           %d" % duplicates_removed)
    print("Non-crime articles removed:   %d" % stats.get("non_crime", 0))
    print("Non-Vellore articles removed: %d" % stats.get("non_vellore", 0))
    print("Final Vellore crime articles: %d" % len(validated))
    print()
    print("Raw collection:       %s" % RAW_OUTPUT)
    print("Validated dataset:    %s" % VALIDATED_OUTPUT)
    print("Report:               %s" % REPORT_OUTPUT)
    print("=" * 70)

    return 0 if validated else 1


if __name__ == "__main__":
    sys.exit(main())

