"""Approved source registry for the CrimeSense collection pipeline.

COMPLIANCE IS THE GATE. Every source here was verified against its live
robots.txt (raw rules archived in ``data/raw/candidates/_state/robots_cache.json``).
Sources whose robots.txt disallows generic user-agents are listed with
``robots_allowed = False`` and the pipeline records the failure instead of
crawling them.

Verified verdicts (2026-09-17):
    dinamalar     Allow (only /search, /admin, /dinaadmin disallowed)  -> OK
    dailythanthi  Allow: /                                            -> OK
    maalaimalar   Allow: /                                            -> OK
    dinamani      Allow: / ; article URLs live under /all-editions/    -> OK
    thehindu      dated paths (/200*, /201*) disallowed; articles OK   -> OK
    dtnext        Allow: /                                            -> OK
    nie           Allow: /                                            -> OK
    oneindia_ta   Disallow: / for generic UA (Googlebot/Bingbot only)  -> BLOCKED
    thenewsminute Disallow: /                                         -> BLOCKED
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional


@dataclass
class Source:
    key: str
    name: str                 # canonical ``source_name`` written to records
    domain: str
    language: str             # "ta" (Tamil) | "en" (English)
    kind: str                 # "news" | "govt" | "court" | "wiki" | "archive"
    sitemap_index: Optional[str] = None   # URL of sitemap index (preferred)
    daily_patterns: List[str] = field(default_factory=list)  # {date}/{date_dmy}
    # Path fragments marking a URL as a likely district/local news article.
    section_roots: List[str] = field(default_factory=list)
    # Reject URLs containing any of these fragments (robots-disallowed paths).
    url_exclude: List[str] = field(default_factory=list)
    max_articles_per_run: Optional[int] = None
    request_delay: Optional[float] = None
    robots_allowed: bool = True
    notes: str = ""


def _mk(**kw) -> Source:
    return Source(**kw)

# ---------------------------------------------------------------------------
# ACTIVE, ROBOTS-VERIFIED SOURCES
# ---------------------------------------------------------------------------
SOURCES = {
    "dinamalar": _mk(
        key="dinamalar", name="Dinamalar", domain="www.dinamalar.com",
        language="ta", kind="news",
        sitemap_index="https://www.dinamalar.com/sitemap_index.xml",
        daily_patterns=[
            "https://www.dinamalar.com/sitemapxml/sitemap_{date_dmy}.xml"],
        section_roots=["tamil-nadu-district-news-vellore",
                       "tamil-nadu-district-news-ranipet",
                       "tamil-nadu-district-news-tirupathur",
                       "tamil-nadu-district-news-tirupattur",
                       "/news/tamilnadu/", "/news/district/"],
        url_exclude=["/dinaadmin/", "/admin/", "/search", "/show.asp"],
        request_delay=0.4, max_articles_per_run=1200,
        notes="Dedicated tamil-nadu-district-news-vellore prefix; daily sitemaps "
              "cover ~2025-07 onward (older days 404 in the index)."),
    "dinamani": _mk(
        key="dinamani", name="Dinamani", domain="www.dinamani.com",
        language="ta", kind="news",
        sitemap_index="https://www.dinamani.com/sitemap.xml",
        daily_patterns=[
            "https://www.dinamani.com/sitemap/sitemap-daily-{date}.xml"],
        section_roots=["/all-editions/", "/tamilnadu/"],
        url_exclude=["/story/", "/search", "/author/"],
        request_delay=0.4, max_articles_per_run=1500,
        notes="Dedicated /all-editions/edition-vellore/. Largest index (~6.3k "
              "daily sitemaps). /story/ is robots-disallowed; /all-editions/ is not."),
    "dailythanthi": _mk(
        key="dailythanthi", name="Daily Thanthi", domain="www.dailythanthi.com",
        language="ta", kind="news",
        sitemap_index="https://www.dailythanthi.com/sitemap.xml",
        daily_patterns=[
            "https://www.dailythanthi.com/sitemap/sitemap-daily-{date}.xml"],
        section_roots=["/news/tamilnadu/", "/news/district/", "/news/vellore/"],
        url_exclude=["/login", "/tag-", "/page-", "/slug-", "/user-", "/preview"],
        request_delay=0.4, max_articles_per_run=1200,
        notes="Daily sitemaps back to 2016-12."),
    "maalaimalar": _mk(
        key="maalaimalar", name="Maalai Malar", domain="www.maalaimalar.com",
        language="ta", kind="news",
        sitemap_index="https://www.maalaimalar.com/sitemap.xml",
        daily_patterns=[
            "https://www.maalaimalar.com/sitemap/sitemap-daily-{date}.xml"],
        section_roots=["/news/district/", "/news/tamilnadu/"],
        url_exclude=["/login", "/tag-", "/page-", "/slug-", "/user-", "/buzz"],
        request_delay=0.4, max_articles_per_run=1200,
        notes="Deepest Tamil archive: daily sitemaps back to 2011-12."),
    "thehindu": _mk(
        key="thehindu", name="The Hindu", domain="www.thehindu.com",
        language="en", kind="news",
        sitemap_index=None,
        daily_patterns=[
            "https://www.thehindu.com/sitemap/googlenews/all/all.xml"],
        section_roots=["/news/national/tamil-nadu/", "/news/cities/",
                       "/news/national/"],
        url_exclude=["/search", "/todays-paper/", "/photo/"],
        request_delay=0.5, max_articles_per_run=800,
        notes="English corroboration + historic Tamil Nadu crime."),
    "dtnext": _mk(
        key="dtnext", name="DT Next", domain="www.dtnext.in",
        language="en", kind="news",
        sitemap_index="https://www.dtnext.in/sitemap.xml",
        daily_patterns=[
            "https://www.dtnext.in/sitemap/sitemap-daily-{date}.xml"],
        section_roots=["/news/tamilnadu/", "/news/"],
        url_exclude=["/tags", "/page-", "/user-", "/preview/story"],
        request_delay=0.35, max_articles_per_run=600),
    "nie": _mk(
        key="nie", name="The New Indian Express",
        domain="www.newindianexpress.com", language="en", kind="news",
        sitemap_index="https://www.newindianexpress.com/sitemap.xml",
        daily_patterns=[
            "https://www.newindianexpress.com/sitemap/sitemap-daily-{date}.xml"],
        section_roots=["/states/tamil-nadu/", "/cities/", "/nation/"],
        url_exclude=["/search"],
        request_delay=0.35, max_articles_per_run=600),
}
