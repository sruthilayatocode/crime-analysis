"""
Descriptive temporal analysis for crime/article data.

This module provides publication-date trend analysis only.
It does NOT predict future crime and does NOT fabricate
missing dates.

Important terminology
---------------------
All outputs use the terms "publication-date" or "article-date"
because the database stores news article publication timestamps,
not verified crime-occurrence timestamps.
"""

from __future__ import annotations

import calendar
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd


def _parse_date(raw: Any) -> Optional[pd.Timestamp]:
    """
    Parse a date string into a pandas Timestamp, or None on failure.

    Accepts ISO-8601, RFC-1123, and common human-readable formats.
    """
    if raw is None:
        return None

    text = str(raw).strip()

    if not text:
        return None

    try:
        parsed = pd.to_datetime(text, errors="coerce")

        if parsed is None or pd.isna(parsed):
            return None

        if parsed.tzinfo is not None:
            parsed = parsed.tz_convert(None)

        return parsed
    except Exception:
        return None


def _extract_date_features(parsed: pd.Timestamp) -> Dict[str, Optional[int]]:
    """Extract month, year, and day-of-week from a parsed Timestamp."""
    return {
        "year": int(parsed.year),
        "month": int(parsed.month),
        "month_name": calendar.month_name[int(parsed.month)],
        "day_of_week": int(parsed.weekday()),
        "day_name": calendar.day_name[int(parsed.weekday())],
    }


def analyze_temporal_patterns(
    records: List[Dict[str, Any]],
    date_field: str = "crime_date",
) -> Dict[str, Any]:
    """
    Compute descriptive publication-date patterns.

    Parameters
    ----------
    records : list of dict
        Crime records. Each record should contain the field named
        by ``date_field``.
    date_field : str
        Name of the date field in each record. Defaults to
        ``"crime_date"`` because the database stores article
        publication dates under this column.

    Returns
    -------
    dict
        {
            "total_records": int,
            "valid_dates": int,
            "invalid_dates": int,
            "excluded_dates": int,
            "date_range": {"start": str, "end": str} or None,
            "monthly_counts": dict,
            "yearly_counts": dict,
            "day_of_week_counts": dict,
            "crime_type_monthly": dict,
            "limitations": str,
        }
    """
    total_records = len(records)
    valid_records = []
    invalid_count = 0

    for record in records:
        raw = record.get(date_field)

        if raw is None:
            invalid_count += 1
            continue

        text = str(raw).strip()

        if not text:
            invalid_count += 1
            continue

        parsed = _parse_date(text)

        if parsed is None:
            invalid_count += 1
            continue

        features = _extract_date_features(parsed)
        features["parsed_date"] = parsed
        features["original_date"] = text
        valid_records.append(features)

    valid_count = len(valid_records)
    excluded_count = total_records - valid_count

    date_range = None
    if valid_records:
        dates = [r["parsed_date"] for r in valid_records]
        date_range = {
            "start": min(dates).strftime("%Y-%m-%d"),
            "end": max(dates).strftime("%Y-%m-%d"),
        }

    monthly_counter: Counter = Counter()
    yearly_counter: Counter = Counter()
    dow_counter: Counter = Counter()
    crime_type_monthly: Dict[str, Counter] = defaultdict(Counter)

    for record, features in zip(records, valid_records + [{}] * excluded_count):
        if not features:
            continue

        year = features["year"]
        month = features["month"]
        dow = features["day_of_week"]
        month_key = f"{year:04d}-{month:02d}"
        year_key = f"{year:04d}"
        dow_name = features["day_name"]

        monthly_counter[month_key] += 1
        yearly_counter[year_key] += 1
        dow_counter[dow_name] += 1

        crime_type = record.get("crime_type")
        if crime_type:
            crime_type_monthly[crime_type][month_key] += 1

    monthly_counts = dict(sorted(monthly_counter.items()))
    yearly_counts = dict(sorted(yearly_counter.items()))
    day_of_week_counts = dict(sorted(dow_counter.items()))

    crime_type_monthly_out = {
        ct: dict(sorted(counter.items()))
        for ct, counter in sorted(crime_type_monthly.items())
    }

    return {
        "total_records": total_records,
        "valid_dates": valid_count,
        "invalid_dates": invalid_count,
        "excluded_dates": excluded_count,
        "date_range": date_range,
        "monthly_counts": monthly_counts,
        "yearly_counts": yearly_counts,
        "day_of_week_counts": day_of_week_counts,
        "crime_type_monthly": crime_type_monthly_out,
        "limitations": (
            "These are publication-date trends, not verified "
            "crime-occurrence trends. Article publication dates "
            "may lag behind actual events, and missing/invalid "
            "dates have been excluded from the counts."
        ),
    }


def get_monthly_crime_counts(
    records: List[Dict[str, Any]],
    date_field: str = "crime_date",
) -> Dict[str, int]:
    """
    Convenience wrapper returning only monthly publication-date counts.

    Returns a dict mapping 'YYYY-MM' strings to counts.
    """
    result = analyze_temporal_patterns(records, date_field=date_field)
    return result["monthly_counts"]


def get_yearly_crime_counts(
    records: List[Dict[str, Any]],
    date_field: str = "crime_date",
) -> Dict[str, int]:
    """
    Convenience wrapper returning only yearly publication-date counts.

    Returns a dict mapping 'YYYY' strings to counts.
    """
    result = analyze_temporal_patterns(records, date_field=date_field)
    return result["yearly_counts"]


def get_day_of_week_counts(
    records: List[Dict[str, Any]],
    date_field: str = "crime_date",
) -> Dict[str, int]:
    """
    Convenience wrapper returning only day-of-week publication-date counts.

    Returns a dict mapping weekday names to counts.
    """
    result = analyze_temporal_patterns(records, date_field=date_field)
    return result["day_of_week_counts"]
