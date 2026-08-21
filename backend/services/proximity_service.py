from math import radians, sin, cos, sqrt, atan2


def calculate_distance(
    latitude_1,
    longitude_1,
    latitude_2,
    longitude_2
):
    """
    Calculate the distance between two GPS coordinates
    using the Haversine formula.

    The returned distance is in meters.
    """

    earth_radius = 6371000

    latitude_difference = radians(
        latitude_2 - latitude_1
    )

    longitude_difference = radians(
        longitude_2 - longitude_1
    )

    a = (
        sin(latitude_difference / 2) ** 2
        + cos(radians(latitude_1))
        * cos(radians(latitude_2))
        * sin(longitude_difference / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    distance = earth_radius * c

    return round(distance, 2)


def check_proximity(
    user_latitude,
    user_longitude,
    hotspot_latitude,
    hotspot_longitude,
    alert_radius=500
):
    """
    Check whether the user's location is inside
    the selected crime-hotspot alert radius.
    """

    distance = calculate_distance(
        user_latitude,
        user_longitude,
        hotspot_latitude ,
        hotspot_longitude 
    )

    is_nearby = distance <= alert_radius

    return {
        "distance_meters": distance,
        "alert_radius_meters": alert_radius,
        "is_nearby": is_nearby
    }