from collections import defaultdict


def analyze_hotspots(crimes):
    """
    Analyze crime records and group them by location.

    This is a temporary rule-based hotspot analysis.
    It will later be replaced with DBSCAN when the
    final crime dataset is integrated.
    """

    if not crimes:
        return []

    location_groups = defaultdict(list)

    for crime in crimes:

        location = (
            crime.get("location")
            or "Unknown"
        )

        location_groups[location].append(
            crime
        )

    hotspots = []

    for location, crime_records in (
        location_groups.items()
    ):

        crime_count = len(
            crime_records
        )

        average_latitude = sum(
            crime.get("latitude", 0)
            for crime in crime_records
        ) / crime_count

        average_longitude = sum(
            crime.get("longitude", 0)
            for crime in crime_records
        ) / crime_count

        if crime_count >= 5:
            risk_level = "High"

        elif crime_count >= 3:
            risk_level = "Medium"

        else:
            risk_level = "Low"

        hotspots.append({
            "location": location,
            "crime_count": crime_count,
            "average_latitude": round(
                average_latitude,
                6
            ),
            "average_longitude": round(
                average_longitude,
                6
            ),
            "risk_level": risk_level
        })

    hotspots.sort(
        key=lambda hotspot: (
            hotspot["crime_count"]
        ),
        reverse=True
    )

    return hotspots