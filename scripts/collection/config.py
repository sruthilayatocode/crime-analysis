"""Central configuration for the CrimeSense collection pipeline.

EVERY tunable lives here so behaviour is configurable "from one place"
(requirement). Nothing downstream hard-codes limits.
"""
from __future__ import annotations

from pathlib import Path

# --------------------------------------------------------------------------
# Paths (additive to the existing project layout; nothing is overwritten)
# --------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
FINAL_DIR = DATA_DIR / "final"
ANALYSIS_DIR = DATA_DIR / "analysis"

# New pipeline-owned directories (created on demand).
CANDIDATE_DIR = RAW_DIR / "candidates"           # discovered + fetched candidates
INCIDENT_DIR = PROCESSED_DIR / "incidents"       # validated incident dataset
PROVENANCE_DIR = DATA_DIR / "provenance"         # provenance link tables
CACHE_DIR = RAW_DIR / "cache"                    # raw HTTP cache (cache-aware)
LOG_DIR = PROJECT_ROOT / "logs" / "collection"

# Persistent, resumable state.
STATE_DIR = RAW_DIR / "candidates" / "_state"
SEEN_URLS_JSON = STATE_DIR / "seen_urls.json"          # discovery ledger
FETCHED_JSON = STATE_DIR / "fetched.json"              # url -> extraction summary
SOURCE_STATS_JSON = STATE_DIR / "source_stats.json"    # per-source yield tracking
ROBOTS_CACHE_JSON = STATE_DIR / "robots_cache.json"    # parsed robots.txt rules

# Protected inputs (READ-ONLY; must never be modified by this pipeline).
PROTECTED_FINAL_CSV = FINAL_DIR / "crimesense_database_import.csv"
EXISTING_ACCEPTED_JSON = PROCESSED_DIR / "accepted_incidents.json"

# Outputs (new files only).
CANDIDATES_JSONL = CANDIDATE_DIR / "candidates.jsonl"
INCIDENTS_JSON = INCIDENT_DIR / "incidents.json"
INCIDENTS_CSV = FINAL_DIR / "crimesense_incidents_v2.csv"      # incident-level
CANONICAL_CSV = FINAL_DIR / "crimesense_import_v2_canonical.csv"  # 15-col, backend-compatible
PROVENANCE_CSV = PROVENANCE_DIR / "incident_provenance.csv"
COURT_CANDIDATES_JSONL = CANDIDATE_DIR / "court_candidates.jsonl"

# --------------------------------------------------------------------------
# Network / politeness (all configurable)
# --------------------------------------------------------------------------
USER_AGENT = ("CrimeSenseResearchBot/1.0 (+academic crime-hotspot research; "
              "contact: project maintainer)")
REQUEST_DELAY = 0.35          # seconds between requests to the SAME host
REQUEST_TIMEOUT = 30          # per-request timeout (seconds)
RETRY_COUNT = 3               # retries per URL on transient failure
RETRY_BACKOFF = 1.5           # exponential backoff factor
CONCURRENCY = 8               # parallel workers (per-host politeness still enforced)
RESPECT_ROBOTS = True         # never bypass robots.txt
CACHE_ENABLED = True          # serve repeated fetches from disk cache
CACHE_TTL_DAYS = 30           # cached pages older than this are re-fetched

# --------------------------------------------------------------------------
# Collection volume limits (configurable; NO tiny global cap)
# --------------------------------------------------------------------------
TARGET_INCIDENTS = 1000       # research goal (not a hard stop)
MAX_RESULTS_PER_QUERY = 250   # per generated query
MAX_PAGES_PER_QUERY = 5       # pagination depth per query
MAX_ARTICLES_PER_SOURCE = 5000  # ceiling per source per run
MAX_SITEMAPS_PER_RUN = 4000   # sitemap documents per run (ramp-controlled)
MAX_ARTICLE_FETCHES_PER_RUN = 3000  # article pages fetched per run

# --------------------------------------------------------------------------
# Validation / acceptance rules
# --------------------------------------------------------------------------
# Only these geographic scopes enter the MAIN incident dataset.
ACCEPT_SCOPES = ("VELLORE_CITY", "VELLORE_DISTRICT")
# Historic-vellore-but-now-elsewhere records go to a flagged side table only.
SIDE_TABLE_SCOPES = ("HISTORIC_VELLORE_OUT_OF_SCOPE",)
MIN_DESCRIPTION_CHARS = 60    # too-thin articles are rejected
MIN_TITLE_CHARS = 12

# Confidence gate: only HIGH/MEDIUM enter the validated incident dataset.
ACCEPT_CONFIDENCE = ("HIGH", "MEDIUM")

# --------------------------------------------------------------------------
# Deduplication
# --------------------------------------------------------------------------
# Incidents whose (date, locality, crime_type) match AND whose titles are at
# least this similar are treated as the same real-world incident.
DEDUPE_TITLE_SIMILARITY = 0.62
DEDUPE_DATE_WINDOW_DAYS = 5   # +- window for same-incident publication lag

# --------------------------------------------------------------------------
# Historical search windows (used by the query matrix)
# --------------------------------------------------------------------------
HISTORICAL_PERIODS = [
    ("1976-1989", 1976, 1989),
    ("1990-1999", 1990, 1999),
    ("2000-2009", 2000, 2009),
    ("2010-2019", 2010, 2019),
    ("2020-2026", 2020, 2026),
]

# --------------------------------------------------------------------------
# Aliases used across modules (single source of truth above).
# --------------------------------------------------------------------------
INCIDENTS_DIR = INCIDENT_DIR                 # legacy name compatibility
PROVENANCE_DIR = PROVENANCE_DIR
MAX_SITEMAPS_PER_SOURCE_PER_RUN = MAX_SITEMAPS_PER_RUN  # per-source cap
SITEMAP_DELAY = REQUEST_DELAY                # politeness between sitemaps

