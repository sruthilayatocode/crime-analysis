"""Transparent confidence scoring.

HIGH   = scope-confirmed + explicit incident date + locality + category hit
         AND description substantial.
MEDIUM = scope-confirmed + category hit, but incident date missing (falls back
         to publication date) OR locality coarse OR thin description.
LOW    = everything else (kept as CANDIDATE, excluded from main dataset).

Only config.ACCEPT_CONFIDENCE records enter the validated incident dataset.
"""
from __future__ import annotations

from scripts.collection.config import (ACCEPT_SCOPES, MIN_DESCRIPTION_CHARS,
                                       ACCEPT_CONFIDENCE)


def score(rec: dict) -> str:
    scope_ok = rec.get("scope_class") in ACCEPT_SCOPES
    has_date = bool(rec.get("incident_date"))
    has_loc = bool(rec.get("locality"))
    has_cat = bool(rec.get("crime_type") or rec.get("crime_category"))
    rich = len(rec.get("description") or "") >= MIN_DESCRIPTION_CHARS

    if scope_ok and has_date and has_loc and has_cat and rich:
        return "HIGH"
    if scope_ok and has_cat and (has_date or rec.get("source_publication_date")):
        return "MEDIUM"
    return "LOW"


def score_all(records: list) -> dict:
    counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for r in records:
        s = score(r)
        r["confidence_score"] = s
        counts[s] += 1
    return counts


def admissible(rec: dict) -> bool:
    return rec.get("confidence_score") in ACCEPT_CONFIDENCE
