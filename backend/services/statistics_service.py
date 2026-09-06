"""
Statistics service.

Builds dashboard-friendly aggregates from real crime
records for frontend chart integration.
"""

UNKNOWN_LABEL = "Unknown"


def _increment(counter, key):

    counter[key] = counter.get(key, 0) + 1


def _extract_month(crime_date):
    """
    Extract a YYYY-MM month label from a crime_date
    string (YYYY-MM-DD or YYYY-MM). Returns
    "Unknown" when the value cannot be parsed.
    """

    if not crime_date:
        return UNKNOWN_LABEL

    text = str(crime_date).strip()

    parts = text.split("-")

    if len(parts) >= 2:

        year = parts[0]
        month = parts[1]

        if (
            len(year) == 4
            and year.isdigit()
            and len(month) in (1, 2)
            and month.isdigit()
            and 1 <= int(month) <= 12
        ):
            return f"{year}-{int(month):02d}"

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