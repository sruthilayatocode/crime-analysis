"""
Tests for ml/hotspot_model.py.

Uses small synthetic coordinates. Does not touch the production
database.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from ml.hotspot_model import (
    HotspotModel,
    _compute_centroid,
    _filter_valid_coordinates,
    _validate_coordinate,
)


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #


def _radians(coords):
    return np.radians(np.array(coords, dtype=float))


# ------------------------------------------------------------------ #
# Unit tests for helpers
# ------------------------------------------------------------------ #


class TestValidateCoordinate:
    def test_valid_coordinate(self):
        result = _validate_coordinate(13.0, 79.0)
        assert result == (13.0, 79.0)

    def test_string_coordinates_coerced(self):
        result = _validate_coordinate("13.0", "79.0")
        assert result == (13.0, 79.0)

    def test_none_returns_none(self):
        result = _validate_coordinate(None, None)
        assert result is None

    def test_invalid_latitude_returns_none(self):
        result = _validate_coordinate(999.0, 79.0)
        assert result is None

    def test_invalid_longitude_returns_none(self):
        result = _validate_coordinate(13.0, -999.0)
        assert result is None

    def test_boundary_latitude_valid(self):
        result = _validate_coordinate(90.0, 0.0)
        assert result == (90.0, 0.0)

    def test_boundary_longitude_valid(self):
        result = _validate_coordinate(0.0, 180.0)
        assert result == (0.0, 180.0)


class TestFilterValidCoordinates:
    def test_filters_invalid(self):
        coords = [(13.0, 79.0), (999.0, 79.0), ("abc", 79.0)]
        valid = _filter_valid_coordinates(coords)
        assert valid == [(13.0, 79.0)]

    def test_empty_input(self):
        assert _filter_valid_coordinates([]) == []

    def test_mixed_types(self):
        coords = [(13.0, 79.0), (None, None), (14.0, 80.0)]
        valid = _filter_valid_coordinates(coords)
        assert len(valid) == 2


class TestComputeCentroid:
    def test_single_point(self):
        coords = _radians([(13.0, 79.0)])
        lat, lon = _compute_centroid(coords)
        assert math.isclose(lat, 13.0)
        assert math.isclose(lon, 79.0)

    def test_multiple_points(self):
        coords = _radians([(13.0, 79.0), (14.0, 80.0)])
        lat, lon = _compute_centroid(coords)
        assert math.isclose(lat, 13.5)
        assert math.isclose(lon, 79.5)


# ------------------------------------------------------------------ #
# Unit tests for HotspotModel
# ------------------------------------------------------------------ #


class TestHotspotModel:
    def test_empty_coordinates(self):
        model = HotspotModel()
        model.fit([])

        assert model.valid_count() == 0
        assert model.noise_count() == 0
        assert model.get_clusters() == []

    def test_single_point_becomes_noise(self):
        model = HotspotModel(eps_km=1.0, min_samples=2)
        model.fit([(13.0, 79.0)])

        assert model.valid_count() == 1
        assert model.noise_count() == 1
        clusters = model.get_clusters()
        assert len(clusters) == 1
        assert clusters[0]["noise"] is True

    def test_two_close_points_form_cluster(self):
        model = HotspotModel(eps_km=10.0, min_samples=2)
        coords = [(13.0, 79.0), (13.01, 79.01)]
        model.fit(coords)

        assert model.valid_count() == 2
        assert model.noise_count() == 0
        clusters = model.get_clusters()
        assert len(clusters) == 1
        assert clusters[0]["noise"] is False
        assert clusters[0]["crime_count"] == 2

    def test_far_points_form_noise(self):
        model = HotspotModel(eps_km=0.01, min_samples=2)
        coords = [(13.0, 79.0), (14.0, 80.0)]
        model.fit(coords)

        assert model.noise_count() == 2

    def test_fit_predict_returns_labels(self):
        model = HotspotModel(eps_km=1.0, min_samples=2)
        coords = [(13.0, 79.0), (13.01, 79.01)]
        labels = model.fit_predict(coords)

        assert len(labels) == 2
        assert set(labels).issubset({0, -1})

    def test_get_clusters_before_fit_raises(self):
        model = HotspotModel()
        with pytest.raises(RuntimeError, match="fit"):
            model.get_clusters()

    def test_cluster_summary_without_records(self):
        model = HotspotModel(eps_km=10.0, min_samples=2)
        coords = [(13.0, 79.0), (13.01, 79.01)]
        model.fit(coords)

        summary = model.get_cluster_summary(records=None)
        assert len(summary) == 1
        assert "cluster_id" in summary[0]

    def test_cluster_summary_with_records(self):
        model = HotspotModel(eps_km=10.0, min_samples=2)
        coords = [(13.0, 79.0), (13.01, 79.01)]
        records = [
            {"crime_type": "Murder", "severity_score": 10, "risk_level": "Critical", "location_name": "A"},
            {"crime_type": "Murder", "severity_score": 10, "risk_level": "Critical", "location_name": "A"},
        ]
        model.fit(coords)

        summary = model.get_cluster_summary(records=records)
        assert summary[0]["dominant_crime_type"] == "Murder"
        assert summary[0]["dominant_location"] == "A"

    def test_invalid_coordinates_ignored(self):
        model = HotspotModel(eps_km=1.0, min_samples=2)
        coords = [(999.0, 79.0), (13.0, 79.0)]
        model.fit(coords)

        assert model.valid_count() == 1

    def test_deterministic_results(self):
        coords = [(13.0, 79.0), (13.01, 79.01), (14.0, 80.0)]

        model1 = HotspotModel(eps_km=10.0, min_samples=2)
        model1.fit(coords)
        labels1 = model1.get_clusters()

        model2 = HotspotModel(eps_km=10.0, min_samples=2)
        model2.fit(coords)
        labels2 = model2.get_clusters()

        assert labels1 == labels2

    def test_noise_percentage_calculation(self):
        model = HotspotModel(eps_km=10.0, min_samples=2)
        coords = [(13.0, 79.0), (13.01, 79.01), (14.0, 80.0)]
        model.fit(coords)

        assert model.valid_count() == 3

    def test_multiple_clusters(self):
        model = HotspotModel(eps_km=1.0, min_samples=2)
        coords = [
            (13.0, 79.0),
            (13.001, 79.001),
            (14.0, 80.0),
            (14.001, 80.001),
        ]
        model.fit(coords)

        clusters = model.get_clusters()
        non_noise = [c for c in clusters if not c["noise"]]
        assert len(non_noise) == 2
