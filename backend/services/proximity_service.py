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
        hotspot_latitude,
        hotspot_longitude
    )

    is_nearby = distance <= alert_radius

    return {
        "distance_meters": distance,
        "alert_radius_meters": alert_radius,
        "is_nearby": is_nearby
    }


def calculate_distance_km(
    latitude_1,
    longitude_1,
    latitude_2,
    longitude_2
):
    """
    Distance between two coordinates in kilometers.
    """

    distance_meters = calculate_distance(
        latitude_1,
        longitude_1,
        latitude_2,
        longitude_2
    )

    return round(distance_meters / 1000, 3)


def find_nearby_crimes(
    crimes,
    latitude,
    longitude,
    radius_km
):
    """
    Filter crime records to those located within
    radius_km of the given coordinates.

    Every returned record carries its real
    calculated distance in "distance_km" and the
    result is sorted from nearest to farthest.
    """

    nearby_crimes = []

    for crime in crimes:

        try:

            crime_latitude = float(
                crime["latitude"]
            )

            crime_longitude = float(
                crime["longitude"]
            )

        except (
            KeyError,
            TypeError,
            ValueError
        ):

            # Skip records without usable coordinates.
            continue

        distance_km = calculate_distance_km(
            latitude,
            longitude,
            crime_latitude,
            crime_longitude
        )

        if distance_km <= radius_km:

            nearby_crime = dict(crime)

            nearby_crime[
                "distance_km"
            ] = distance_km

            nearby_crimes.append(
                nearby_crime
            )

    nearby_crimes.sort(
        key=lambda crime: crime[
            "distance_km"
        ]
    )

    return nearby_crimes


def find_nearest_hotspot(
    hotspots,
    latitude,
    longitude
):
    """
    Return the hotspot closest to the given
    coordinates, or None when no hotspots exist.
    """

    nearest_hotspot = None
    nearest_distance = None

    for hotspot in hotspots:

        distance_meters = calculate_distance(
            latitude,
            longitude,
            hotspot.get(
                "average_latitude",
                0
            ),
            hotspot.get(
                "average_longitude",
                0
            )
        )

        if (
            nearest_distance is None
            or distance_meters < nearest_distance
        ):

            nearest_distance = distance_meters

            nearest_hotspot = hotspot

    return nearest_hotspot
