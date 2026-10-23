"""Polite HTTP client: robots.txt compliance, rate limiting, retries,
disk cache, and failure logging — configured from collection/config.py."""
from __future__ import annotations
import hashlib, json, time
from pathlib import Path
from urllib import robotparser
from urllib.parse import urlparse

import requests

from scripts.collection.config import (REQUEST_DELAY, RETRY_COUNT, RETRY_BACKOFF,
                                       REQUEST_TIMEOUT as HTTP_TIMEOUT, CACHE_DIR, LOG_DIR,
                                       USER_AGENT)

_cache_dir = Path(CACHE_DIR)
_cache_dir.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
_fail_log = LOG_DIR / "http_failures.jsonl"

_session = requests.Session()
_session.headers.update({"User-Agent": USER_AGENT,
                         "Accept-Language": "en,ta;q=0.9"})

_robots_cache: dict[str, robotparser.RobotFileParser] = {}


def _robots_for(url: str):
    """Parse and cache robots.txt for the URL's origin.

    We fetch robots.txt through our own session (with the configured UA)
    instead of RobotFileParser.read(), which uses Python-urllib and is
    blocked by some CDNs with 403 — and a 403 robots fetch must NOT be
    treated as a site-wide disallow when the file is in fact served to
    normal clients. Compliance: we still apply the file's exact rules.
    """
    origin = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    if origin in _robots_cache:
        return _robots_cache[origin]

    rp = robotparser.RobotFileParser()
    status, text = fetch(origin + "/robots.txt", use_cache=True,
                         respect_robots=False)
    if status == 200 and text:
        rp.parse(text.splitlines())
    elif status in ("401", "403"):
        # Genuinely restricted robots.txt -> conservative disallow-all.
        rp.parse(["User-agent: *", "Disallow: /"])
        with open(_fail_log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"type": "robots_403_disallow_all",
                                 "origin": origin}) + "\n")
    else:
        # Unreachable (network error / 404 / 5xx): standard convention is
        # allow, but log it for the audit trail.
        with open(_fail_log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"type": "robots_unreachable",
                                 "status": str(status), "origin": origin}) + "\n")
    _robots_cache[origin] = rp
    return rp


def allowed(url: str) -> bool:
    try:
        return _robots_for(url).can_fetch(USER_AGENT, url)
    except Exception:
        return False


def _cache_path(url: str) -> Path:
    key = hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]
    return _cache_dir / f"{key}.txt"


def cache_get(url: str):
    p = _cache_path(url)
    if p.exists():
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
            return rec.get("status"), rec.get("text")
        except Exception:
            return None, None
    return None, None


def cache_put(url: str, status, text):
    try:
        _cache_path(url).write_text(
            json.dumps({"status": status, "text": text}, ensure_ascii=False),
            encoding="utf-8")
    except Exception:
        pass


def fetch(url: str, use_cache: bool = True, respect_robots: bool = True):
    """Return (status, text) with status in {200, 403, 404, ...}; text None on
    non-200. Honors robots.txt, caches successes, logs failures."""
    if respect_robots and not allowed(url):
        with open(_fail_log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"type": "robots_disallow", "url": url}) + "\n")
        return ("robots_disallow", None)

    if use_cache:
        st, tx = cache_get(url)
        if st == 200 and tx is not None:
            return st, tx

    last = None
    for attempt in range(RETRY_COUNT + 1):
        try:
            r = _session.get(url, timeout=HTTP_TIMEOUT)
            if r.status_code == 200:
                if use_cache:
                    cache_put(url, 200, r.text)
                return 200, r.text
            last = r.status_code
            if r.status_code in (403, 404, 410):
                break                      # permanent — don't retry
        except requests.RequestException as exc:
            last = type(exc).__name__
        time.sleep(RETRY_BACKOFF * (attempt + 1))
    with open(_fail_log, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"type": "http_error", "status": str(last),
                             "url": url}) + "\n")
    return (str(last), None)


def fetch_many(urls, use_cache=True):
    """Sequential, rate-limited fetch of a list. Yields (url, status, text)."""
    for i, u in enumerate(urls):
        status, text = fetch(u, use_cache=use_cache)
        yield u, status, text
        if i < len(urls) - 1:
            time.sleep(REQUEST_DELAY)
