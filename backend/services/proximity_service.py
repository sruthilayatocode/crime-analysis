from math import radians, sin, cos, sqrt, atan2


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two GPS coordinates
    using the Haversine formula.

    The returned distance is in meters.
    """

    earth_radius = 6371000

    latitude_difference = radians(lat2 - lat1)
    longitude_difference = radians(lon2 - lon1)

    a = (
        sin(latitude_difference / 2) ** 2
        + cos(radians(lat1))
        * cos(radians(lat2))
        * sin(longitude_difference / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = earth_radius * c

    return round(distance, 2)


def check_proximity(
    user_lat,
    user_lon,
    crime_lat,
    crime_lon,
    alert_radius=1000
):
    """
    Check whether the user is within the selected
    alert radius of a crime location.

    The alert radius is measured in meters.
    """

    distance = calculate_distance(
        user_lat,
        user_lon,
        crime_lat,
        crime_lon
    )

    is_nearby = distance <= alert_radius

    return {
        "distance_in_meters": distance,
        "alert_radius_in_meters": alert_radius,
        "is_nearby": is_nearby,
        "message": (
            "Warning: You are near a reported crime location."
            if is_nearby
            else "You are outside the selected crime alert radius."
        )
    }