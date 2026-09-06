#!/usr/bin/env python
"""
Enrich incident locality confidence for validated Vellore crime news.

This stage does not geocode and does not modify the validated input file.
It only extracts explicitly supported incident localities from article title
and description, then writes an enriched CSV plus a review CSV.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "news_validated.csv"
LOCALITIES_CSV = PROJECT_ROOT / "data" / "reference" / "vellore_localities.csv"
LOCALITIES_CONFIG = PROJECT_ROOT / "data" / "reference" / "vellore_localities_config.json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "news_location_enriched.csv"
REVIEW_FILE = PROJECT_ROOT / "data" / "logs" / "location_enrichment_review.csv"


BROAD_VELLORE_PATTERNS = [
    r"\bvellore district\b",
    r"\btamil nadu'?s vellore\b",
    r"\b(?:in|near|at)\s+vellore\b",
]

AMBIGUOUS_VELLORE_PATTERNS = [
    r"\bfrom vellore\b",
    r"\bvellore (?:man|woman|doctor|trio|women|lady|youth|sp|police|court|jail|prison)\b",
    r"\bcmc vellore\b",
    r"\bvellore central prison\b",
]

INCIDENT_CONTEXT_PATTERNS = [
    r"\b(?:in|near|at|around|outside|inside)\s+{alias}\b",
    r"\b{alias}\s+(?:case|gang-rape|rape|murder|robbery|burglary|theft|assault)\b",
    r"\b(?:held|arrested|booked|attacked|murdered|robbed|stolen|assaulted|raped)\s+(?:in|near|at)\s+{alias}\b",
]

NON_INCIDENT_LOCATION_PATTERNS = [
    r"\b{alias}\s+(?:police|court|jail|prison)\b",
    r"\b(?:police|court|jail|prison)\s+(?:in|at|near)\s+{alias}\b",
]

OUTSIDE_OR_AMBIGUOUS = {
    "arani",
    "ranipet",
    "tirupattur",
    "tiruppattur",
    "ambur",
}

EXPLICIT_LANDMARK_PATTERNS = [
    ("Katpadi railway station", r"\bkatpadi railway station\b"),
    ("Vellore Fort", r"\bvellore fort\b"),
    ("Vellore GH", r"\bvellore gh\b"),
]


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def load_locality_aliases() -> Dict[str, List[str]]:
    localities: Dict[str, List[str]] = {}

    with LOCALITIES_CSV.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = normalize(row.get("locality_name", ""))
            if not name or "replace with real data" in name.lower():
                continue
            localities.setdefault(name, []).append(name)

    if LOCALITIES_CONFIG.exists():
        with LOCALITIES_CONFIG.open("r", encoding="utf-8") as f:
            config = json.load(f)
        for item in config.get("localities", []):
            name = normalize(item.get("name", ""))
            if not name:
                continue
            aliases = [name] + [normalize(a) for a in item.get("aliases", []) if normalize(a)]
            localities.setdefault(name, [])
            for alias in aliases:
                if alias not in localities[name]:
                    localities[name].append(alias)

    return localities


def article_text(row: Dict[str, str]) -> str:
    return normalize("%s %s" % (row.get("title", ""), row.get("description", "")))


def context_snippet(text: str, start: int, end: int) -> str:
    return normalize(text[max(0, start - 70):end + 70])


def is_non_incident_context(text_l: str, alias_pattern: str) -> bool:
    return any(
        re.search(pattern.format(alias=alias_pattern), text_l)
        for pattern in NON_INCIDENT_LOCATION_PATTERNS
    )


def find_explicit_locality(
    row: Dict[str, str],
    aliases_by_locality: Dict[str, List[str]],
) -> Tuple[str, str, str, str]:
    """Return locality, confidence, source, reason."""
    text = article_text(row)
    text_l = text.lower()

    for locality, pattern in EXPLICIT_LANDMARK_PATTERNS:
        match = re.search(pattern, text_l)
        if match:
            return locality, "HIGH", context_snippet(text, match.start(), match.end()), ""

    matches: List[Tuple[int, int, str, str]] = []
    for locality, aliases in aliases_by_locality.items():
        for alias in aliases:
            alias_l = alias.lower()
            if alias_l in OUTSIDE_OR_AMBIGUOUS:
                continue
            if alias_l == "vellore":
                continue
            alias_pattern = re.escape(alias_l).replace(r"\ ", r"\s+")
            if is_non_incident_context(text_l, alias_pattern):
                continue
            for pattern in INCIDENT_CONTEXT_PATTERNS:
                match = re.search(pattern.format(alias=alias_pattern), text_l)
                if match:
                    matches.append((match.start(), match.end(), locality, context_snippet(text, match.start(), match.end())))
                    break

    if matches:
        matches.sort(key=lambda item: (item[0], -(item[1] - item[0])))
        _, _, locality, source = matches[0]
        return locality, "HIGH", source, ""

    for pattern in AMBIGUOUS_VELLORE_PATTERNS:
        match = re.search(pattern, text_l)
        if match:
            return "", "UNKNOWN", context_snippet(text, match.start(), match.end()), "ambiguous_vellore_context_not_incident_location"

    for name in OUTSIDE_OR_AMBIGUOUS:
        match = re.search(r"\b%s\b" % re.escape(name), text_l)
        if match:
            return "", "UNKNOWN", context_snippet(text, match.start(), match.end()), "outside_or_ambiguous_locality:%s" % name

    if any(re.search(pattern, text_l) for pattern in BROAD_VELLORE_PATTERNS):
        return "", "LOW", "Vellore district/context mentioned, exact incident locality not stated", "district_or_broad_vellore_context_only"

    if re.search(r"\bvellore\b", text_l):
        return "", "LOW", "Vellore mentioned, exact incident locality not stated", "district_or_broad_vellore_context_only"

    return "", "UNKNOWN", "", "no_reliable_vellore_incident_location"


def main() -> int:
    aliases_by_locality = load_locality_aliases()
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REVIEW_FILE.parent.mkdir(parents=True, exist_ok=True)

    with INPUT_FILE.open("r", encoding="utf-8", newline="") as f:
        records = list(csv.DictReader(f))

    output_rows: List[Dict[str, str]] = []
    review_rows: List[Dict[str, str]] = []
    original_high = 0
    newly_identified = set()

    for row in records:
        original_locality = normalize(row.get("locality", ""))
        locality, confidence, source, reason = find_explicit_locality(row, aliases_by_locality)

        if locality and locality != original_locality:
            newly_identified.add(locality)
        if confidence == "HIGH":
            original_high += 1

        out = dict(row)
        out["locality"] = locality
        out["location_confidence"] = confidence
        out["location_source"] = source
        output_rows.append(out)

        if confidence in {"LOW", "UNKNOWN"}:
            review_rows.append({
                "article_id": row.get("article_id", ""),
                "title": row.get("title", ""),
                "original_locality": original_locality,
                "location_confidence": confidence,
                "review_reason": reason,
                "location_source": source,
            })

    fieldnames = list(records[0].keys()) if records else []
    for field in ("location_confidence", "location_source"):
        if field not in fieldnames:
            fieldnames.append(field)

    with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(output_rows)

    review_fields = [
        "article_id", "title", "original_locality", "location_confidence",
        "review_reason", "location_source",
    ]
    with REVIEW_FILE.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=review_fields)
        writer.writeheader()
        writer.writerows(review_rows)

    high = sum(1 for row in output_rows if row["location_confidence"] == "HIGH")
    low = sum(1 for row in output_rows if row["location_confidence"] == "LOW")
    unknown = sum(1 for row in output_rows if row["location_confidence"] == "UNKNOWN")
    unique_localities = sorted({row["locality"] for row in output_rows if row["locality"]})

    print("=" * 60)
    print("Location Enrichment Results")
    print("=" * 60)
    print("Total records:                %d" % len(output_rows))
    print("HIGH:                         %d" % high)
    print("LOW:                          %d" % low)
    print("UNKNOWN:                      %d" % unknown)
    print("Unique localities:            %s" % (", ".join(unique_localities) or "none"))
    print("Newly identified localities:  %s" % (", ".join(sorted(newly_identified)) or "none"))
    print("Output file:                  %s" % OUTPUT_FILE)
    print("Review file:                  %s" % REVIEW_FILE)
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
