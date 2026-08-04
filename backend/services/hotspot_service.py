def analyze_hotspots(crimes):
    """
    Groups crime records by location and calculates
    a simple risk level based on the number of crimes.
    """

    location_counts = {}

    for crime in crimes:
        location = crime.get("location", "Unknown")

        if location not in location_counts:
            location_counts[location] = 0

        location_counts[location] += 1

    hotspots = []

    for location, crime_count in location_counts.items():

        if crime_count >= 5:
            risk_level = "High"
        elif crime_count >= 3:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        hotspots.append({
            "location": location,
            "crime_count": crime_count,
            "risk_level": risk_level
        })

    return hotspots