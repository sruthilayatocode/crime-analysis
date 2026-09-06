#!/usr/bin/env python
"""
Crime severity/risk scoring stage for enriched Vellore crime news.

Reads the location-enriched dataset, preserves all existing columns, appends
severity_score and risk_level, and writes a scoring report. Unmapped crime
types are reported explicitly and receive no arbitrary severity score.
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "news_location_enriched.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "news_scored_final.csv"
REPORT_FILE = PROJECT_ROOT / "data" / "reports" / "risk_scoring_final_report.txt"
CRIME_CATEGORIES_FILE = PROJECT_ROOT / "data" / "reference" / "crime_categories.csv"
SEVERITY_MAPPING_FILE = PROJECT_ROOT / "data" / "reference" / "severity_mapping.csv"


def normalize(value: str) -> str:
    return (value or "").strip()


def load_severity_mapping() -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    with SEVERITY_MAPPING_FILE.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            severity = normalize(row.get("severity", ""))
            score = normalize(row.get("risk_score", ""))
            if severity:
                mapping[severity.lower()] = score
    return mapping


def load_crime_categories(valid_scores: Dict[str, str]) -> Dict[str, Tuple[str, str]]:
    categories: Dict[str, Tuple[str, str]] = {}
    with CRIME_CATEGORIES_FILE.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            crime_type = normalize(row.get("crime_type", ""))
            severity = normalize(row.get("severity", ""))
            score = normalize(row.get("risk_score", ""))
            if not crime_type or not severity:
                continue
            expected_score = valid_scores.get(severity.lower())
            if expected_score and not score:
                score = expected_score
            categories[crime_type.lower()] = (severity, score)
    return categories


def write_report(
    input_records: int,
    output_records: int,
    crime_distribution: Counter,
    severity_distribution: Counter,
    risk_distribution: Counter,
    mapping_used: Dict[str, Tuple[str, str]],
    unknown_types: Counter,
    missing_severity: int,
) -> None:
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = []
    lines.append("RISK SCORING REPORT")
    lines.append("=" * 60)
    lines.append("")
    lines.append("Input file:  %s" % INPUT_FILE)
    lines.append("Output file: %s" % OUTPUT_FILE)
    lines.append("")
    lines.append("Input records:  %d" % input_records)
    lines.append("Output records: %d" % output_records)
    lines.append("")

    lines.append("All crime types:")
    for key, count in sorted(crime_distribution.items(), key=lambda item: (-item[1], item[0])):
        lines.append("  %s: %d" % (key or "(blank)", count))
    lines.append("")

    lines.append("Severity mapping used:")
    for crime_type in sorted(crime_distribution):
        mapped = mapping_used.get(crime_type.lower())
        if mapped:
            lines.append("  %s -> %s (%s)" % (crime_type, mapped[0], mapped[1]))
        else:
            lines.append("  %s -> UNMAPPED" % (crime_type or "(blank)"))
    lines.append("")

    lines.append("Severity-score distribution:")
    for key, count in sorted(severity_distribution.items(), key=lambda item: (item[0] == "", item[0])):
        lines.append("  %s: %d" % (key or "(missing)", count))
    lines.append("")

    lines.append("Risk-level distribution:")
    for key, count in sorted(risk_distribution.items(), key=lambda item: (item[0] == "Unknown", item[0])):
        lines.append("  %s: %d" % (key or "(blank)", count))
    lines.append("")

    lines.append("Unknown/unmapped crime types:")
    if unknown_types:
        for key, count in sorted(unknown_types.items(), key=lambda item: (-item[1], item[0])):
            lines.append("  %s: %d" % (key or "(blank)", count))
    else:
        lines.append("  None")
    lines.append("")

    lines.append("Records with missing severity: %d" % missing_severity)

    with REPORT_FILE.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    valid_scores = load_severity_mapping()
    crime_categories = load_crime_categories(valid_scores)

    with INPUT_FILE.open("r", encoding="utf-8", newline="") as f:
        records = list(csv.DictReader(f))

    output_rows: List[Dict[str, str]] = []
    crime_distribution: Counter = Counter()
    severity_distribution: Counter = Counter()
    risk_distribution: Counter = Counter()
    unknown_types: Counter = Counter()
    missing_severity = 0

    for row in records:
        crime_type = normalize(row.get("crime_type", ""))
        crime_distribution[crime_type] += 1

        out = dict(row)
        mapped = crime_categories.get(crime_type.lower())
        if mapped:
            risk_level, severity_score = mapped
            out["severity_score"] = severity_score
            out["risk_level"] = risk_level
        else:
            out["severity_score"] = ""
            out["risk_level"] = "Unknown"
            unknown_types[crime_type] += 1
            missing_severity += 1

        severity_distribution[out["severity_score"]] += 1
        risk_distribution[out["risk_level"]] += 1
        output_rows.append(out)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(records[0].keys()) if records else []
    for field in ("severity_score", "risk_level"):
        if field not in fieldnames:
            fieldnames.append(field)

    with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(output_rows)

    write_report(
        input_records=len(records),
        output_records=len(output_rows),
        crime_distribution=crime_distribution,
        severity_distribution=severity_distribution,
        risk_distribution=risk_distribution,
        mapping_used=crime_categories,
        unknown_types=unknown_types,
        missing_severity=missing_severity,
    )

    print("=" * 60)
    print("Crime Risk Scoring Results")
    print("=" * 60)
    print("Total records: %d" % len(output_rows))
    print("")
    print("Crime-type distribution:")
    for key, count in sorted(crime_distribution.items(), key=lambda item: (-item[1], item[0])):
        print("  %s: %d" % (key or "(blank)", count))
    print("")
    print("Severity-score distribution:")
    for key, count in sorted(severity_distribution.items(), key=lambda item: (item[0] == "", item[0])):
        print("  %s: %d" % (key or "(missing)", count))
    print("")
    print("Risk-level distribution:")
    for key, count in sorted(risk_distribution.items(), key=lambda item: (item[0] == "Unknown", item[0])):
        print("  %s: %d" % (key or "(blank)", count))
    print("")
    print("Unknown/unmapped crime types:")
    if unknown_types:
        for key, count in sorted(unknown_types.items(), key=lambda item: (-item[1], item[0])):
            print("  %s: %d" % (key or "(blank)", count))
    else:
        print("  None")
    print("")
    print("Records with missing severity: %d" % missing_severity)
    print("Output file: %s" % OUTPUT_FILE)
    print("Report file: %s" % REPORT_FILE)
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
