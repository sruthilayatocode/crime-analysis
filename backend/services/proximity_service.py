from math import radians, sin, cos, sqrt, atan2


# Earth radius in kilometres.
EARTH_RADIUS_KM = 6371.0


def _validate_coordinate(latitude, longitude):
    """
    Validate a latitude/longitude pair.

    Returns (lat, lon) as floats if valid, or None if invalid/missing.
    """
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (TypeError, ValueError):
        return None

    if not (-90.0 <= lat <= 90.0):
        return None

    if not (-180.0 <= lon <= 180.0):
        return None

    return (lat, lon)


def calculate_distance(
    latitude_1,
    longitude_1,
    latitude_2,
    longitude_2
):
    """
    Calculate the distance between two GPS coordinates
    using the Haversine formula.

    The returned distance is in metres.
    """

    coord1 = _validate_coordinate(latitude_1, longitude_1)
    coord2 = _validate_coordinate(latitude_2, longitude_2)

    if coord1 is None or coord2 is None:
        return None

    lat1, lon1 = coord1
    lat2, lon2 = coord2

    latitude_difference = radians(
        lat2 - lat1
    )

    longitude_difference = radians(
        lon2 - lon1
    )

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

    distance = EARTH_RADIUS_KM * c * 1000

    return round(distance, 2)


def calculate_distance_km(
    latitude_1,
    longitude_1,
    latitude_2,
    longitude_2
):
    """
    Distance between two coordinates in kilometres.

    Returns None if coordinates are invalid.
    """
    distance_meters = calculate_distance(
        latitude_1,
        longitude_1,
        latitude_2,
        longitude_2
    )

    if distance_meters is None:
        return None

    return round(distance_meters / 1000, 3)


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

    alert_radius is in metres.
    """

    distance = calculate_distance(
        user_latitude,
        user_longitude,
        hotspot_latitude,
        hotspot_longitude
    )

    if distance is None:
        return {
            "distance_meters": None,
            "alert_radius_meters": alert_radius,
            "is_nearby": False,
        }

    is_nearby = distance <= alert_radius

    return {
        "distance_meters": distance,
        "alert_radius_meters": alert_radius,
        "is_nearby": is_nearby
    }


def find_nearby_crimes(
    crimes,
    latitude,
    longitude,
    radius_km,
    limit=None
):
    """
    Filter crime records to those located within
    radius_km of the given coordinates.

    Every returned record carries its real
    calculated distance in "distance_km" and the
    result is sorted from nearest to farthest.

    Parameters
    ----------
    crimes : list of dict
        Crime records.
    latitude : float
        User latitude.
    longitude : float
        User longitude.
    radius_km : float
        Search radius in kilometres.
    limit : int or None
        Maximum number of results to return.

    Returns
    -------
    list of dict
    """
    if radius_km is None or radius_km <= 0:
        return []

    nearby_crimes = []

    for crime in crimes:

        crime_latitude = crime.get("latitude")
        crime_longitude = crime.get("longitude")

        if crime_latitude is None or crime_longitude is None:
            continue

        distance_km = calculate_distance_km(
            latitude,
            longitude,
            crime_latitude,
            crime_longitude
        )

        if distance_km is None:
            continue

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

    if limit is not None and limit > 0:
        nearby_crimes = nearby_crimes[:limit]

    return nearby_crimes


def find_nearest_hotspot(
    hotspots,
    latitude,
    longitude
):
    """
    Return the hotspot closest to the given
    coordinates, or None when no hotspots exist.

    Uses the correct centroid keys from hotspot_service.py
    and ml/hotspot_model.py.
    """

    coord = _validate_coordinate(latitude, longitude)

    if coord is None:
        return None

    nearest_hotspot = None
    nearest_distance = None

    for hotspot in hotspots:

        hotspot_lat = hotspot.get("centroid_latitude")
        hotspot_lon = hotspot.get("centroid_longitude")

        if hotspot_lat is None or hotspot_lon is None:
            continue

        distance_meters = calculate_distance(
            latitude,
            longitude,
            hotspot_lat,
            hotspot_lon
        )

        if distance_meters is None:
            continue

        if (
            nearest_distance is None
            or distance_meters < nearest_distance
        ):

            nearest_distance = distance_meters
            nearest_hotspot = hotspot

    return nearest_hotspot


def find_nearby_hotspots(
    hotspots,
    latitude,
    longitude,
    radius_km,
    limit=None
):
    """
    Filter hotspots to those within radius_km of the given coordinates.

    Parameters
    ----------
    hotspots : list of dict
        Hotspot dicts with centroid_latitude / centroid_longitude.
    latitude : float
        User latitude.
    longitude : float
        User longitude.
    radius_km : float
        Search radius in kilometres.
    limit : int or None
        Maximum number of results.

    Returns
    -------
    list of dict, sorted by distance ascending.
    """
    if radius_km is None or radius_km <= 0:
        return []

    coord = _validate_coordinate(latitude, longitude)

    if coord is None:
        return []

    nearby = []

    for hotspot in hotspots:
        hotspot_lat = hotspot.get("centroid_latitude")
        hotspot_lon = hotspot.get("centroid_longitude")

        if hotspot_lat is None or hotspot_lon is None:
            continue

        distance_km = calculate_distance_km(
            latitude,
            longitude,
            hotspot_lat,
            hotspot_lon
        )

        if distance_km is None:
            continue

        if distance_km <= radius_km:
            entry = dict(hotspot)
            entry["distance_km"] = distance_km
            nearby.append(entry)

    nearby.sort(key=lambda h: h["distance_km"])

    if limit is not None and limit > 0:
        nearby = nearby[:limit]

    return nearby
