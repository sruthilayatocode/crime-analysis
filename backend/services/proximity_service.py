from math import radians, sin, cos, sqrt, atan2


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two GPS coordinates
    using the Haversine formula.

    Returns distance in meters.
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

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    distance = earth_radius * c

    return distance


def check_proximity(
    user_latitude,
    user_longitude,
    hotspot_latitude,
    hotspot_longitude,
    alert_radius=500
):
    """
    Check whether user is within alert radius
    of a crime hotspot.
    """

    distance = calculate_distance(
        user_latitude,
        user_longitude,
        hotspot_latitude,
        hotspot_longitude
    )

    return {
        "distance_meters": round(distance, 2),
        "is_nearby": distance <= alert_radius,
        "alert_radius_meters": alert_radius
    }