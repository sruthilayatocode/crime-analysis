"""Article extraction: title, description, JSON-LD dates, body text.

Extracts ONLY what the page actually declares — no field is guessed.
"""
from __future__ import annotations
import json, re
from datetime import datetime
from urllib.parse import urlparse

from scripts.collection.http_client import fetch

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

_META = re.compile(
    r'<meta[^>]+(?:property|name)="([^"]+)"[^>]+content="([^"]*)"', re.I | re.S)
_META2 = re.compile(
    r'<meta[^>]+content="([^"]*)"[^>]+(?:property|name)="([^"]+)"', re.I | re.S)


def _metas(html: str) -> dict:
    out = {}
    for name, val in _META.findall(html or ""):
        out.setdefault(name.lower(), val)
    for val, name in _META2.findall(html or ""):
        out.setdefault(name.lower(), val)
    return out


_DATE_PATTERNS = [
    # ISO: 2024-05-03T06:00:00+05:30 / 2024-05-03 06:00:00
    re.compile(r'"datePublished"\s*:\s*"([^"]{4,40})"'),
    re.compile(r'"publishedDate"\s*:\s*"([^"]{4,40})"'),
    # <time datetime=...> / visible "03 May 2024"
    re.compile(r'<time[^>]+datetime="([^"]{4,40})"', re.I),
]
_VISIBLE_DATES = [
    re.compile(r"\b(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) "
               r"(\d{4})\b"),
    re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b"),
]
_MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun",
     "jul", "aug", "sep", "oct", "nov", "dec"])}


def parse_date(raw: str):
    """Normalize a date-like string to ISO YYYY-MM-DD; None if unparseable."""
    raw = (raw or "").strip()
    if not raw:
        return None
    # Normalize ISO-8601 variants: strip 'Z' and timezone offsets like +05:30
    # so "2026-09-15T21:26:00+05:30" parses as local datetime.
    raw = raw.replace("Z", "").strip()
    raw = re.sub(r"[+-]\d{2}:?\d{2}$", "", raw).strip().rstrip("T ")

    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d",
                "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw[:len(fmt) + 12], fmt).date().isoformat()
        except ValueError:
            continue
    m = _VISIBLE_DATES[0].search(raw)
    if m:
        d, mon, y = int(m.group(1)), m.group(2).lower(), int(m.group(3))
        if mon in _MONTHS:
            return f"{y:04d}-{_MONTHS[mon]:02d}-{d:02d}"
    m = _VISIBLE_DATES[1].search(raw)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return None


def extract_article(url: str, html: str) -> dict | None:
    """Extract declared metadata + body text from a fetched article page."""
    if not html or len(html) < 3000:
        return None
    metas = _metas(html)
    title = (metas.get("og:title") or metas.get("title") or "").strip()
    if not title and BeautifulSoup:
        soup = BeautifulSoup(html, "html.parser")
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
    description = (metas.get("og:description")
                   or metas.get("description") or "").strip()

    # published date: JSON-LD / <time> / visible text (first match wins)
    published = None
    for pat in _DATE_PATTERNS:
        m = pat.search(html)
        if m:
            published = parse_date(m.group(1))
            if published:
                break
    if not published:
        for pat in _VISIBLE_DATES:
            m = pat.search(re.sub(r"<[^>]+>", " ", html[:200000]))
            if m:
                published = parse_date(m.group(0))
                if published:
                    break

    # body text (meta description as primary declared summary; else <p> text)
    body = description
    if BeautifulSoup and (not body or len(body) < 120):
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()
        text = " ".join(p.get_text(" ", strip=True)
                        for p in soup.find_all("p"))
        text = re.sub(r"\s+", " ", text).strip()
        body = text[:4000] if len(text) > len(body or "") else (body or text[:4000])

    return {
        "source_url": url,
        "source_name": urlparse(url).netloc.replace("www.", ""),
        "title": title,
        "description": description[:500],
        "body_text": body or "",
        "published_date": published or "",
        "source_publication_date": published or "",
        "extracted_at": datetime.utcnow().isoformat(timespec="seconds"),
    }


def fetch_article(url: str):
    st, html = fetch(url)
    if st != 200 or not html:
        return None, st
    return extract_article(url, html), st
