"""
Descriptive crime pattern analysis.

This module provides summary statistics for crime records
without creating artificial ML labels or claiming predictive
performance.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional


def analyze_crime_patterns(
    records: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Compute descriptive statistics for crime records.

    Parameters
    ----------
    records : list of dict
        Crime records.

    Returns
    -------
    dict
        {
            "total_records": int,
            "crime_type_distribution": dict,
            "severity_score_distribution": dict,
            "risk_level_distribution": dict,
            "location_distribution": dict,
            "district_distribution": dict,
            "dominant_crime_types": list,
            "limitations": str,
        }
    """
    total_records = len(records)

    crime_type_counter: Counter = Counter()
    severity_counter: Counter = Counter()
    risk_counter: Counter = Counter()
    location_counter: Counter = Counter()
    district_counter: Counter = Counter()

    for record in records:
        crime_type = record.get("crime_type")
        if crime_type:
            crime_type_counter[crime_type] += 1

        severity = record.get("severity_score")
        if severity is not None:
            try:
                severity_counter[int(severity)] += 1
            except (TypeError, ValueError):
                pass

        risk = record.get("risk_level")
        if risk:
            risk_counter[risk] += 1

        location = record.get("location_name")
        if location:
            location_counter[location] += 1

        district = record.get("district")
        if district:
            district_counter[district] += 1

    dominant_crime_types = [
        {"crime_type": ct, "count": count}
        for ct, count in crime_type_counter.most_common(10)
    ]

    return {
        "total_records": total_records,
        "crime_type_distribution": dict(sorted(crime_type_counter.items())),
        "severity_score_distribution": dict(sorted(severity_counter.items())),
        "risk_level_distribution": dict(sorted(risk_counter.items())),
        "location_distribution": dict(sorted(location_counter.items())),
        "district_distribution": dict(sorted(district_counter.items())),
        "dominant_crime_types": dominant_crime_types,
        "limitations": (
            "Risk_level and severity_score are currently rule-derived "
            "from crime_type and are not independent outcome labels."
        ),
    }


def get_crime_type_distribution(
    records: List[Dict[str, Any]]
) -> Dict[str, int]:
    """Return crime type counts."""
    result = analyze_crime_patterns(records)
    return result["crime_type_distribution"]


def get_severity_distribution(
    records: List[Dict[str, Any]]
) -> Dict[int, int]:
    """Return severity score counts."""
    result = analyze_crime_patterns(records)
    return result["severity_score_distribution"]


def get_risk_level_distribution(
    records: List[Dict[str, Any]]
) -> Dict[str, int]:
    """Return risk level counts."""
    result = analyze_crime_patterns(records)
    return result["risk_level_distribution"]
