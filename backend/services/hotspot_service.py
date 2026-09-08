import math

from sklearn.cluster import DBSCAN
import numpy as np

from config.config import (
    DBSCAN_EPS_KM,
    DBSCAN_MIN_SAMPLES,
    EARTH_RADIUS_KM,
)


def _km_to_radians(kilometers):
    """Convert a distance in kilometres to radians for the Haversine metric."""
    return kilometers / EARTH_RADIUS_KM


def _filter_valid_coordinates(crimes):
    """
    Return only records that carry a valid geographic coordinate.

    Records with missing or non-numeric latitude/longitude are
    silently dropped so the clustering step never sees bad data.
    """
    valid = []

    for crime in crimes:

        try:

            latitude = float(crime["latitude"])

            longitude = float(crime["longitude"])

        except (
            TypeError,
            ValueError,
            KeyError
        ):
            continue

        if not -90.0 <= latitude <= 90.0:
            continue

        if not -180.0 <= longitude <= 180.0:
            continue

        valid.append(
            {
                "latitude": latitude,
                "longitude": longitude,
                "location_name": (
                    crime.get("location_name") or "Unknown"
                ),
            }
        )

    return valid


def _compute_cluster_centroid(coordinates_rad):
    """
    Compute the geographic centroid of a cluster as the mean
    of its member coordinates (expressed in radians and then
    converted back to degrees).
    """
    mean_lat_rad = np.mean(coordinates_rad[:, 0])
    mean_lon_rad = np.mean(coordinates_rad[:, 1])

    centroid_latitude = math.degrees(mean_lat_rad)
    centroid_longitude = math.degrees(mean_lon_rad)

    return centroid_latitude, centroid_longitude


def _risk_level(crime_count):
    """
    Map a cluster crime count to the project's risk terminology.
    """
    if crime_count >= 5:
        return "High"

    if crime_count >= 3:
        return "Medium"

    return "Low"


def analyze_hotspots(crimes):
    """
    Detect crime hotspots using DBSCAN clustering on geographic
    coordinates.

    Why Haversine?
        Crime coordinates are expressed as latitude/longitude on
        the surface of the Earth.  Euclidean distance on raw
        degree values is not meaningful because a degree of
        longitude represents a shorter physical distance near the
        poles than near the equator.  The Haversine formula
        computes the great-circle distance between two points on
        a sphere, which is the standard approach for geographic
        clustering.

    DBSCAN parameters:
        eps        -- neighbourhood radius in kilometres.  Two
                      crimes are considered neighbours if they
                      lie within this Haversine distance.
        min_samples-- minimum number of crimes required to form
                      a dense region (cluster).  Isolated points
                      are labelled as noise (-1) and are NOT
                      returned as hotspots.

    Returns a list of hotspot dicts sorted by crime_count
    descending, or an empty list when no valid coordinates
    are available.
    """
    if not crimes:
        return []

    valid_crimes = _filter_valid_coordinates(crimes)

    if not valid_crimes:
        return []

    coordinates_rad = np.radians(
        np.array(
            [
                [c["latitude"], c["longitude"]]
                for c in valid_crimes
            ]
        )
    )

    eps_rad = _km_to_radians(DBSCAN_EPS_KM)

    clustering = DBSCAN(
        eps=eps_rad,
        min_samples=DBSCAN_MIN_SAMPLES,
        metric="haversine",
        algorithm="ball_tree",
    ).fit(coordinates_rad)

    labels = clustering.labels_

    clusters = {}

    for index, label in enumerate(labels):

        if label == -1:
            continue

        clusters.setdefault(label, []).append(index)

    hotspots = []

    for label, member_indices in clusters.items():

        member_coords = coordinates_rad[member_indices]

        centroid_lat, centroid_lon = (
            _compute_cluster_centroid(member_coords)
        )

        crime_count = len(member_indices)

        location_names = [
            valid_crimes[i].get(
                "location_name",
                valid_crimes[i].get("location", "Unknown"),
            )
            for i in member_indices
        ]

        primary_location = max(
            set(location_names),
            key=location_names.count,
        )

        hotspots.append(
            {
                "cluster_id": int(label),
                "location": primary_location,
                "crime_count": crime_count,
                "centroid_latitude": round(
                    centroid_lat, 6
                ),
                "centroid_longitude": round(
                    centroid_lon, 6
                ),
                "risk_level": _risk_level(crime_count),
            }
        )

    hotspots.sort(
        key=lambda hotspot: hotspot["crime_count"],
        reverse=True,
    )

    return hotspots
