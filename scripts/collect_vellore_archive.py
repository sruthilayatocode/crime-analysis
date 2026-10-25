"""Vellore crime collector over the permitted Tamil/English news archives.

Why this script exists
----------------------
The sanctioned sources in `collect_news.py` (DT Next, NIE) expose only a small
number of daily sitemaps, which are nearly exhausted (~42 new Vellore-crime
records). Four further outlets from the project's own "reputable Tamil Nadu news
outlets" list publish enormous, **robots-declared** daily-sitemap archives:

    maalaimalar  4,871 daily sitemaps   2011-12-28 .. today
    dailythanthi 3,566 daily sitemaps   1969-12-31 .. today
    thenewsminute 4,475 daily sitemaps  2014-04-14 .. today
    dinamalar    daily sitemaps via /sitemap_index.xml

The Tamil outlets publish in Tamil but their **URL slugs are English** and the
outlet itself categorises each story, e.g.
    .../news/tamil-nadu-district-news-vellore/<english-slug>/
    .../news/woman-arrested-for-selling-liquor-near-ranipettai
So the story's place and crime type are declared by the publisher in the URL
path. This collector matches Vellore-scope place + crime terms in that slug,
then fetches the real article page and records ONLY what the page declares
(og:title, og:description, JSON-LD datePublished). Nothing is invented:
coordinates and severity stay empty, and every record keeps its source URL.

Output: data/raw/collected_sources/batches/batch_harvested.json, in the schema
`expand_crimesense_dataset.py` already ingests.
"""
from __future__ import annotations
import argparse, concurrent.futures, json, re, sys, time
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
import collect_news as cn  # noqa: E402  (project helpers/constants)

BATCH_DIR = cn.BATCH_DIR
SEEN_JSON = cn.SEEN_JSON
CANDIDATES_JSON = cn.CANDIDATES_JSON
# The existing, validated 89-record dataset (read-only; used for title dedup).
EXISTING_FINAL = PROJECT_ROOT / "data" / "final" / "crimesense_database_import.csv"

# --- permitted outlets with robots-declared daily-sitemap archives -----------
SOURCES = {
    "dinamalar": {
        "domain": "www.dinamalar.com",
        "index": "https://www.dinamalar.com/sitemap_index.xml",
        "daily_re": re.compile(
            r"<loc>\s*(https://www\.dinamalar\.com/sitemapxml/sitemap_"
            r"\d{2}-\d{2}-\d{4}\.xml)\s*</loc>", re.I),
        "daily_date_re": re.compile(
            r"sitemapxml/sitemap_(\d{2})-(\d{2})-(\d{4})\.xml", re.I),
    },
    "maalimalar": {
        "domain": "www.maalaimalar.com",
        "index": "https://www.maalaimalar.com/sitemap.xml",
        "daily_re": re.compile(
            r"<loc>\s*(https://www\.maalaimalar\.com/sitemap/sitemap-daily-"
            r"\d{4}-\d{2}-\d{2}\.xml)\s*</loc>", re.I),
        "daily_date_re": re.compile(
            r"sitemap-daily-(\d{4})-(\d{2})-(\d{2})\.xml", re.I),
    },
    "dailythanthi": {
        "domain": "www.dailythanthi.com",
        "index": "https://www.dailythanthi.com/sitemap.xml",
        "daily_re": re.compile(
            r"<loc>\s*(https://www\.dailythanthi\.com/sitemap/sitemap-daily-"
            r"\d{4}-\d{2}-\d{2}\.xml)\s*</loc>", re.I),
        "daily_date_re": re.compile(
            r"sitemap-daily-(\d{4})-(\d{2})-(\d{2})\.xml", re.I),
    },
    "thenewsminute": {
        "domain": "www.thenewsminute.com",
        "index": "https://www.thenewsminute.com/sitemap.xml",
        "daily_re": re.compile(
            r"<loc>\s*(https://www\.thenewsminute\.com/sitemap/sitemap-daily-"
            r"\d{4}-\d{2}-\d{2}\.xml)\s*</loc>", re.I),
        "daily_date_re": re.compile(
            r"sitemap-daily-(\d{4})-(\d{2})-(\d{2})\.xml", re.I),
    },
}

# Vellore *district* scope — exactly the places expand_crimesense_dataset's
# is_vellore() accepts, so every harvested record can be validated downstream.
VELLORE_SCOPE = {
    "vellore": "Vellore", "vellore-district": "Vellore",
    "katpadi": "Katpadi", "gudiyatham": "Gudiyatham", "gudiyathur": "Gudiyatham",
    "pernambut": "Pernambut", "ambur": "Ambur", "jolarpet": "Jolarpet",
    "jolarpettai": "Jolarpet", "natrampalli": "Natrampalli",
    "nattrampalli": "Natrampalli", "anaicut": "Anaicut", "anaikattu": "Anaicut",
}
scope_re = re.compile(r"\b(" + "|".join(
    sorted(VELLORE_SCOPE, key=len, reverse=True)) + r")\b", re.I)

# Crime terms as published in the URL slug -> canonical crime type.
CRIME_SLUG = [
    ("attempt-to-murder", "Attempt to Murder"),
    ("murder", "Murder"), ("homicide", "Murder"), ("stab", "Murder"),
    ("rape", "Rape"), ("sexual-assault", "Sexual Assault"),
    ("molest", "Sexual Assault"), ("pocso", "Sexual Assault"),
    ("kidnap", "Kidnapping"), ("abduct", "Kidnapping"), ("missing", "Kidnapping"),
    ("dowry", "Domestic Violence"), ("domestic-violence", "Domestic Violence"),
    ("assault", "Assault"), ("attack", "Assault"),
    ("burglar", "Burglary"), ("house-break", "Burglary"),
    ("robber", "Robbery"), ("snatch", "Snatching"),
    ("theft", "Theft"), ("steal", "Theft"), ("stolen", "Theft"),
    ("fraud", "Fraud"), ("cheat", "Cheating"), ("dupe", "Cheating"),
    ("cyber", "Cyber Crime"), ("phishing", "Cyber Crime"),
    ("narcotic", "Drug Arrest"), ("ganja", "Drug Arrest"),
    ("smuggl", "Drug Arrest"), ("drugs", "Drug Arrest"),
    ("weapon", "Illegal Weapons"), ("illegal-arms", "Illegal Weapons"),
    ("arson", "Vandalism"), ("extortion", "Extortion"),
]

# Terms that mean "accident / natural death", NOT a crime. Checked before the
# crime gate so "3 killed in accident" is never recorded as a murder.
NEG_SLUG_RE = re.compile(r"\b(accident|mishap|electrocuted|drowned|lightning)\b", re.I)
crime_slug_re = re.compile(
    r"\b(" + "|".join(re.escape(k) for k, _ in CRIME_SLUG) + r")\b", re.I)

# Discovery gate: a slug must contain BOTH a Vellore-scope place AND one of the
# CRIME_SLUG terms above, so every harvested row already has a crime_type.

UAGENT = cn.UA
from requests.adapters import HTTPAdapter  # noqa: E402
try:
    from urllib3.util.retry import Retry
    _retry = Retry(total=2, backoff_factor=0.3,
                   status_forcelist=[429, 500, 502, 503, 504])
except Exception:
    _retry = None


def make_session():
    s = cn.requests.Session()
    s.headers.update(UAGENT)
    if _retry is not None:
        ad = HTTPAdapter(max_retries=_retry, pool_connections=16, pool_maxsize=32)
        s.mount("http://", ad)
        s.mount("https://", ad)
    return s


SESSION = make_session()


def fetch(url, timeout=25):
    """Polite GET via the shared, pooled, retrying session."""
    try:
        r = SESSION.get(url, timeout=timeout)
        if r.status_code == 200:
            return r.text
        return None
    except Exception:
        return None

CRIME_MAP = dict(CRIME_SLUG)


def slug_info(url):
    """Return (locality, crime_type) the OUTLET declares in its URL path, or None.

    The publisher writes the place and the crime in the slug
    (e.g. /.../district-news-vellore/two-held-for-bike-theft/). We only read
    what is actually in the path — no inference beyond that.
    """
    path = urlparse(url).path.lower()
    m = scope_re.search(path)
    if not m:
        return None
    locality = VELLORE_SCOPE.get(m.group(1).lower(), "")
    cm = crime_slug_re.search(path)
    if not cm:
        return None
    return locality, CRIME_MAP.get(cm.group(1).lower(), "")


def load_known():
    known_titles = set()
    if EXISTING_FINAL.exists():
        with open(EXISTING_FINAL, encoding="utf-8-sig") as fh:
            import csv as _csv
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


def index_daily_sitemaps(source_key, max_days=None):
    """List (date, daily_sitemap_url) from a source's robots-declared index."""
    src = SOURCES[source_key]
    xml = fetch(src["index"], timeout=40)
    if not xml:
        print(f"  [{source_key}] index fetch failed: {src['index']}")
        return []
    out = []
    for m in src["daily_re"].finditer(xml):
        daily_url = m.group(1)
        dm = src["daily_date_re"].search(daily_url)
        if not dm:
            continue
        g = dm.groups()
        try:
            if source_key == "dinamalar":      # dd-mm-yyyy
                d = date(int(g[2]), int(g[1]), int(g[0]))
            else:                              # yyyy-mm-dd
                d = date(int(g[0]), int(g[1]), int(g[2]))
        except ValueError:
            continue
        if d.year < 1970:
            continue
        out.append((d, daily_url))
    out.sort(key=lambda x: x[0], reverse=True)   # newest first
    if max_days:
        out = out[:max_days]
    print(f"  [{source_key}] {len(out)} daily sitemaps"
          + (f" (newest {out[0][0]} .. oldest {out[-1][0]})" if out else ""))
    return out


def vellore_crime_urls(xml, source_key):
    """Article URLs in one daily sitemap whose slug is Vellore-scope + a crime."""
    keep = []
    for loc in re.findall(r"<loc>\s*(.*?)\s*</loc>", xml or "", re.S):
        loc = loc.strip()
        info = slug_info(loc)
        if info:
            keep.append((loc, source_key, info[0], info[1]))
    return keep

def _fetch_daily(t):
    """Worker: fetch one daily sitemap and return (date, [candidate URLs])."""
    d, u, k = t
    xml = fetch(u, timeout=30)
    if not xml:
        return None
    return d, vellore_crime_urls(xml, k)


def extract_article(url, fallback_date):
    """Fetch the real article page; return ONLY what the page declares."""
    html = fetch(url, timeout=25)
    if not html or len(html) < 4000:
        return None, "not_article"
    title = (cn.meta(html, "og:title") or cn.meta(html, "twitter:title") or "").strip()
    if not title:
        return None, "no_headline"
    desc = (cn.meta(html, "og:description") or cn.meta(html, "description"))[:500]
    pub = ""
    m = re.search(r'"datePublished"\s*:\s*"([^"]+)"', html)
    if m:
        pub = m.group(1)[:35]
    if not pub:
        pub = fallback_date.isoformat()   # the day it entered the daily sitemap
    return {"headline": title, "description": desc, "published_date": pub}, "ok"


def build_record(url, locality, ctype, art):
    dom = urlparse(url).netloc.replace("www.", "")
    hist = cn.POST_2019_MOVED.get(locality.lower(), "")
    return {
        "article_id": "", "title": art["headline"], "headline": art["headline"],
        "published_date": art["published_date"], "incident_date": "",
        "source": dom, "url": url, "source_url": url,
        "crime_type": ctype, "crime_type_raw": ctype,
        "description": art["description"],
        "district": "Vellore", "locality": locality, "state": "Tamil Nadu",
        "latitude": "", "longitude": "", "location_confidence": "",
        "location_source": "source URL path section (outlet-declared)",
        "severity_score": "", "risk_level": "", "historical_region": hist,
        "vellore_terms": locality, "crime_terms": ctype,
        "_headline": art["headline"], "_state": "Tamil Nadu",
        "_incident_date": "", "_url": url,
    }

def _write_batch(records, out_path):
    """Merge harvested records into the batch file expand_crimesense_dataset.py reads."""
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    prior = []
    if out_path.exists():
        try:
            prior = json.loads(out_path.read_text(encoding="utf-8"))
        except Exception:
            prior = []
    by_url = {}
    for r in prior:
        by_url[(r.get("source_url") or r.get("url") or "")] = r
    for r in records:
        by_url[r["source_url"]] = r
    out_path.write_text(json.dumps(list(by_url.values()), indent=2, ensure_ascii=False),
                        encoding="utf-8")
    return len(by_url)


def main():
    ap = argparse.ArgumentParser(description="Vellore crime archive collector")
    ap.add_argument("--target", type=int, default=320, help="accepted records goal")
    ap.add_argument("--sitemap-budget", type=int, default=2500)
    ap.add_argument("--fetch-budget", type=int, default=2200)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--max-days", type=int, default=1500, help="daily sitemaps per source")
    ap.add_argument("--sources", default="dinamalar,maalimalar,dailythanthi,thenewsminute")
    ap.add_argument("--dry-run", action="store_true",
                    help="discover + list candidates only; fetch nothing, write nothing")
    ap.add_argument("--out", default=str(BATCH_DIR / "batch_harvested.json"))
    args = ap.parse_args()

    srcs = [s.strip() for s in args.sources.split(",") if s.strip()]
    print("=== Vellore archive collector (4 permitted outlets) ===")
    print(f"sources={srcs} target={args.target} sitemaps<={args.sitemap_budget} "
          f"fetches<={args.fetch_budget} workers={args.workers}")

    print("[1] listing robots-declared daily sitemaps...")
    pool = []
    for k in srcs:
        for d, u in index_daily_sitemaps(k, max_days=args.max_days):
            pool.append((d, u, k))
    pool.sort(key=lambda x: x[0], reverse=True)   # newest-first across sources
    print(f"    {len(pool)} daily sitemaps pooled")

    print("[2] scanning daily sitemaps for Vellore+crime slugs...")
    t0 = time.time()
    known_titles, known_urls = load_known()
    cand = {}
    by_src = Counter()
    scanned = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(_fetch_daily, t): t for t in pool[:args.sitemap_budget]}
        for fut in concurrent.futures.as_completed(futs):
            try:
                res = fut.result()
            except Exception:
                continue
            if not res:
                continue
            d, items = res
            scanned += 1
            for url, key, loc, ct in items:
                if url in known_urls or url in cand:
                    continue
                cand[url] = (d, loc, ct)
                by_src[key] += 1
            if len(cand) >= args.fetch_budget:
                for f in futs:
                    f.cancel()
                break
    print(f"    scanned {scanned} sitemaps | Vellore+crime article URLs: {len(cand)} "
          f"(elapsed {time.time()-t0:.1f}s)")
    print(f"    by source: {dict(by_src)}")

    if args.dry_run:
        print("\n[dry-run] no article pages fetched, no files written.")
        for u, (d, loc, ct) in list(cand.items())[:15]:
            print(f"   {d} | {loc} | {ct} | {u[:100]}")
        return 0

    print(f"[3] fetching real article pages (<= {args.fetch_budget}) ...")
    records = []
    stats = Counter()
    done = 0
    items = list(cand.items())
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        fut_to = {ex.submit(extract_article, u, d): (u, loc, ct)
                  for u, (d, loc, ct) in items}
        for fut in concurrent.futures.as_completed(fut_to):
            if done >= args.fetch_budget:
                for f in fut_to:
                    f.cancel()
                break
            u, loc, ct = fut_to[fut]
            try:
                art, reason = fut.result()
            except Exception:
                stats["error"] += 1
                continue
            done += 1
            stats["fetched"] += 1
            if not art:
                stats[reason] += 1
                continue
            nt = cn.normalize_title(art["headline"]) or url
            if nt in known_titles:
                stats["dup_title"] += 1
                continue
            rec = build_record(u, loc, ct, art)
            if not cn.vellore_relevant(rec):
                stats["not_vellore"] += 1
                continue
            if not cn.crime_relevant(rec):
                rec["crime_type_raw"] = rec["crime_type_raw"] or ct
            known_titles.add(nt)
            records.append(rec)
            stats["accepted"] += 1

    print(f"    fetched={stats.get('fetched',0)} accepted={stats.get('accepted',0)}")

    total = _write_batch(records, args.out)

    # Provenance trail: also append to the review pool (never staged directly).
    try:
        pool = []
        if CANDIDATES_JSON.exists():
            pool = json.loads(CANDIDATES_JSON.read_text(encoding="utf-8"))
        have = {(r.get("source_url") or r.get("url") or "") for r in pool}
        for r in records:
            if r["source_url"] in have:
                continue
            have.add(r["source_url"])
            pool.append({k: r[k] for k in
                         ("headline", "source_url", "url", "source", "published_date",
                          "incident_date", "crime_type_raw", "description", "district",
                          "locality", "state", "latitude", "longitude",
                          "location_confidence", "location_source", "severity_score",
                          "risk_level", "vellore_terms", "crime_terms",
                          "historical_region") if k in r})
        CANDIDATES_JSON.write_text(json.dumps(pool, indent=2, ensure_ascii=False),
                                   encoding="utf-8")
    except Exception as exc:
        print(f"  [warn] candidate pool not updated: {exc}")

    # Seen-URL ledger so re-runs don't refetch the same articles.
    try:
        seen = set(json.loads(SEEN_JSON.read_text(encoding="utf-8"))) if SEEN_JSON.exists() else set()
    except Exception:
        seen = set()
    seen.update(cand.keys())
    SEEN_JSON.write_text(json.dumps(sorted(seen), indent=0), encoding="utf-8")

    print("\n=== archive collection summary ===")
    for k in ("accepted", "not_article", "no_headline", "not_vellore", "dup_title",
              "error", "fetched"):
        print(f"  {k}: {stats.get(k, 0)}")
    print(f"  new records this run: {len(records)} | batch pool total: {total}")
    print(f"  wrote: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
