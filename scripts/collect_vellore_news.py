"""Fast, integrity-preserving Vellore-crime news collector (concurrent).

Reuses the EXACT extraction + filtering helpers from collect_news.py so the
integrity rules stay identical (real article pages only, word-boundary Vellore
locality match, crime-term confirmation, no coordinate invention). The only
change vs collect_news.py is concurrency for sitemaps + article pages, so we can
scale past the old 25-fetch/run cap and approach the 300-record target.

Output: writes batches/batch_harvested.json in the SAME schema as
batch_collected.json, so expand_crimesense_dataset.py ingests it unchanged.
"""
from __future__ import annotations
import argparse, concurrent.futures, json, os, re, sys, time, csv as _csv
from collections import OrderedDict, Counter
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
import collect_news as cn  # noqa: E402  (project helpers/constants)

SOURCES = cn.SOURCES
UA = cn.UA
VELLORE_TERMS = cn.VELLORE_TERMS
BATCH_DIR = cn.BATCH_DIR
CANDIDATES_JSON = cn.CANDIDATES_JSON
SEEN_JSON = cn.SEEN_JSON
EXISTING_FINAL = PROJECT_ROOT / "data" / "final" / "crimesense_database_import.csv"

url_term_re = re.compile(rf"\b({'|'.join(VELLORE_TERMS)})\b", re.I)

# Crime keywords that, when present in an article URL slug, signal a likely
# individual-crime story. Used to keep fetches targeted + high-precision; the
# article BODY is still re-validated by collect_news.crime_relevant().
CRIME_URL_RE = re.compile(
    r"\b(arrest|arrested|arrests|murder|killed|killing|deaths|died|"
    r"found-dead|stabbed|stab|shot|shooting|gunman|shootout|attack|attacked|"
    r"assault|raped|rape|sexual|harassment|theft|stolen|stealing|robbery|robbed|"
    r"burglary|burglar|broke|loot|looted|looter|acid|dacoity|dacoit|extort|"
    r"extortion|cheat|cheating|fraud|scam|scammer|narcotics|drugs|drug|smuggl|"
    r"traffick|trafficking|kidnap|abduct|abduction|dowry|bribery|corruption|"
    r"bomb|blast|riot|weapon|explosive|terror|terrorist|missing|recovered)\b",
    re.I)

# Shared session with connection pooling + retries (per-call sessions caused
# socket exhaustion / low success under concurrency).
from requests.adapters import HTTPAdapter
try:
    from urllib3.util.retry import Retry
    _retry = Retry(total=2, backoff_factor=0.3,
                   status_forcelist=[429, 500, 502, 503, 504])
except Exception:
    _retry = None
SESSION = cn.requests.Session()
SESSION.headers.update(UA)
if _retry is not None:
    _adapter = HTTPAdapter(max_retries=_retry, pool_connections=16, pool_maxsize=32)
    SESSION.mount("http://", _adapter)
    SESSION.mount("https://", _adapter)


def sitemap_locs(xml_text):
    out = []
    for block in re.findall(r"<url>(.*?)</url>", xml_text or "", re.S):
        loc = re.search(r"<loc>\s*(.*?)\s*</loc>", block)
        last = re.search(r"<lastmod>\s*(.*?)\s*</lastmod>", block)
        if loc:
            out.append((loc.group(1).strip(), last.group(1).strip() if last else ""))
    if not out:
        out = [(u.strip(), "") for u in re.findall(r"<loc>\s*(.*?)\s*</loc>", xml_text or "")]
    return out


def vellore_urls_in_sitemap(xml_text, source_key):
    """Article URLs from a sitemap whose path is a permitted news section,
    is located in a Vellore-region place, AND looks like a crime story."""
    src = SOURCES[source_key]
    keep = []
    for loc, lastmod in sitemap_locs(xml_text):
        low = loc.lower()
        if not any(root in low for root in src["section_roots"]):
            continue
        if url_term_re.search(loc) and CRIME_URL_RE.search(loc):
            keep.append((loc, lastmod))
    return keep


def load_known():
    known_titles = set()
    if EXISTING_FINAL.exists():
        with open(EXISTING_FINAL, encoding="utf-8") as fh:
            for r in _csv.DictReader(fh):
                known_titles.add(cn.normalize_title(r.get("title", "")))
    seen_urls = set()
    if SEEN_JSON.exists():
        try:
            seen_urls = set(json.loads(SEEN_JSON.read_text(encoding="utf-8")))
        except Exception:
            seen_urls = set()
    cand_urls = set()
    if CANDIDATES_JSON.exists():
        try:
            for r in json.loads(CANDIDATES_JSON.read_text(encoding="utf-8")):
                cand_urls.add(r.get("source_url") or r.get("url") or "")
        except Exception:
            pass
    return known_titles, seen_urls | cand_urls


def fetch(url, timeout=25):
    try:
        r = SESSION.get(url, timeout=timeout)
        if r.status_code == 200:
            return r.text
        print(f"  [skip] HTTP {r.status_code} {url[:80]}")
        return None
    except Exception as exc:
        print(f"  [err] {type(exc).__name__} {url[:80]}")
        return None

def extract_record(url, source_key, lastmod):
    html = fetch(url, timeout=25)
    if not html or len(html) < 20000:
        return None, "not_article"
    rec = cn.extract_article(url, html, source_key, lastmod)
    rec.setdefault("source_url", url)
    rec.setdefault("url", url)
    if not rec.get("headline"):
        return None, "no_headline"
    if not cn.vellore_relevant(rec):
        return None, "not_vellore"
    if not cn.crime_relevant(rec):
        return None, "not_crime"
    return rec, "ok"


def to_batch_record(rec):
    return {
        "article_id": "", "title": rec.get("headline", ""), "headline": rec.get("headline", ""),
        "published_date": rec.get("published_date", ""), "incident_date": "",
        "source": rec.get("source", ""),
        "url": rec.get("source_url") or rec.get("url", ""),
        "source_url": rec.get("source_url") or rec.get("url", ""),
        "crime_type": rec.get("crime_type_raw", ""), "crime_type_raw": rec.get("crime_type_raw", ""),
        "description": rec.get("description", ""),
        "district": rec.get("district") or ("Vellore" if rec.get("locality") else ""),
        "locality": rec.get("locality", ""), "state": rec.get("state") or "Tamil Nadu",
        "latitude": "", "longitude": "", "location_confidence": "", "location_source": "",
        "severity_score": "", "risk_level": "", "historical_region": rec.get("historical_region", ""),
        "_headline": rec.get("headline", ""), "_state": rec.get("state") or "Tamil Nadu",
        "_incident_date": "", "_url": rec.get("source_url") or rec.get("url", ""),
    }
def _fetch_sitemap(day_key):
    day, key = day_key
    src = SOURCES[key]
    u = src["daily_pattern"].format(date=day.isoformat())
    xml = fetch(u, timeout=20)
    if not xml:
        return []
    return [(loc, key, lastmod) for loc, lastmod in vellore_urls_in_sitemap(xml, key)]


def _fetch_daily(dl_key):
    day_url, key = dl_key
    xml = fetch(day_url, timeout=20)
    if not xml or "<loc" not in xml.lower():
        return []
    return vellore_urls_in_sitemap(xml, key)


def crawl_from_indexes(source_filter, workers=12):
    """Fetch each source's /sitemap.xml index once, then all listed daily
    sitemaps concurrently. Eliminates the 404 waste of date-based scanning."""
    urls = OrderedDict()
    n_idx = 0
    n_daily = 0
    for key in list(SOURCES.keys()):
        if source_filter != "both" and key != source_filter:
            continue
        src = SOURCES[key]
        idx = f"https://{src['domain']}/sitemap.xml"
        xml = fetch(idx, timeout=35)
        if not xml or "<loc" not in xml.lower():
            print(f"  index fetch failed: {idx}")
            continue
        n_idx += 1
        daily = [(loc, key) for loc, _ in sitemap_locs(xml)
                 if "sitemap-daily" in loc.lower()]
        n_daily += len(daily)
        print(f"  {key}: {len(daily)} daily sitemaps in index")
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
            for res in ex.map(_fetch_daily, daily):
                for loc, lastmod in res:
                    urls.setdefault(loc, (key, lastmod))
    return urls, n_idx, n_daily


def crawl_sitemaps(start_year, end_year, sitemap_budget, source_filter,
                   workers=12, url_target=0):
    today = date.today()
    floor = date(max(start_year, 2015), 1, 1)
    days = []
    d = today
    # Newest first, step 1 day, both sources -> richer Vellore coverage.
    while d >= floor and len(days) < sitemap_budget:
        for key in list(SOURCES.keys()):
            if source_filter != "both" and key != source_filter:
                continue
            if d.year < SOURCES[key]["first_year"]:
                continue
            days.append((d, key))
            if len(days) >= sitemap_budget:
                break
        d -= timedelta(days=1)
    urls = OrderedDict()
    ok = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_fetch_sitemap, dk): dk for dk in days}
        for fut in concurrent.futures.as_completed(futs):
            res = fut.result()
            if res:
                ok += 1
                for loc, key, lastmod in res:
                    urls.setdefault(loc, (key, lastmod))
            if url_target and len(urls) >= url_target:
                for f in futs:
                    f.cancel()
                break
    return urls, ok, len(days)
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start-year", type=int, default=2016)
    ap.add_argument("--end-year", type=int, default=date.today().year)
    ap.add_argument("--sitemap-budget", type=int, default=400)
    ap.add_argument("--fetch-budget", type=int, default=500)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--source", default="both", choices=["both", "nie", "dtnext"])
    ap.add_argument("--index", action="store_true", help="crawl sitemap indexes instead of date scan")
    ap.add_argument("--out", default=str(BATCH_DIR / "batch_harvested.json"))
    args = ap.parse_args()

    print(f"=== Vellore news collector (concurrent) ===")
    print(f"years {args.start_year}-{args.end_year} | sitemaps<={args.sitemap_budget} | "
          f"fetch<={args.fetch_budget} | workers={args.workers} | src={args.source}")

    print("[1] crawling permitted daily sitemaps (concurrent)...")
    t0 = time.time()
    if args.index:
        print("[1] crawling sitemap indexes (no 404 waste)...")
        urls, n_idx, n_daily = crawl_from_indexes(args.source, workers=args.workers)
        n_sitemaps = n_daily
        print(f"    indexes={n_idx} daily-sitemaps-in-index={n_daily} | Vellore+crime URLs surfaced: {len(urls)}")
    else:
        print("[1] crawling permitted daily sitemaps (concurrent)...")
        t0 = time.time()
        urls, n_sitemaps, n_attempts = crawl_sitemaps(
            args.start_year, args.end_year, args.sitemap_budget, args.source,
            workers=args.workers)
        print(f"    sitemaps fetched ok: {n_sitemaps} | Vellore+crime URLs surfaced: {len(urls)} (elapsed {time.time()-t0:.1f}s)")
    print(f"    sitemaps fetched: {n_sitemaps} | Vellore-URLs surfaced: {len(urls)} "
          f"(elapsed {time.time()-t0:.1f}s)")

    known_titles, known_urls = load_known()
    fresh = [(u, k, lm) for u, (k, lm) in urls.items() if u not in known_urls]
    fresh.sort(key=lambda x: x[0])
    print(f"    fresh URLs (not seen / not in 89): {len(fresh)} (cap {args.fetch_budget})")

    seen_now = set()
    records = []
    stats = Counter()
    done = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        fut_to = {ex.submit(extract_record, u, k, lm): u for u, k, lm in fresh}
        for fut in concurrent.futures.as_completed(fut_to):
            if done >= args.fetch_budget:
                break
            try:
                rec, reason = fut.result()
            except Exception:
                stats["error"] += 1
                continue
            done += 1
            stats["fetched"] += 1
            if rec is None:
                stats[reason] += 1
                continue
            nt = cn.normalize_title(rec["headline"])
            if nt in known_titles or nt in seen_now:
                stats["dup_title"] += 1
                continue
            seen_now.add(nt)
            known_titles.add(nt)
            records.append(to_batch_record(rec))
            stats["accepted"] += 1

    # Merge into collected_candidates.json (collect_news accumulator).
    merged = []
    if CANDIDATES_JSON.exists():
        try:
            merged = json.loads(CANDIDATES_JSON.read_text(encoding="utf-8"))
        except Exception:
            merged = []
    existing_cand_urls = {r.get("source_url") or r.get("url") or "" for r in merged}
    for rec in records:
        u = rec["source_url"]
        if u in existing_cand_urls:
            continue
        existing_cand_urls.add(u)
        merged.append({
            "headline": rec["headline"], "source_url": u, "url": u,
            "source": rec["source"], "published_date": rec["published_date"],
            "incident_date": "", "crime_type_raw": rec.get("crime_type_raw", ""),
            "description": rec["description"], "district": rec["district"],
            "locality": rec["locality"], "state": rec["state"],
            "latitude": "", "longitude": "", "location_confidence": "",
            "location_source": "", "severity_score": "", "risk_level": "",
            "vellore_terms": rec.get("locality", ""),
            "crime_terms": rec.get("crime_type_raw", ""),
            "historical_region": rec.get("historical_region", ""),
        })
    CANDIDATES_JSON.write_text(json.dumps(merged, indent=2, ensure_ascii=False),
                               encoding="utf-8")

    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    batch_path = Path(args.out)
    prior = []
    if batch_path.exists():
        try:
            prior = json.loads(batch_path.read_text(encoding="utf-8"))
        except Exception:
            prior = []
    by_url = {r.get("source_url") or r.get("url"): r for r in prior}
    for rec in records:
        by_url[rec["source_url"]] = rec
    batch_path.write_text(json.dumps(list(by_url.values()), indent=2, ensure_ascii=False),
                          encoding="utf-8")

    seen = set()
    if SEEN_JSON.exists():
        try:
            seen = set(json.loads(SEEN_JSON.read_text(encoding="utf-8")))
        except Exception:
            seen = set()
    seen.update(u for u, _ in urls.items())
    SEEN_JSON.write_text(json.dumps(sorted(seen), indent=0), encoding="utf-8")

    print("\n=== collection summary ===")
    for k in ("accepted", "not_article", "no_headline", "not_vellore",
              "not_crime", "dup_title", "error", "fetched"):
        print(f"  {k}: {stats.get(k, 0)}")
    print(f"  new records into batch: {len(records)} | batch pool total: {len(by_url)}")
    print(f"  wrote: {batch_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

