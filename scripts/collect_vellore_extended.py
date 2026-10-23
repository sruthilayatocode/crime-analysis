"""Extended Vellore-crime collector for registry-sanctioned news sitemaps.

Adds four SOURCE_REGISTRY-approved outlets whose robots-declared sitemap
indexes reach far back in time:
  * dailythanthi.com  sitemap index spans 1969 -> present  (~57 years)
  * maalaimalar.com   sitemap index spans 2011 -> present
  * thenewsminute.com sitemap index spans 2014 -> present
  * dinamalar.com     sitemap index spans 2025 -> present

All four publish English slugs but Tamil og:title/og:description. So:
  - locality  <- matched from the ENGLISH URL slug (kept as source wording)
  - crime_type<- matched from the ENGLISH URL slug
  - title/description -> preserved verbatim (Tamil kept; nothing translated)
This keeps zero-fabrication: every field traces to real page/slug data.

Output schema matches batches/batch_collected.json so the existing
expand_crimesense_dataset.py ingests it unchanged.
"""
from __future__ import annotations
import argparse, concurrent.futures, csv as _csv, json, re, sys, time
from collections import Counter, OrderedDict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
import collect_news as cn  # noqa: E402

BATCH_DIR = cn.BATCH_DIR
CANDIDATES_JSON = cn.CANDIDATES_JSON
SEEN_JSON = cn.SEEN_JSON
EXISTING_FINAL = PROJECT_ROOT / "data" / "final" / "crimesense_database_import.csv"

UA = cn.UA
try:
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    _retry = Retry(total=2, backoff_factor=0.4,
                   status_forcelist=[429, 500, 502, 503, 504])
except Exception:
    _retry = None
SESSION = cn.requests.Session()
SESSION.headers.update(UA)
if _retry is not None:
    _ad = HTTPAdapter(max_retries=_retry, pool_connections=24, pool_maxsize=64)
    SESSION.mount("http://", _ad)
    SESSION.mount("https://", _ad)

# robots-declared sitemap indexes (see SOURCE_REGISTRY.md acceptable outlets)
EXT_SOURCES = {
    "dailythanthi": "https://www.dailythanthi.com/sitemap.xml",
    "maalaimalar": "https://www.maalaimalar.com/sitemap.xml",
    "thenewsminute": "https://www.thenewsminute.com/sitemap.xml",
    "dinamalar": "https://www.dinamalar.com/sitemap_index.xml",
}
# Only these URL shapes denote per-day article sitemaps.
DAILY_MARKERS = ("sitemap-daily-", "sitemapxml/sitemap_")

VELLORE_SLUG_RE = re.compile(
    r"\b(vellore|katpadi|gudiyatham|gudiyattam|pernambut|pernambattu|ambur|"
    r"vaniyambadi|tirupattur|tirupathur|jolarpet|natrampalli|nattrampalli|"
    r"sholingur|sholinghur|walajapet|walajah|arcot|ranipet|ranipettai|"
    r"melvisharam|arakkonam|arakonam|anaicut|anaicat|alangayam|sripuranthapuram)\b",
    re.I)
CRIME_SLUG_RE = re.compile(
    r"\b(murder|homicide|killed|killing|death|deaths|died|found-dead|stabbed|"
    r"stab|shot|shooting|gunman|shootout|attack|attacked|assault|raped|rape|"
    r"sexual|harassment|theft|stolen|stealing|robbery|robbed|snatching|burglar|"
    r"burglary|broke|loot|looted|acid|dacoity|dacoit|extort|extortion|cheat|"
    r"cheating|fraud|scam|scammer|narcotics|narcotic|drugs|drug|ganja|smuggl|"
    r"traffick|trafficking|kidnap|abduct|abduction|dowry|bribery|corruption|"
    r"bomb|blast|riot|weapon|explosive|terror|terrorist|missing|recovered|"
    r"arrest|arrested|arrests|booked|case-registered|police)\b",
    re.I)


def fetch(url, timeout=25):
    """Single polite GET using the shared pooled session."""
    try:
        r = SESSION.get(url, timeout=timeout)
        if r.status_code == 200:
            return r.text
        return None
    except Exception:
        return None


def read_index(source_key):
    """Return the list of daily-sitemap URLs declared by a source index."""
    xml = fetch(EXT_SOURCES[source_key], timeout=35)
    if not xml or "<loc" not in xml.lower():
        return []
    out = []
    for loc in re.findall(r"<loc>\s*(.*?)\s*</loc>", xml, re.S):
        loc = loc.strip()
        if any(m in loc for m in DAILY_MARKERS):
            out.append(loc)
    return out


def vellore_crime_urls(daily_url):
    """From one daily sitemap, return article URLs that are BOTH in the
    Vellore historical region AND look like an individual crime story.
    Matching is on the English URL slug only (titles are Tamil)."""
    xml = fetch(daily_url, timeout=25)
    if not xml or "<loc" not in xml.lower():
        return []
    keep = []
    for loc in re.findall(r"<loc>\s*(.*?)\s*</loc>", xml, re.S):
        loc = loc.strip()
        low = loc.lower()
        if "/sitemap" in low or low.endswith(".xml"):
            continue
        if VELLORE_SLUG_RE.search(loc) and CRIME_SLUG_RE.search(loc):
            keep.append(loc)
    return keep


def crawl_all(max_sitemaps=0, workers=16, per_source_cap=0):
    """Fetch every daily sitemap concurrently; return {url: source_key}."""
    found = OrderedDict()
    stats = Counter()
    for key in EXT_SOURCES:
        days = read_index(key)
        if per_source_cap:
            days = days[:per_source_cap]
        print(f"  [{key}] {len(days)} daily sitemaps in index")
        stats[f"idx_{key}"] = len(days)
        if max_sitemaps:
            days = days[:max_sitemaps]
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
            for res in ex.map(vellore_crime_urls, days):
                for u in res:
                    found.setdefault(u, key)
        print(f"      -> cumulative Vellore+crime URLs: {len(found)}")
    return found, stats

def slug_locality(url):
    """Vellore-region place as written in the publisher's English slug."""
    m = VELLORE_SLUG_RE.search(url)
    if not m:
        return ""
    term = m.group(1).lower()
    return term


def slug_crime_type(url):
    """Crime classification derived from the publisher's English slug."""
    low = url.lower()
    for kw, ct in cn.CRIME_PAIRS:
        if re.search(rf"\b{re.escape(kw)}\b", low):
            return ct
    return ""


def build_record(url, source_key):
    """Fetch + extract one article; return canonical candidate dict or None."""
    html = fetch(url, timeout=25)
    if not html or len(html) < 5000:
        return None, "not_article"
    rec = cn.extract_article(url, html, source_key="", lastmod="")
    headline = (rec.get("headline") or "").strip()
    if not headline:
        return None, "no_headline"
    loc = slug_locality(url)
    ctype = slug_crime_type(url)
    if not loc:
        return None, "no_locality_in_slug"
    if not ctype:
        return None, "no_crime_in_slug"
    # Prefer explicit Vellore wording when the slug says Vellore itself.
    locality = "Vellore" if "vellore" in loc else loc.title()
    rec.update({
        "headline": headline,
        "source": rec.get("source") or url.split("/")[2].replace("www.", ""),
        "published_date": rec.get("published_date", ""),
        "crime_type_raw": ctype,
        "locality": locality,
        "district": "Vellore",
        "state": "Tamil Nadu",
        "historical_region": cn.POST_2019_MOVED.get(loc, ""),
    })
    return rec, "ok"


def load_known():
    titles, urls = set(), set()
    if EXISTING_FINAL.exists():
        with open(EXISTING_FINAL, encoding="utf-8") as fh:
            for r in _csv.DictReader(fh):
                t = cn.normalize_title(r.get("title", ""))
                if t:
                    titles.add(t)
                for k in ("url", "source_url"):
                    if r.get(k):
                        urls.add(r[k].strip())
    if SEEN_JSON.exists():
        try:
            urls |= set(json.loads(SEEN_JSON.read_text(encoding="utf-8")))
        except Exception:
            pass
    pool = []
    if CANDIDATES_JSON.exists():
        try:
            pool = json.loads(CANDIDATES_JSON.read_text(encoding="utf-8"))
        except Exception:
            pool = []
    for r in pool:
        u = (r.get("source_url") or r.get("url") or "").strip()
        if u:
            urls.add(u)
    return titles, urls, pool


def batch_row(rec):
    return {
        "article_id": "", "title": rec["headline"], "headline": rec["headline"],
        "published_date": rec.get("published_date", ""), "incident_date": "",
        "source": rec["source"], "url": rec["source_url"], "source_url": rec["source_url"],
        "crime_type": rec["crime_type_raw"], "description": rec.get("description", ""),
        "district": rec.get("district", "Vellore"), "locality": rec.get("locality", ""),
        "state": "Tamil Nadu",
        "latitude": "", "longitude": "", "location_confidence": "",
        "location_source": "", "severity_score": "", "risk_level": "",
        "historical_region": rec.get("historical_region", ""),
    }


def main():
    ap = argparse.ArgumentParser(description="Extended Vellore-crime sitemap collector")
    ap.add_argument("--max-sitemaps", type=int, default=0, help="cap daily sitemaps per source (0=all)")
    ap.add_argument("--per-source-cap", type=int, default=0, help="keep first N daily sitemaps per source")
    ap.add_argument("--fetch-budget", type=int, default=600, help="max article pages to fetch")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--measure-only", action="store_true", help="only report URL counts")
    ap.add_argument("--out", default=str(BATCH_DIR / "batch_extended.json"))
    args = ap.parse_args()

    t0 = time.time()
    print("=== Extended Vellore-crime collector ===")
    print(f"sources: {', '.join(EXT_SOURCES)} | workers={args.workers} | "
          f"fetch-budget={args.fetch_budget}")

    print("[1] reading indexes + daily sitemaps (concurrent)...")
    found, idx_stats = crawl_all(args.max_sitemaps, args.workers, args.per_source_cap)
    print(f"    total Vellore+crime article URLs discovered: {len(found)} "
          f"({time.time()-t0:.0f}s)")

    by_source = Counter(v for v in found.values())
    for k, v in by_source.most_common():
        print(f"      {k}: {v}")

    if args.measure_only:
        print("\n[measure-only] sample URLs:")
        for u in list(found)[:25]:
            print("   ", u[:150])
        return 0

    known_titles, known_urls, pool = load_known()
    fresh = [u for u in found if u not in known_urls]
    print(f"[2] fresh URLs (not already collected): {len(fresh)}")
    fresh = fresh[:args.fetch_budget * 3]   # allow for non-article rejects

    records, stats = [], Counter()
    seen_titles = set()
    done = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(build_record, u, found[u]): u for u in fresh}
        for fut in concurrent.futures.as_completed(futs):
            if len(records) >= args.fetch_budget:
                break
            try:
                rec, reason = fut.result()
            except Exception:
                stats["error"] += 1
                continue
            done += 1
            if rec is None:
                stats[reason] += 1
                continue
            t = cn.normalize_title(rec["headline"])
            key = t if t else rec["source_url"]
            if key in known_titles or key in seen_titles:
                stats["dup_title"] += 1
                continue
            seen_titles.add(key)
            known_titles.add(key)
            records.append(rec)
            stats["accepted"] += 1

    print(f"[3] fetched={done} accepted={stats['accepted']} "
          f"rejected={ {k: v for k, v in stats.items() if k in ('not_article','no_headline','no_locality_in_slug','no_crime_in_slug','dup_title','error')} }")

    # ---- write batch (merge with prior) ----
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    bp = Path(args.out)
    prior = []
    if bp.exists():
        try:
            prior = json.loads(bp.read_text(encoding="utf-8"))
        except Exception:
            prior = []
    by_url = {(r.get("source_url") or r.get("url")): r for r in prior}
    for rec in records:
        by_url[rec["source_url"]] = batch_row(rec)
    bp.write_text(json.dumps(list(by_url.values()), indent=2, ensure_ascii=False),
                  encoding="utf-8")

    # ---- append to candidate pool (provenance ledger) ----
    existing = {(r.get("source_url") or r.get("url") or "") for r in pool}
    for rec in records:
        if rec["source_url"] in existing:
            continue
        existing.add(rec["source_url"])
        pool.append({
            "headline": rec["headline"], "source_url": rec["source_url"],
            "url": rec["source_url"], "source": rec["source"],
            "published_date": rec.get("published_date", ""), "incident_date": "",
            "crime_type_raw": rec["crime_type_raw"],
            "description": rec.get("description", ""),
            "district": rec.get("district", "Vellore"),
            "locality": rec.get("locality", ""), "state": "Tamil Nadu",
            "latitude": "", "longitude": "", "location_confidence": "",
            "location_source": "", "severity_score": "", "risk_level": "",
            "vellore_terms": rec.get("locality", ""),
            "crime_terms": rec["crime_type_raw"],
            "historical_region": rec.get("historical_region", ""),
        })
    CANDIDATES_JSON.write_text(json.dumps(pool, indent=2, ensure_ascii=False),
                               encoding="utf-8")

    # ---- update seen-URL ledger ----
    seen = set()
    if SEEN_JSON.exists():
        try:
            seen = set(json.loads(SEEN_JSON.read_text(encoding="utf-8")))
        except Exception:
            seen = set()
    seen |= set(found)
    SEEN_JSON.write_text(json.dumps(sorted(seen), indent=0), encoding="utf-8")

    print(f"\n=== summary ===\n  new records: {len(records)} | batch pool: {len(by_url)}")
    print(f"  wrote: {bp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

