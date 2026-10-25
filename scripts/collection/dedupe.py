"""Incident-level deduplication.

One real-world incident may appear in many articles. Records are grouped by
(district, locality, crime_type, incident window) and merged when headline
similarity >= DEDUPE_TITLE_SIMILARITY, or when a crime/case number matches
exactly. Deterministic: groups get stable duplicate_group_ids; the
highest-confidence, best-sourced article is the incident's primary record and
all other source URLs go to the provenance table.
"""
from __future__ import annotations
import re
from datetime import date

from scripts.collection.config import (DEDUPE_TITLE_SIMILARITY,
                                       DEDUPE_DATE_WINDOW_DAYS)
from scripts.collection.store import normalize_title

_STOP = set("a an the in at on of and or to for by with from after over "
            "man woman held arrested booked case police district vellore "
            "tamil nadu near nears".split())


def _tokens(t: str):
    return [w for w in normalize_title(t).split()
            if w and w not in _STOP and len(w) > 2]


def _jaccard(a, b) -> float:
    if not a or not b:
        return 0.0
    sa, sb = set(a), set(b)
    return len(sa & sb) / len(sa | sb)


def _days(iso_a, iso_b):
    """Signed day difference; None if either date missing."""
    def p(s):
        try:
            y, m, d = s[:10].split("-")
            return date(int(y), int(m), int(d))
        except Exception:
            return None
    da, db = p(iso_a or ""), p(iso_b or "")
    if not da or not db:
        return None
    return abs((da - db).days)


def _same_incident(a, b) -> bool:
    # 0) explicit identifiers trump everything
    for f in ("crime_number", "case_number"):
        if a.get(f) and b.get(f):
            return a[f] == b[f]
    # 1) crime type must agree (or one is unknown)
    if a.get("crime_type") and b.get("crime_type") \
            and a["crime_type"] != b["crime_type"]:
        return False
    # 2) same locality (or unknown) — different localities are different
    la, lb = (a.get("locality") or "").lower(), (b.get("locality") or "").lower()
    if la and lb and la != lb:
        return False
    # 3) temporal proximity
    dd = _days(a.get("incident_date") or a.get("source_publication_date"),
               b.get("incident_date") or b.get("source_publication_date"))
    if dd is not None and dd > DEDUPE_DATE_WINDOW_DAYS:
        return False
    # 4) headline similarity
    return _jaccard(_tokens(a.get("title", "")), _tokens(b.get("title", ""))) \
        >= DEDUPE_TITLE_SIMILARITY


def group_incidents(records: list) -> list:
    """Greedy single-pass clustering (deterministic: input order fixed by
    caller sorting). Returns list of groups; each group is a list of records."""
    groups: list[list] = []
    for rec in records:
        placed = False
        for g in groups:
            if _same_incident(g[0], rec):
                g.append(rec)
                placed = True
                break
        if not placed:
            groups.append([rec])
    return groups


def merge_group(group: list, gid: str) -> dict:
    """Collapse a duplicate group into ONE incident record + provenance rows."""
    # primary = longest description (richest evidence), then earliest date
    prim = sorted(group, key=lambda r: (
        -len(r.get("description") or ""),
        r.get("incident_date") or r.get("source_publication_date") or "9999")
    )[0]

    dates = sorted({r["incident_date"] for r in group if r.get("incident_date")})
    localities = {r.get("locality") for r in group if r.get("locality")}
    types = {r.get("crime_type") for r in group if r.get("crime_type")}

    inc = {
        "incident_id": gid,
        "incident_date": dates[0] if dates else "",
        # year falls back to publication year when no incident date is known
        "incident_year": (dates[0] if dates
                          else (prim.get("source_publication_date") or ""))[:4],
        "crime_type": sorted(types)[0] if types else "",
        "crime_subtype": "",
        "description": prim.get("description", ""),
        "locality": sorted(localities)[0] if localities else "",
        "police_station": prim.get("police_station", ""),
        "district": prim.get("district", "Vellore"),
        "state": prim.get("state", "Tamil Nadu"),
        # scope provenance must survive the merge so confidence scoring works
        "scope_class": prim.get("scope_class", ""),
        "scope_basis": prim.get("scope_basis", ""),
        "crime_category": prim.get("crime_category", ""),
        # primary-source provenance must survive the merge: the confidence
        # scorer uses source_publication_date as the incident-date fallback.
        "source_name": prim.get("source_name", ""),
        "source_url": prim.get("source_url", ""),
        "source_publication_date": prim.get("source_publication_date", ""),
        "source_type": "NEWS",
        "title": prim.get("title", ""),
        "latitude": "", "longitude": "",
        "geocoding_status": "pending",
        "validation_status": prim.get("validation_status", "validated"),
        "confidence_score": "",
        "duplicate_group_id": gid,
        "n_sources": len(group),
    }
    if len(types) > 1:
        inc["validation_status"] = "review_type_conflict"
    if len(localities) > 1:
        inc["validation_status"] = "review_locality_conflict"

    prov = [{
        "incident_id": gid,
        "source_name": r.get("source_name", ""),
        "source_url": r.get("source_url", ""),
        "source_publication_date": r.get("source_publication_date", ""),
        "source_type": "NEWS",
        "title": r.get("title", ""),
        "is_primary": r is prim,
    } for r in group]
    return inc, prov


def deduplicate(records: list):
    """records -> (incidents, provenance_rows, n_duplicates)."""
    order = sorted(records, key=lambda r: (
        r.get("incident_date") or r.get("source_publication_date") or "9999",
        r.get("source_url") or ""))
    groups = group_incidents(order)
    incidents, prov = [], []
    for i, g in enumerate(groups, 1):
        gid = f"CS-{len(order):06d}-{i:04d}"
        inc, pv = merge_group(g, gid)
        incidents.append(inc)
        prov.extend(pv)
    n_dup = len(order) - len(groups)
    return incidents, prov, n_dup
