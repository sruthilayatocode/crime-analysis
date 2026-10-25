"""Sitemap-based discovery: index -> daily sitemaps -> candidate article URLs.

Resumable via a discovery ledger (data/raw/candidates/discovery_ledger.json)
so repeated runs never re-crawl a processed sitemap. Sources come from
scripts/collection/sources.py — only robots-verified outlets.
"""
from __future__ import annotations
import json, re, time
from pathlib import Path

from scripts.collection.config import (CANDIDATE_DIR,
                                       MAX_SITEMAPS_PER_SOURCE_PER_RUN,
                                       SITEMAP_DELAY)
from scripts.collection.http_client import fetch
from scripts.collection import sources as SRC

LEDGER = Path(CANDIDATE_DIR) / "discovery_ledger.json"
LEDGER.parent.mkdir(parents=True, exist_ok=True)

_LOC = re.compile(r"<loc>\s*(.*?)\s*</loc>", re.S)
_LASTMOD = re.compile(r"<lastmod>\s*(.*?)\s*</lastmod>", re.S)


def _load_ledger() -> dict:
    if LEDGER.exists():
        try:
            return json.loads(LEDGER.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"done_sitemaps": [], "urls": {}}


def _save_ledger(led: dict) -> None:
    tmp = LEDGER.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(led, ensure_ascii=False), encoding="utf-8")
    tmp.replace(LEDGER)


def _locs(xml: str):
    """[(url, lastmod)] from sitemap XML."""
    out = []
    for block in re.findall(r"<url>(.*?)</url>", xml or "", re.S):
        m = _LOC.search(block)
        if not m:
            continue
        lm = _LASTMOD.search(block)
        out.append((m.group(1).strip(),
                    lm.group(1).strip() if lm else ""))
    if not out:                                   # plain <loc> sitemap
        out = [(u.strip(), "") for u in _LOC.findall(xml or "")]
    return out


def _daily_urls(src, start_date, end_date, max_urls):
    """Generate daily-sitemap URLs from the source's patterns over a date
    window (newest first)."""
    from datetime import date as _date, timedelta as _td
    out = []
    d = end_date
    while d >= start_date and len(out) < max_urls:
        for pat in src.daily_patterns:
            out.append(pat.format(date=d.isoformat(),
                                  date_dmy=d.strftime("%d-%m-%Y")))
        d -= _td(days=1)
    return out


def discover_source(source_key: str, max_sitemaps: int = None,
                    years_back: int = 6) -> dict:
    """Crawl one source: fetch its sitemap index, then daily sitemaps (from the
    index when available, else generated from daily_patterns), filtering URLs
    to the source's article sections. Resumable via the ledger."""
    from datetime import date as _date, timedelta as _td
    src = SRC.SOURCES[source_key]
    if not src.robots_allowed:
        return {"skipped": "robots_disallowed"}
    max_sitemaps = max_sitemaps or MAX_SITEMAPS_PER_SOURCE_PER_RUN
    led = _load_ledger()
    done = set(led["done_sitemaps"])
    counts = {"new_urls": 0, "sitemaps": 0}

    # 1) child sitemap list: index first, then pattern-generated fallback
    sitemap_urls = []
    if src.sitemap_index:
        st, xml = fetch(src.sitemap_index)
        if st == 200 and xml:
            sitemap_urls = [u for u, _ in _locs(xml)]
    if not sitemap_urls or len(sitemap_urls) < 10:
        gen = _daily_urls(src, _date.today() - _td(days=365 * years_back),
                          _date.today(), max_sitemaps)
        seen_sm = set(sitemap_urls)
        sitemap_urls += [u for u in gen if u not in seen_sm]
    sitemap_urls = [u for u in dict.fromkeys(sitemap_urls) if u not in done]

    for smu in sitemap_urls[:max_sitemaps]:
        st, xml = fetch(smu)
        if st == 200 and xml and "<url" in xml.lower():
            done.add(smu)          # only mark done on success (failures retry)
            counts["sitemaps"] += 1
            for url, lastmod in _locs(xml):
                low = url.lower()
                if url in led["urls"]:
                    continue
                if any(root in low for root in src.section_roots) and \
                        not any(ex in low for ex in src.url_exclude):
                    led["urls"][url] = {"source": source_key,
                                        "lastmod": lastmod}
                    counts["new_urls"] += 1
        elif st in ("404", "403", "410"):
            # Permanent failure (that date/URL will never exist) — mark done,
            # log it, don't waste future runs retrying.
            done.add(smu)
            counts["sitemaps"] += 1
            import json as _json
            with open(LEDGER.parent.parent.parent / "logs" / "collection" / "sitemap_failures.jsonl",
                      "a", encoding="utf-8") as fh:
                fh.write(_json.dumps({"sitemap": smu, "status": str(st)}) + "\n")
        else:
            # Transient failure (5xx / network): leave out of `done` so the
            # next run retries it; still counts against this run's budget.
            counts["sitemaps"] += 1
        if SITEMAP_DELAY:
            time.sleep(SITEMAP_DELAY)
        if counts["sitemaps"] >= max_sitemaps:
            break

    led["done_sitemaps"] = sorted(done)
    _save_ledger(led)
    return counts


def discover(sources_keys=None) -> dict:
    keys = sources_keys or list(SRC.SOURCES.keys())
    summary = {}
    for k in keys:
        try:
            summary[k] = discover_source(k)
        except Exception as exc:
            summary[k] = {"error": str(exc)}
    total = sum(v.get("new_urls", 0) for v in summary.values())
    return {"summary": summary, "new_urls": total}


def pending_urls(limit=None):
    """Article URLs discovered but not yet fetched/extracted.

    Ordered with Vellore-specific URLs first (URL slug contains a Vellore-region
    place name or Tamil name), so limited fetch budgets go to the highest-yield
    candidates. All discovered URLs remain queued behind them."""
    from scripts.collection.store import fetched_urls
    from scripts.collection.scope import URL_PLACE_RE
    led = _load_ledger()
    have = fetched_urls()
    pri, rest = [], []
    for u, rec in led["urls"].items():
        if u in have:
            continue
        (pri if URL_PLACE_RE.search(u) else rest).append((u, rec["source"]))
    out = pri + rest
    if limit:
        out = out[:limit]
    return out
