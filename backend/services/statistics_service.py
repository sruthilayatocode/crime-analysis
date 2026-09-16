"""
Statistics service.

Builds dashboard-friendly aggregates from real crime
records for frontend chart integration.
"""

from datetime import datetime

UNKNOWN_LABEL = "Unknown"


def _increment(counter, key):

    counter[key] = counter.get(key, 0) + 1


def _extract_month(crime_date):
    """
    Extract a YYYY-MM month label from a crime_date
    string. Returns "Unknown" when the value cannot
    be parsed.

    Supports ISO-style dates (YYYY-MM-DD, YYYY-MM) as
    well as common human-readable formats such as
    "DD Month YYYY" (for example "31 July 2026").
    """

    if not crime_date:
        return UNKNOWN_LABEL

    text = str(crime_date).strip()

    if not text:
        return UNKNOWN_LABEL

    try:
        parsed = datetime.strptime(
            text,
            "%Y-%m-%d"
        )
        return f"{parsed.year}-{parsed.month:02d}"
    except ValueError:
        pass

    try:
        parsed = datetime.strptime(
            text,
            "%Y-%m"
        )
        return f"{parsed.year}-{parsed.month:02d}"
    except ValueError:
        pass

    try:
        parsed = datetime.strptime(
            text,
            "%d %B %Y"
        )
        return f"{parsed.year}-{parsed.month:02d}"
    except ValueError:
        pass

    try:
        parsed = datetime.strptime(
            text,
            "%d %b %Y"
        )
        return f"{parsed.year}-{parsed.month:02d}"
    except ValueError:
        pass

    return UNKNOWN_LABEL


def build_statistics(crimes):
    """
    Aggregate crime records into dashboard statistics:
    total count, counts by type/severity/area/month.
    """

    by_type = {}
    by_severity = {}
    by_area = {}
    by_month = {}

    for crime in crimes:

        crime_type = (
            crime.get("crime_type")
            or UNKNOWN_LABEL
        )

        severity = (
            crime.get("severity")
            or UNKNOWN_LABEL
        )

        area = (
            crime.get("location_name")
            or UNKNOWN_LABEL
        )

        month = _extract_month(
            crime.get("crime_date")
        )

        _increment(by_type, crime_type)
        _increment(by_severity, severity)
        _increment(by_area, area)
        _increment(by_month, month)

    # Sort month labels chronologically,
    # keeping "Unknown" entries last.
    sorted_months = dict(
        sorted(
            by_month.items(),
            key=lambda item: (
                item[0] == UNKNOWN_LABEL,
                item[0]
            )
        )
    )

    return {
        "total_crimes": len(crimes),
        "by_type": by_type,
        "by_severity": by_severity,
        "by_area": by_area,
        "by_month": sorted_months,
    }