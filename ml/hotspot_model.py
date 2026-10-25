"""
Unsupervised DBSCAN-based hotspot model for crime data.

This module provides a reusable sklearn-compatible wrapper for
spatial hotspot detection using DBSCAN clustering on latitude/
longitude coordinates with Haversine distance.

Design rules:
    * Independent of Flask and the production database.
    * Accepts coordinate arrays directly.
    * Validates coordinate ranges.
    * Treats DBSCAN noise label (-1) correctly.
    * Returns deterministic results when random_state is fixed.
    * Does NOT claim to predict future crime.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
from sklearn.cluster import DBSCAN


def _validate_coordinate(latitude: Any, longitude: Any) -> Optional[Tuple[float, float]]:
    """
    Validate a single latitude/longitude pair.

    Returns a (lat, lon) tuple if valid, or None if invalid/missing.
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


def _filter_valid_coordinates(
    coordinates: Sequence[Tuple[Any, Any]]
) -> List[Tuple[float, float]]:
    """
    Return only coordinates that pass range validation.

    Parameters
    ----------
    coordinates : sequence of (latitude, longitude) pairs.

    Returns
    -------
    list of valid (float, float) tuples.
    """
    valid = []

    for lat, lon in coordinates:
        result = _validate_coordinate(lat, lon)

        if result is not None:
            valid.append(result)

    return valid


def _compute_centroid(coordinates_rad: np.ndarray) -> Tuple[float, float]:
    """
    Compute the geographic centroid of a cluster.

    Parameters
    ----------
    coordinates_rad : np.ndarray of shape (n_points, 2)
        Coordinates expressed in radians.

    Returns
    -------
    (centroid_latitude, centroid_longitude) in degrees.
    """
    mean_lat_rad = np.mean(coordinates_rad[:, 0])
    mean_lon_rad = np.mean(coordinates_rad[:, 1])

    centroid_latitude = math.degrees(mean_lat_rad)
    centroid_longitude = math.degrees(mean_lon_rad)

    return (centroid_latitude, centroid_longitude)


class HotspotModel:
    """
    Reusable DBSCAN hotspot detector for geographic crime data.

    Public API
    ----------
    fit(coordinates)
        Fit DBSCAN on valid coordinates. Returns self.
    fit_predict(coordinates)
        Fit and return cluster labels for each input coordinate.
    get_clusters()
        Return cluster metadata computed during fit.
    get_cluster_summary(...)
        Return a list of hotspot summary dicts.

    Example
    -------
    >>> model = HotspotModel()
    >>> coords = [(13.0, 79.0), (13.01, 79.01), (13.02, 79.02)]
    >>> model.fit(coords)
    >>> clusters = model.get_clusters()
    """

    def __init__(
        self,
        eps_km: float = 1.0,
        min_samples: int = 2,
        random_state: Optional[int] = None,
    ) -> None:
        """
        Parameters
        ----------
        eps_km : float
            Neighborhood radius in kilometres.
        min_samples : int
            Minimum samples per cluster.
        random_state : int or None
            For reproducibility.
        """
        self.eps_km = float(eps_km)
        self.min_samples = int(min_samples)
        self.random_state = random_state

        self._clusters: Optional[List[Dict[str, Any]]] = None
        self._labels: Optional[np.ndarray] = None
        self._valid_coordinates: Optional[List[Tuple[float, float]]] = None
        self._fitted: bool = False

    def _build_dbscan(self) -> DBSCAN:
        """
        Construct a DBSCAN instance with Haversine metric.

        eps must be expressed in radians for the Haversine metric.
        """
        earth_radius_km = 6371.0
        eps_rad = self.eps_km / earth_radius_km

        return DBSCAN(
            eps=eps_rad,
            min_samples=self.min_samples,
            metric="haversine",
            algorithm="ball_tree",
        )

    def fit(
        self,
        coordinates: Sequence[Tuple[Any, Any]]
    ) -> "HotspotModel":
        """
        Fit DBSCAN on the provided coordinates.

        Parameters
        ----------
        coordinates : sequence of (latitude, longitude) pairs.
            Each pair may be numeric or string values that can be
            converted to float.

        Returns
        -------
        self
        """
        valid = _filter_valid_coordinates(coordinates)

        if not valid:
            self._valid_coordinates = []
            self._labels = np.array([], dtype=int)
            self._clusters = []
            self._fitted = True
            return self

        self._valid_coordinates = valid

        coords_rad = np.radians(np.array(valid))

        dbscan = self._build_dbscan()
        labels = dbscan.fit_predict(coords_rad)

        self._labels = labels
        self._fitted = True

        self._clusters = self._build_clusters(labels, coords_rad)

        return self

    def fit_predict(
        self,
        coordinates: Sequence[Tuple[Any, Any]]
    ) -> np.ndarray:
        """
        Fit the model and return cluster labels.

        Returns
        -------
        np.ndarray of shape (n_coordinates,)
            Cluster labels, where -1 indicates noise.
        """
        self.fit(coordinates)

        if self._labels is None:
            return np.array([], dtype=int)

        return self._labels

    def get_clusters(self) -> List[Dict[str, Any]]:
        """
        Return cluster metadata computed during fit.

        Returns
        -------
        list of dicts, each containing:
            cluster_id : int
            crime_count : int
            centroid_latitude : float
            centroid_longitude : float
            noise : bool
            member_indices : list[int]
        """
        if not self._fitted:
            raise RuntimeError("fit() must be called before get_clusters()")

        return list(self._clusters or [])

    def get_cluster_summary(
        self,
        records: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Return a list of hotspot summary dicts.

        Parameters
        ----------
        records : list of dict, optional
            Original crime records used for fit. When provided,
            each cluster summary includes descriptive statistics
            drawn from these records (dominant crime type, etc.).

        Returns
        -------
        list of dict
        """
        clusters = self.get_clusters()

        if not clusters:
            return []

        if records is None:
            return [
                {
                    "cluster_id": c["cluster_id"],
                    "crime_count": c["crime_count"],
                    "centroid_latitude": c["centroid_latitude"],
                    "centroid_longitude": c["centroid_longitude"],
                    "noise": c["noise"],
                }
                for c in clusters
            ]

        summaries = []

        for cluster in clusters:
            member_indices = cluster.get("member_indices", [])

            if not member_indices:
                continue

            member_records = [records[i] for i in member_indices if i < len(records)]

            crime_types = [
                r.get("crime_type")
                for r in member_records
                if r.get("crime_type")
            ]

            dominant_crime_type = None
            if crime_types:
                dominant_crime_type = max(
                    sorted(set(crime_types)),
                    key=crime_types.count,
                )

            severity_scores = [
                r.get("severity_score")
                for r in member_records
                if r.get("severity_score") is not None
            ]

            avg_severity = None
            if severity_scores:
                avg_severity = round(sum(severity_scores) / len(severity_scores), 2)

            risk_levels = [
                r.get("risk_level")
                for r in member_records
                if r.get("risk_level")
            ]

            dominant_risk = None
            if risk_levels:
                dominant_risk = max(
                    sorted(set(risk_levels)),
                    key=risk_levels.count,
                )

            locations = [
                r.get("location_name")
                for r in member_records
                if r.get("location_name")
            ]

            dominant_location = None
            if locations:
                dominant_location = max(
                    sorted(set(locations)),
                    key=locations.count,
                )

            summaries.append({
                "cluster_id": cluster["cluster_id"],
                "crime_count": cluster["crime_count"],
                "centroid_latitude": cluster["centroid_latitude"],
                "centroid_longitude": cluster["centroid_longitude"],
                "noise": cluster["noise"],
                "dominant_crime_type": dominant_crime_type,
                "avg_severity_score": avg_severity,
                "dominant_risk_level": dominant_risk,
                "dominant_location": dominant_location,
            })

        return summaries

    def _build_clusters(
        self,
        labels: np.ndarray,
        coords_rad: np.ndarray,
    ) -> List[Dict[str, Any]]:
        """
        Build cluster metadata from DBSCAN labels.

        Parameters
        ----------
        labels : np.ndarray
            DBSCAN cluster labels.
        coords_rad : np.ndarray
            Coordinates in radians.

        Returns
        -------
        list of cluster dicts.
        """
        clusters: Dict[int, List[int]] = {}

        for index, label in enumerate(labels):
            clusters.setdefault(int(label), []).append(index)

        result = []

        for label, member_indices in clusters.items():
            member_coords_rad = coords_rad[member_indices]
            centroid_lat, centroid_lon = _compute_centroid(member_coords_rad)

            result.append({
                "cluster_id": int(label),
                "crime_count": len(member_indices),
                "centroid_latitude": round(centroid_lat, 6),
                "centroid_longitude": round(centroid_lon, 6),
                "noise": bool(label == -1),
                "member_indices": member_indices,
            })

        return result

    def noise_count(self) -> int:
        """Return the number of noise points (-1 label)."""
        if self._labels is None:
            return 0
        return int(np.sum(self._labels == -1))

    def valid_count(self) -> int:
        """Return the number of valid coordinates processed."""
        if self._valid_coordinates is None:
            return 0
        return len(self._valid_coordinates)
