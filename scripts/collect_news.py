"""
collect_news.py
===============
REAL source-backed news collection for CrimeSense (zero fabrication).

Permitted discovery channels (each robots.txt-verified, publicly accessible,
no auth/paywall/CAPTCHA bypass):
  * newindianexpress.com daily sitemaps  (robots: "Allow: /") — 2016→ present
  * dtnext.in daily sitemaps             (robots: "Allow: /") — 2016→ present
  * researcher_urls.txt                  (human-supplied article URLs)

Environment variables:
  CS_START_YEAR (default 2015)   CS_END_YEAR  (default: current year)
  CS_SITEMAPS   (default 60)     CS_MAX_FETCH (default 25)
  CS_RATE_LIMIT (default 1.0 s)  CS_SOURCE    (nie|dtnext|both)

Historical Vellore region: incidents may belong to places now in Ranipet or
Tirupattur (2019 reorganization). The collector keeps the SOURCE's own
terminology and flags `historical_region` for review instead of relabelling.
"""
from __future__ import annotations

import json
import os
import re
import time
import unicodedata
from collections import OrderedDict
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlparse

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCES_DIR = PROJECT_ROOT / "data" / "raw" / "collected_sources"
BATCH_DIR = SOURCES_DIR / "batches"
CANDIDATES_JSON = SOURCES_DIR / "collected_candidates.json"
SEEN_JSON = SOURCES_DIR / "collection_state_seen_urls.json"
RESEARCHER_URLS = SOURCES_DIR / "researcher_urls.txt"

TARGET_NEW_RECORDS = 1000          # goal only — never manufactured

UA = {"User-Agent": "CrimeSenseResearchBot/1.0 (+academic crime-data research)"}

# --- configuration -----------------------------------------------------------
START_YEAR = int(os.environ.get("CS_START_YEAR", "2015"))
END_YEAR = int(os.environ.get("CS_END_YEAR", str(date.today().year)))
MAX_SITEMAPS = int(os.environ.get("CS_SITEMAPS", "60"))
MAX_ARTICLE_FETCHES_PER_RUN = int(os.environ.get("CS_MAX_FETCH", "25"))
RATE_LIMIT = float(os.environ.get("CS_RATE_LIMIT", "1.0"))
SOURCE_FILTER = os.environ.get("CS_SOURCE", "both").lower()

# --- permitted sources (robots.txt-verified; see SOURCE_REGISTRY.md) ---------
SOURCES = {
    "nie": {
        "domain": "www.newindianexpress.com",
        "daily_pattern": ("https://www.newindianexpress.com/sitemap/"
                          "sitemap-daily-{date}.xml"),
        "first_year": 2016,
        "url_date_pattern": r"/(\d{4})/([A-Z][a-z]{2})/(\d{2})/",
        "url_months": {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5,
                       "Jun": 6, "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10,
                       "Nov": 11, "Dec": 12},
        "section_roots": ("/states/", "/cities/"),
        "parse_lastmod": False,
    },
    "dtnext": {
        "domain": "www.dtnext.in",
        "daily_pattern": "https://www.dtnext.in/sitemap/sitemap-daily-{date}.xml",
        "first_year": 2016,
        # DT slugs do NOT embed dates -> use sitemap <lastmod> per URL.
        "url_date_pattern": None,
        "url_months": {},
        "section_roots": ("/news/", "/city/", "/sports/", "/entertainment/"),
        "parse_lastmod": True,
    },
}

# --- Vellore historical region ------------------------------------------------
# Includes places moved to Ranipet / Tirupattur districts in the 2019 split.
VELLORE_TERMS = ("vellore", "katpadi", "gudiyatham", "gudiyattam", "pernambut",
                 "ambur", "vaniyambadi", "tirupattur", "tirupathur", "jolarpet",
                 "natrampalli", "nattrampalli", "sholingur", "sholinghur",
                 "walajapet", "walajah", "arcot", "ranipet", "melvisharam",
                 "arakkonam", "arakonam", "anaicut", "alangayam")

# 2019 reorganization: where these places sit TODAY (for review flags only —
# the SOURCE's own terminology is preserved in district/locality).
POST_2019_MOVED = {"ranipet": "Ranipet", "sholingur": "Ranipet",
                   "sholinghur": "Ranipet", "walajapet": "Ranipet",
                   "walajah": "Ranipet", "arcot": "Ranipet",
                   "melvisharam": "Ranipet", "arakkonam": "Ranipet",
                   "arakonam": "Ranipet", "vaniyambadi": "Tirupattur",
                   "tirupattur": "Tirupattur", "tirupathur": "Tirupattur",
                   "jolarpet": "Tirupattur", "natrampalli": "Tirupattur",
                   "nattrampalli": "Tirupattur", "alangayam": "Tirupattur",
                   "ambur": "Tirupattur", "pernambut": "Tirupattur"}

CRIME_TERMS = ("murder", "killed", "homicide", "assault", "attacked",
               "arrested", "arrest", "booked", "case registered", "theft",
               "steal", "stolen", "burglary", "burglar", "robbery", "robbed",
               "snatch", "kidnap", "abduct", "missing", "rape",
               "sexual assault", "molestation", "dowry", "harass",
               "domestic violence", "fraud", "cheat", "cheating", "duped",
               "cyber", "phishing", "online scam", "narcotic", "drugs",
               "ganja", "smuggl", "weapons", "arson", "body found",
               "found dead", "torture", "extortion")

CRIME_PAIRS = [("murder", "Murder"), ("homicide", "Murder"), ("killed", "Murder"),
               ("theft", "Theft"), ("steal", "Theft"), ("stolen", "Theft"),
               ("burglar", "Burglary"), ("robber", "Robbery"),
               ("snatch", "Chain Snatching"), ("kidnap", "Kidnapping"),
               ("abduct", "Kidnapping"), ("rape", "Sexual Assault"),
               ("sexual assault", "Sexual Assault"),
               ("molest", "Sexual Assault"), ("dowry", "Domestic Violence"),
               ("domestic violence", "Domestic Violence"),
               ("harass", "Assault"), ("assault", "Assault"),
               ("fraud", "Fraud"), ("cheat", "Cheating"), ("duped", "Cheating"),
               ("cyber", "Cyber Crime"), ("phishing", "Cyber Crime"),
               ("online scam", "Cyber Crime"), ("narcotic", "Drug Arrest"),
               ("drugs", "Drug Arrest"), ("ganja", "Drug Arrest"),
               ("smuggl", "Drug Arrest"), ("weapons", "Illegal Weapons"),
               ("arson", "Arson"), ("extortion", "Extortion")]

MONTHS = {m: i + 1 for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}


def http_get(url, timeout=25):
    """GET with polite rate limiting; returns text or None."""
    try:
        r = requests.get(url, headers=UA, timeout=timeout)
        time.sleep(RATE_LIMIT)
        if r.status_code == 200:
            return r.text
        print(f"  [skip] HTTP {r.status_code} {url[:90]}")
        return None
    except requests.RequestException as exc:
        print(f"  [err] {type(exc).__name__} {url[:90]}")
        return None


def load_seen():
    if SEEN_JSON.exists():
        return set(json.loads(SEEN_JSON.read_text(encoding="utf-8")))
    return set()


def save_seen(seen):
    SEEN_JSON.write_text(json.dumps(sorted(seen), indent=0), encoding="utf-8")


def extract_locs(xml_text):
    """Yield (url, lastmod) pairs from a sitemap XML document."""
    out = []
    for block in re.findall(
            r"<url>(.*?)</url>", xml_text or "", re.S):
        loc = re.search(r"<loc>\s*(.*?)\s*</loc>", block)
        last = re.search(r"<lastmod>\s*(.*?)\s*</lastmod>", block)
        if loc:
            out.append((loc.group(1).strip(),
                        (last.group(1).strip() if last else "")))
    if not out:  # plain <loc>-only sitemap
        out = [(u.strip(), "") for u in
               re.findall(r"<loc>\s*(.*?)\s*</loc>", xml_text or "")]
    return out


def active_sources():
    if SOURCE_FILTER == "both":
        return dict(SOURCES)
    return {k: v for k, v in SOURCES.items() if k == SOURCE_FILTER}


def discover_sitemaps(max_files):
    """Sweep permitted daily sitemaps newest-first across CS_START_YEAR..
    CS_END_YEAR for every active source. Returns {url: (source_key, lastmod)}.
    Stops after `max_files` successful sitemap downloads in this run."""
    found = {}
    today = date.today()
    ok_files = 0
    step = 2                      # sample every 2nd day per run (incremental)
    day = today
    floor = date(max(START_YEAR, 2015), 1, 1)
    while ok_files < max_files and day >= floor:
        for key, src in active_sources().items():
            if day.year < src["first_year"]:
                continue
            u = src["daily_pattern"].format(date=day.isoformat())
            xml = http_get(u)
            if xml is None:
                continue
            ok_files += 1
            for loc, lastmod in extract_locs(xml):
                low = loc.lower()
                if any(root in low for root in src["section_roots"]):
                    found[loc] = (key, lastmod)
            if ok_files >= max_files:
                break
        day -= timedelta(days=step)
    return found


def discover_researcher_urls():
    if not RESEARCHER_URLS.exists():
        return set()
    out = set()
    for line in RESEARCHER_URLS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and urlparse(line).scheme.startswith("http"):
            out.add(line)
    return out


def discover_researcher_urls():
    if not RESEARCHER_URLS.exists():
        return set()
    out = set()
    for line in RESEARCHER_URLS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and urlparse(line).scheme.startswith("http"):
            out.add(line)
    return out


def clean(text):
    text = re.sub(r"&[a-z]+;|&#\d+;", " ", text or "")
    return unicodedata.normalize("NFKD", re.sub(r"\s+", " ", text)).strip()


def meta(html, prop):
    m = re.search(
        rf'<meta[^>]+(?:property|name)="{prop}"[^>]+content="(.*?)"', html, re.I | re.S)
    if not m:
        m = re.search(
            rf'<meta[^>]+content="(.*?)"[^>]+(?:property|name)="{prop}"',
            html, re.I | re.S)
    return clean(m.group(1)) if m else ""


def extract_article(url, html, source_key="", lastmod=""):
    """Extract ONLY what the page actually declares. Never guess."""
    src = SOURCES.get(source_key, {})
    title = meta(html, "og:title") or ""
    description = (meta(html, "og:description")
                   or meta(html, "description"))[:500]
    published = ""

    # 1) JSON-LD datePublished
    for m in re.finditer(r'"datePublished"\s*:\s*"([^"]+)"', html):
        published = m.group(1)[:35]
        break
    # 2) Source-specific URL-embedded date (NIE: /YYYY/Mon/DD/)
    if not published and src.get("url_date_pattern"):
        m = re.search(src["url_date_pattern"], url)
        if m and m.group(2) in src["url_months"]:
            published = (f"{m.group(1)}-{src['url_months'][m.group(2)]:02d}-"
                         f"{m.group(3)}")
    # 3) Sitemap lastmod (DT Next slugs carry no date)
    if not published and lastmod:
        published = lastmod[:19].replace("T", " ")

    blob = f"{title} {description}".lower()
    hits = [t for t in VELLORE_TERMS if re.search(rf"\b{t}\b", blob)]
    locality = hits[0].title() if hits else ""
    moved_to = POST_2019_MOVED.get(hits[0]) if hits else ""

    return {
        "headline": title,
        "source_url": url,
        "source": urlparse(url).netloc.replace("www.", ""),
        "published_date": published,
        "incident_date": "",          # only when explicitly stated in text
        "crime_type_raw": "",
        "description": description,
        # SOURCE terminology preserved; historical-region flagged, not relabelled
        "district": "Vellore" if locality else "",
        "locality": locality,
        "state": "Tamil Nadu" if locality else "",
        "historical_region": moved_to if (locality and moved_to) else "",
        "latitude": "",
        "longitude": "",
        "location_confidence": "",
        "location_source": "",
        "severity_score": "",
        "risk_level": "",
    }


def _has_term(text_lw, term):
    """Word-boundary match so 'narcotics' never matches 'arcot'."""
    return re.search(rf"\b{re.escape(term)}\b", text_lw) is not None


def vellore_relevant(rec):
    blob = f"{rec['headline']} {rec['description']} {rec['source_url']}".lower()
    hits = [t.title() for t in VELLORE_TERMS if _has_term(blob, t)]
    rec["vellore_terms"] = ", ".join(hits)
    return bool(hits)


def crime_relevant(rec):
    blob = f"{rec['headline']} {rec['description']}".lower()
    hits = [t for t in CRIME_TERMS if re.search(rf"\b{re.escape(t)}\b", blob)]
    rec["crime_terms"] = ", ".join(hits)
    for kw, ct in CRIME_PAIRS:
        if re.search(rf"\b{re.escape(kw)}\b", blob):
            rec["crime_type_raw"] = ct
            break
    return bool(hits)


def normalize_title(t):
    t = unicodedata.normalize("NFKD", str(t or "")).lower()
    return re.sub(r"[^a-z0-9 ]+", " ", t).strip()


def write_batch(new_candidates):
    """Stage collected candidates in batches/ so expand_crimesense_dataset.py
    runs validation -> normalization -> dedup -> acceptance over them."""
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    path = BATCH_DIR / "batch_collected.json"
    rows = []
    if path.exists():
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            rows = []
    known = {(r.get("url") or r.get("source_url") or "").strip() for r in rows}
    added = 0
    skipped_non_crime = 0
    for r in new_candidates:
        url = (r.get("source_url") or "").strip()
        if not url or url in known:
            continue
        if not r.get("crime_type_raw"):
            # Not an individual crime incident (protest / policy / etc.) —
            # keep it in collected_candidates.json for review, do NOT stage.
            skipped_non_crime += 1
            continue
        rows.append({
            "article_id": "",
            "title": r["headline"],
            "headline": r["headline"],
            "published_date": r["published_date"],
            "incident_date": r.get("incident_date", ""),
            "source": r["source"],
            "url": url,
            "source_url": url,
            "crime_type": r.get("crime_type_raw", ""),
            "description": r["description"],
            "district": r["district"],
            "locality": r["locality"],
            "state": r["state"],
            "latitude": "",           # never guessed
            "longitude": "",
            "location_confidence": "",
            "location_source": "",
            "severity_score": "",     # scoring pipeline's job
            "risk_level": "",
            "historical_region": r.get("historical_region", ""),
        })
        known.add(url)
        added += 1
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nbatch file: {path.name}  total_rows={len(rows)} (+{added} new, "
          f"{skipped_non_crime} non-crime skipped)")


def report(stats, candidate_total):
    remaining = max(0, TARGET_NEW_RECORDS - candidate_total - 89)
    lines = ["# Collection Run Report", "",
             f"- Discovered URLs: **{stats['discovered']}**",
             f"- Successfully fetched: **{stats['fetched']}**",
             f"- Parsed (valid article pages): **{stats['parsed']}**",
             f"- Vellore-region candidates: **{stats['vellore_candidates']}**",
             f"- Crime candidates (individual incidents): "
             f"**{stats['crime_candidates']}**",
             f"- Invalid (no usable headline): **{stats['invalid']}**",
             f"- Duplicates (vs existing 89 / earlier runs): **{stats['duplicates']}**",
             f"- Rejected (not Vellore-region / not crime): **{stats['rejected']}**",
             f"- Accepted into candidate pool: **{stats['accepted']}**",
             f"- Candidate pool total: **{candidate_total}**",
             f"- TARGET_NEW_RECORDS: {TARGET_NEW_RECORDS} (goal only)",
             f"- Remaining to reach goal: **{remaining}**", "",
             "> Zero-fabrication: only pages actually fetched and parsed by this",
             "> collector are recorded. Coordinates and severity/risk stay empty."]

    out = PROJECT_ROOT / "data" / "analysis" / "collection_run_report.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for line in lines:
        if line.startswith("- ") or line.startswith("#"):
            print(line)


def main():
    print("=== CrimeSense news collector ===")
    seen = load_seen()
    print(f"previously seen URLs: {len(seen)}")
    print(f"window {START_YEAR}-{END_YEAR} | sources: {SOURCE_FILTER} "
          f"| sitemaps<= {MAX_SITEMAPS} | fetch<= {MAX_ARTICLE_FETCHES_PER_RUN} "
          f"| rate {RATE_LIMIT}s")

    print("[1/2] multi-source sitemap sweep ...")
    disc = discover_sitemaps(MAX_SITEMAPS)
    print(f"      article URLs surfaced: {len(disc)}")

    print("[2/2] researcher_urls.txt ...")
    ru = discover_researcher_urls()
    print(f"      researcher urls: {len(ru)}")
    for u in ru:
        disc.setdefault(u, ("researcher", ""))

    stats = OrderedDict((k, 0) for k in (
        "discovered", "fetched", "parsed", "vellore_candidates",
        "crime_candidates", "invalid", "duplicates", "accepted", "rejected"))
    stats["discovered"] = len(disc)

    # Vellore-region URLs only, not processed before (word-boundary match).
    term_re = re.compile(rf"\b({'|'.join(VELLORE_TERMS)})\b", re.I)
    fresh = [(u, key, lm) for u, (key, lm) in sorted(disc.items())
             if u not in seen and term_re.search(u.lower())]
    print(f"fresh vellore-region URLs to fetch: {len(fresh)} "
          f"(cap {MAX_ARTICLE_FETCHES_PER_RUN})")

    import csv as _csv
    final_csv = PROJECT_ROOT / "data" / "final" / "crimesense_database_import.csv"
    with open(final_csv, encoding="utf-8") as fh:
        known_titles = {normalize_title(r.get("title", ""))
                        for r in _csv.DictReader(fh)}

    candidates = []
    for url, key, lastmod in fresh:
        if stats["fetched"] >= MAX_ARTICLE_FETCHES_PER_RUN:
            print("per-run fetch cap reached; run again to continue")
            break
        html = http_get(url)
        if not html or len(html) < 20000:
            continue                       # not a real article page
        stats["fetched"] += 1
        rec = extract_article(url, html, key, lastmod)
        seen.add(url)                      # processed even if rejected
        if not rec["headline"]:
            stats["invalid"] += 1
            continue
        stats["parsed"] += 1
        if not vellore_relevant(rec):
            stats["rejected"] += 1
            continue
        stats["vellore_candidates"] += 1
        if not crime_relevant(rec):
            stats["rejected"] += 1
            continue
        stats["crime_candidates"] += 1
        if normalize_title(rec["headline"]) in known_titles:
            stats["duplicates"] += 1
            continue
        known_titles.add(normalize_title(rec["headline"]))
        candidates.append(rec)
        stats["accepted"] += 1

    save_seen(seen)

    prev = json.loads(CANDIDATES_JSON.read_text(encoding="utf-8")) \
        if CANDIDATES_JSON.exists() else []
    merged = {r["source_url"]: r for r in prev}
    for r in candidates:
        merged[r["source_url"]] = r
    CANDIDATES_JSON.write_text(
        json.dumps(list(merged.values()), indent=2, ensure_ascii=False),
        encoding="utf-8")
    write_batch(candidates)
    report(stats, len(merged))


if __name__ == "__main__":
    main()
