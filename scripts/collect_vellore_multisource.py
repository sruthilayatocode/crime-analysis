"""Multi-source Vellore crime news harvester (sitemap-index driven).

Every source here is a reputable outlet listed in
data/raw/collected_sources/SOURCE_REGISTRY.md whose robots.txt publishes
(BOTH declared in robots.txt AND served publicly, no auth/paywall/CAPTCHA
bypass):

  * www.newindianexpress.com   (robots: Allow /, sitemap.xml -> 39 dailies)
  * www.dtnext.in              (robots: Allow /, sitemap.xml -> 94 dailies)
  * www.maalaimalar.com        (robots: sitemap.xml -> 4,871 dailies 2011+)
  * www.dailythanthi.com       (robots: sitemap.xml -> 3,566 dailies)
  * www.thenewsminute.com      (robots: sitemap.xml -> 4,475 dailies 2014+)
  * www.dinamalar.com          (robots: sitemap_index.xml -> 424 dailies)

Strategy: fetch each source's sitemap index ONCE, then walk its daily sitemaps
newest-first. Article URLs are matched on the publisher's own URL slug for a
Vellore-region place name (and, by default, a crime term). The article page is
then actually fetched and its own metadata parsed via collect_news.extract_article.

Integrity rules preserved from collect_news.py:
  * only pages actually fetched + parsed are recorded;
  * no coordinates/severity invented (left blank for the scoring pipeline);
  * source terminology kept; historical_region flagged for the 2019 split;
  * dedup by normalized title + source URL against the 89 canonical records.

Output: data/raw/collected_sources/batches/batch_harvested.json (same schema as
batch_collected.json) so expand_crimesense_dataset.py ingests it unchanged.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import csv as _csv
import json
import re
import sys
import time
from collections import Counter, OrderedDict
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
import collect_news as cn  # noqa: E402

BATCH_DIR = cn.BATCH_DIR
CANDIDATES_JSON = cn.CANDIDATES_JSON
SEEN_JSON = cn.SEEN_JSON
EXISTING_FINAL = PROJECT_ROOT / "data" / "final" / "crimesense_database_import.csv"
UA = cn.UA

from requests.adapters import HTTPAdapter  # noqa: E402

try:
    from urllib3.util.retry import Retry
    _RETRY = Retry(total=2, backoff_factor=0.3,
                   status_forcelist=[429, 500, 502, 503, 504])
except Exception:
    _RETRY = None

SESSION = cn.requests.Session()
SESSION.headers.update(UA)
if _RETRY is not None:
    _ADAPTER = HTTPAdapter(max_retries=_RETRY, pool_connections=32, pool_maxsize=64)
    SESSION.mount("http://", _ADAPTER)
    SESSION.mount("https://", _ADAPTER)
# --- permitted sources with sitemap indexes (see SOURCE_REGISTRY.md) ---------
# daily_re captures the publish date when the sitemap name carries one.
MULTI_SOURCES = {
    "nie": {
        "index": "https://www.newindianexpress.com/sitemap.xml",
        "daily_re": r"sitemap-daily-(\d{4})-(\d{2})-(\d{2})\.xml",
        "date_order": "ymd",
        "first_year": 2016,
        "section_roots": ("/states/", "/cities/"),
    },
    "dtnext": {
        "index": "https://www.dtnext.in/sitemap.xml",
        "daily_re": r"sitemap-daily-(\d{4})-(\d{2})-(\d{2})\.xml",
        "date_order": "ymd",
        "first_year": 2016,
        "section_roots": ("/news/", "/city/", "/sports/", "/entertainment/"),
    },
    "maalaimalar": {
        "index": "https://www.maalaimalar.com/sitemap.xml",
        "daily_re": r"sitemap-daily-(\d{4})-(\d{2})-(\d{2})\.xml",
        "date_order": "ymd",
        "first_year": 2011,
        "section_roots": ("/news/",),
    },
    "dailythanthi": {
        "index": "https://www.dailythanthi.com/sitemap.xml",
        "daily_re": r"sitemap-daily-(\d{4})-(\d{2})-(\d{2})\.xml",
        "date_order": "ymd",
        "first_year": 2012,
        "section_roots": ("/news/",),
    },
    "thenewsminute": {
        "index": "https://www.thenewsminute.com/sitemap.xml",
        "daily_re": r"sitemap-daily-(\d{4})-(\d{2})-(\d{2})\.xml",
        "date_order": "ymd",
        "first_year": 2014,
        "section_roots": ("/",),
    },
    "dinamalar": {
        "index": "https://www.dinamalar.com/sitemap_index.xml",
        "daily_re": r"sitemap_(\d{2})-(\d{2})-(\d{4})\.xml",
        "date_order": "dmy",
        "first_year": 2025,
        "section_roots": ("/news/",),
    },
}

# Vellore-region place spellings -> canonical locality label.
LOCALITY_MAP = OrderedDict([
    ("vellore", "Vellore"),
    ("katpadi", "Katpadi"),
    ("gudiyatham", "Gudiyatham"),
    ("gudiyattam", "Gudiyatham"),
    ("pernambut", "Pernambut"),
    ("pernambut", "Pernambut"),
    ("ambur", "Ambur"),
    ("vaniyambadi", "Vaniyambadi"),
    ("tirupattur", "Tirupattur"),
    ("tirupathur", "Tirupattur"),
    ("tiruppattur", "Tirupattur"),
    ("jolarpet", "Jolarpet"),
    ("natrampalli", "Natrampalli"),
    ("nattrampalli", "Natrampalli"),
    ("sholingur", "Sholingur"),
    ("sholinghur", "Sholingur"),
    ("walajapet", "Walajapet"),
    ("walajah", "Walajapet"),
    ("arcot", "Arcot"),
    ("ranipet", "Ranipet"),
    ("ranipettai", "Ranipet"),
    ("melvisharam", "Melvisharam"),
    ("arakkonam", "Arakkonam"),
    ("arakonam", "Arakkonam"),
    ("anaicut", "Anaicut"),
    ("alangayam", "Alangayam"),
])
LOCALITY_RE = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in LOCALITY_MAP) + r")\b", re.I)
# Crime terms as they appear in publisher URL slugs (English transliteration is
# used by all six sources even where the article body is Tamil).
CRIME_SLUG_RE = re.compile(
    r"(murder|kill|homicid|assault|attack|stab|shot|shoot|gun|"
    r"arrest|booked|held|detain|remand|police|case-registered|fir|"
    r"theft|steal|stolen|burglar|robber|dacoit|snatch|chain-snatch|"
    r"kidnap|abduct|missing|rape|sexual|molest|dowry|harass|"
    r"fraud|cheat|dupe|scam|cyber|phish|"
    r"narcotic|drug|ganja|smuggl|sand-smuggl|"
    r"weapon|arson|body-found|found-dead|dead-body|"
    r"extortion|bribe|corruption|ganja|torched|poison|"
    r"peddler|smuggler|accused|convict|sentenced|acquitted|"
    r"cyber-crime|honey-trap|id-theft|cattle-theft|bike-theft|"
    r"woman-attacked|girl-attacked|assaulted|hurled|stone|"
    r"cheating-case|fraudster|swindl)",
    re.I)


def fetch(url, timeout=20):
    try:
        r = SESSION.get(url, timeout=timeout)
        if r.status_code == 200:
            return r.text
        return None
    except Exception:
        return None


def sitemap_locs(xml_text):
    out = []
    for block in re.findall(r"<url>(.*?)</url>", xml_text or "", re.S):
        loc = re.search(r"<loc>\s*(.*?)\s*</loc>", block)
        last = re.search(r"<lastmod>\s*(.*?)\s*</lastmod>", block)
        if loc:
            out.append((loc.group(1).strip(), last.group(1).strip() if last else ""))
    if not out:
        out = [(u.strip(), "") for u in
               re.findall(r"<loc>\s*(.*?)\s*</loc>", xml_text or "")]
    return out


def daily_date(url, spec):
    """Return YYYY-MM-DD for a dated daily sitemap URL, else ''."""
    m = re.search(spec["daily_re"], url, re.I)
    if not m:
        return ""
    g = m.groups()
    if spec["date_order"] == "ymd":
        return f"{g[0]}-{g[1]}-{g[2]}"
    if spec["date_order"] == "dmy":
        return f"{g[2]}-{g[1]}-{g[0]}"
    return ""


def locality_from_url(url):
    m = LOCALITY_RE.search(url)
    return LOCALITY_MAP.get(m.group(1).lower(), "") if m else ""


def crawl_index(source_key, start_year, end_year, target_rows=0):
    """Fetch one source's sitemap index -> [(daily_url, date_str)] newest first."""
    spec = MULTI_SOURCES[source_key]
    xml = fetch(spec["index"], timeout=35)
    if not xml:
        print(f"  [{source_key}] index fetch FAILED")
        return []
    rows = []
    for loc, _ in sitemap_locs(xml):
        ds = daily_date(loc, spec)
        if not ds:
            continue
        y = int(ds[:4])
        if y < max(start_year, spec["first_year"]) or y > end_year:
            continue
        rows.append((loc, ds))
    rows.sort(key=lambda r: r[1], reverse=True)
    if target_rows and len(rows) > target_rows:
        rows = rows[:target_rows]
    print(f"  [{source_key}] index OK: {len(rows)} daily sitemaps in window "
          f"(first_year={spec['first_year']})")
    return rows
# <<<C3>>>