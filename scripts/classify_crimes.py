#!/usr/bin/env python
"""
Crime-type classification correction stage.

Pipeline position: between location enrichment and risk scoring.

  enrich_locations.py  ->  news_location_enriched.csv
  classify_crimes.py   ->  news_location_enriched.csv  (re-classifies Other)
  score_crime_risk.py  ->  news_scored_final.csv

The upstream classifier assigns 'Other' to incidents it cannot place into a
standard crime category.  Left untouched, Other records would either receive
no severity score (if absent from crime_categories.csv) or a generic one.

This script inspects the title + description of every 'Other' record and
applies a priority-ordered, keyword-based re-classification so that each record
is promoted to the most specific applicable crime type.  Records that genuinely
do not fit any standard category are left as 'Other', which maps to Medium/5.

Usage:
    python scripts/classify_crimes.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "news_location_enriched.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "news_location_enriched.csv"
REPORT_FILE = PROJECT_ROOT / "data" / "reports" / "crime_classification_report.txt"


# Keyword rules -- priority order (most specific / severe first).
# Vehicle Theft handled via COMBINATION_RULES only (see below).
CLASSIFICATION_RULES = [
    ("Murder",        ["killed","killing","murder","homicide","shot dead",
                        "gunned down","strangled","asphyxiated"]),
    ("Assault",       ["stab","stabbing","stabbed","punch","punches","punching",
                        "attack","assaulted","beaten","slapping","slapped","slap",
                        "pushed","pushing","beating","lashed","battered",
                        "cudgel","lathi","slash","slashed"]),
    ("Sexual Assault",["rape","raped","sexual assault","sexual harassment",
                        "molest","molestation","molested","gang-rape","gang rape"]),
    ("Cyber Crime",   ["cyber","digital arrest","online scam","hacking","phishing",
                        "ransomware","malware","cybercrime","cyber slavery",
                        "digital fraud"]),
    ("Robbery",       ["robbery","robbed","at gunpoint","gunpoint","armed"]),
    ("Theft",         ["steal","stolen","theft","stealing","burglary","burglar",
                        "pickpocket","pick-pocket","shoplifting","loot","looted"]),
    ("Fraud",         ["fraud","impersonate","impersonating","posing as",
                        "scam","racket","deception","embezzle","cheating",
                        "fake document","forge","forged","forgery"]),
]

# Both keywords must appear (theft verb + vehicle keyword)
COMBINATION_RULES = [
    ("Vehicle Theft", ["steal","bike"]),
    ("Vehicle Theft", ["steal","two-wheeler"]),
    ("Vehicle Theft", ["steal","motorcycle"]),
    ("Vehicle Theft", ["steal","motorbike"]),
    ("Vehicle Theft", ["steal","scooter"]),
    ("Vehicle Theft", ["stolen","bike"]),
    ("Vehicle Theft", ["stolen","two-wheeler"]),
    ("Vehicle Theft", ["stealing","bike"]),
    ("Vehicle Theft", ["stealing","two-wheeler"]),
    ("Vehicle Theft", ["stealing","motorcycle"]),
    ("Vehicle Theft", ["theft","bike"]),
    ("Vehicle Theft", ["theft","two-wheeler"]),
    ("Vehicle Theft", ["theft","motorcycle"]),
    ("Vehicle Theft", ["theft","scooter"]),
]


def normalize_text(text: str) -> str:
    """Lowercase and collapse whitespace for keyword matching."""
    return " ".join((text or "").lower().split())


def classify_other(title: str, description: str) -> str:
    """Re-classify a record currently typed Other.  Returns crime type."""
    text = normalize_text(title + " " + description)
    for ctype, kws in COMBINATION_RULES:
        if all(kw in text for kw in kws):
            return ctype
    for ctype, kws in CLASSIFICATION_RULES:
        for kw in kws:
            if kw in text:
                return ctype
    return "Other"


def main() -> int:
    """Read enriched data, re-classify Other records, write back, report."""
    with INPUT_FILE.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        records = list(reader)

    total_other = 0
    reclassified: dict[str, int] = {}
    sample: list[tuple[str, str, str, str]] = []

    for row in records:
        if (row.get("crime_type", "") or "").strip() != "Other":
            continue
        total_other += 1
        old_type = "Other"
        new_type = classify_other(
            row.get("title", ""), row.get("description", "")
        )
        if new_type != old_type:
            row["crime_type"] = new_type
            reclassified[new_type] = reclassified.get(new_type, 0) + 1
        else:
            reclassified["Other"] = reclassified.get("Other", 0) + 1
        sample.append((
            str(row.get("article_id", ""))[:12],
            old_type,
            new_type,
            str(row.get("title", ""))[:70],
        ))

    # Write back
    with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)

    # Report
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    lines_r = [
        "CRIME TYPE CLASSIFICATION REPORT",
        "=" * 60,
        "",
        f"Input / output file: {OUTPUT_FILE}",
        f"Total Other records reviewed: {total_other}",
        "",
        "Re-classification summary:",
    ]
    for ct, cnt in sorted(reclassified.items(), key=lambda x: (-x[1], x[0])):
        lines_r.append(f"  {ct}: {cnt}")
    lines_r.append("")
    lines_r.append("Detailed re-classifications:")
    for aid, old, new, title in sample:
        tag = "RECLASSIFIED" if new != old else "unchanged (stays Other)"
        lines_r.append(f"  {aid}  {old} -> {new}  ({tag})")
        lines_r.append(f"    title: {title}")
    lines_r.append("")
    lines_r.append("Remaining Other records keep the default Medium / score 5")
    lines_r.append("mapping defined in crime_categories.csv.")
    lines_r.append("=" * 60)

    report_text = chr(10).join(lines_r)
    with REPORT_FILE.open("w", encoding="utf-8") as f:
        f.write(report_text + chr(10))
    print(report_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
