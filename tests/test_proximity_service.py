"""
Tests for backend/services/proximity_service.py.

Uses small synthetic coordinates. Does not touch the production
database.
"""

from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest

from services.proximity_service import (
    calculate_distance,
    calculate_distance_km,
    check_proximity,
    find_nearby_crimes,
    find_nearest_hotspot,
    find_nearby_hotspots,
    _validate_coordinate,
)


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #


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


# ------------------------------------------------------------------ #
# Unit tests for distance calculations
# ------------------------------------------------------------------ #


class TestCalculateDistance:
    def test_same_coordinate_distance_zero(self):
        dist = calculate_distance(13.0, 79.0, 13.0, 79.0)
        assert dist == 0.0

    def test_nearby_coordinates(self):
        dist = calculate_distance(13.0, 79.0, 13.01, 79.01)
        assert dist is not None
        assert 1000 < dist < 2000

    def test_distant_coordinates(self):
        dist = calculate_distance(13.0, 79.0, 14.0, 80.0)
        assert dist is not None
        assert dist > 100000

    def test_invalid_coordinate_returns_none(self):
        dist = calculate_distance(999.0, 79.0, 13.0, 79.0)
        assert dist is None

    def test_none_coordinate_returns_none(self):
        dist = calculate_distance(None, None, 13.0, 79.0)
        assert dist is None

    def test_non_numeric_returns_none(self):
        dist = calculate_distance("abc", 79.0, 13.0, 79.0)
        assert dist is None


class TestCalculateDistanceKm:
    def test_same_coordinate(self):
        dist = calculate_distance_km(13.0, 79.0, 13.0, 79.0)
        assert dist == 0.0

    def test_nearby_coordinates(self):
        dist = calculate_distance_km(13.0, 79.0, 13.01, 79.01)
        assert dist is not None
        assert 1.0 < dist < 2.0

    def test_invalid_returns_none(self):
        dist = calculate_distance_km(999.0, 79.0, 13.0, 79.0)
        assert dist is None


class TestCheckProximity:
    def test_nearby_returns_true(self):
        result = check_proximity(13.0, 79.0, 13.001, 79.001, alert_radius=5000)
        assert result["is_nearby"] is True
        assert result["alert_radius_meters"] == 5000

    def test_far_returns_false(self):
        result = check_proximity(13.0, 79.0, 14.0, 80.0, alert_radius=500)
        assert result["is_nearby"] is False

    def test_same_location_is_nearby(self):
        result = check_proximity(13.0, 79.0, 13.0, 79.0, alert_radius=100)
        assert result["is_nearby"] is True
        assert result["distance_meters"] == 0.0


# ------------------------------------------------------------------ #
# Unit tests for find_nearby_crimes
# ------------------------------------------------------------------ #


class TestFindNearbyCrimes:
    def test_filters_by_radius(self):
        crimes = [
            {"id": 1, "latitude": 13.0, "longitude": 79.0},
            {"id": 2, "latitude": 14.0, "longitude": 80.0},
        ]
        nearby = find_nearby_crimes(crimes, 13.0, 79.0, radius_km=10.0)
        assert len(nearby) == 1
        assert nearby[0]["id"] == 1

    def test_sorted_by_distance(self):
        crimes = [
            {"id": 1, "latitude": 13.01, "longitude": 79.01},
            {"id": 2, "latitude": 13.0, "longitude": 79.0},
            {"id": 3, "latitude": 13.02, "longitude": 79.02},
        ]
        nearby = find_nearby_crimes(crimes, 13.0, 79.0, radius_km=10.0)
        assert len(nearby) == 3
        assert nearby[0]["id"] == 2
        assert nearby[1]["id"] == 1
        assert nearby[2]["id"] == 3

    def test_missing_coordinates_ignored(self):
        crimes = [
            {"id": 1, "latitude": None, "longitude": 79.0},
            {"id": 2, "latitude": 13.0, "longitude": 79.0},
        ]
        nearby = find_nearby_crimes(crimes, 13.0, 79.0, radius_km=10.0)
        assert len(nearby) == 1
        assert nearby[0]["id"] == 2

    def test_invalid_coordinates_ignored(self):
        crimes = [
            {"id": 1, "latitude": 999.0, "longitude": 79.0},
            {"id": 2, "latitude": 13.0, "longitude": 79.0},
        ]
        nearby = find_nearby_crimes(crimes, 13.0, 79.0, radius_km=10.0)
        assert len(nearby) == 1

    def test_no_nearby_returns_empty(self):
        crimes = [
            {"id": 1, "latitude": 14.0, "longitude": 80.0},
        ]
        nearby = find_nearby_crimes(crimes, 13.0, 79.0, radius_km=1.0)
        assert nearby == []

    def test_empty_crimes_returns_empty(self):
        nearby = find_nearby_crimes([], 13.0, 79.0, radius_km=10.0)
        assert nearby == []

    def test_limit_applied(self):
        crimes = [
            {"id": i, "latitude": 13.0 + i * 0.001, "longitude": 79.0 + i * 0.001}
            for i in range(10)
        ]
        nearby = find_nearby_crimes(crimes, 13.0, 79.0, radius_km=10.0, limit=3)
        assert len(nearby) == 3

    def test_distance_km_added(self):
        crimes = [
            {"id": 1, "latitude": 13.0, "longitude": 79.0},
        ]
        nearby = find_nearby_crimes(crimes, 13.0, 79.0, radius_km=10.0)
        assert "distance_km" in nearby[0]
        assert nearby[0]["distance_km"] == 0.0

    def test_zero_radius_returns_empty(self):
        crimes = [
            {"id": 1, "latitude": 13.0, "longitude": 79.0},
        ]
        nearby = find_nearby_crimes(crimes, 13.0, 79.0, radius_km=0.0)
        assert nearby == []

    def test_negative_radius_returns_empty(self):
        crimes = [
            {"id": 1, "latitude": 13.0, "longitude": 79.0},
        ]
        nearby = find_nearby_crimes(crimes, 13.0, 79.0, radius_km=-1.0)
        assert nearby == []


# ------------------------------------------------------------------ #
# Unit tests for find_nearest_hotspot
# ------------------------------------------------------------------ #


class TestFindNearestHotspot:
    def test_returns_nearest(self):
        hotspots = [
            {"centroid_latitude": 13.0, "centroid_longitude": 79.0, "crime_count": 1},
            {"centroid_latitude": 13.01, "centroid_longitude": 79.01, "crime_count": 2},
        ]
        nearest = find_nearest_hotspot(hotspots, 13.0, 79.0)
        assert nearest["crime_count"] == 1

    def test_empty_hotspots_returns_none(self):
        nearest = find_nearest_hotspot([], 13.0, 79.0)
        assert nearest is None

    def test_invalid_user_coords_returns_none(self):
        hotspots = [
            {"centroid_latitude": 13.0, "centroid_longitude": 79.0},
        ]
        nearest = find_nearest_hotspot(hotspots, 999.0, 79.0)
        assert nearest is None

    def test_missing_centroid_keys_skipped(self):
        hotspots = [
            {"centroid_latitude": None, "centroid_longitude": 79.0},
            {"centroid_latitude": 13.0, "centroid_longitude": 79.0},
        ]
        nearest = find_nearest_hotspot(hotspots, 13.0, 79.0)
        assert nearest is not None
        assert nearest["centroid_latitude"] == 13.0


# ------------------------------------------------------------------ #
# Unit tests for find_nearby_hotspots
# ------------------------------------------------------------------ #


class TestFindNearbyHotspots:
    def test_filters_by_radius(self):
        hotspots = [
            {"centroid_latitude": 13.0, "centroid_longitude": 79.0, "crime_count": 5},
            {"centroid_latitude": 14.0, "centroid_longitude": 80.0, "crime_count": 3},
        ]
        nearby = find_nearby_hotspots(hotspots, 13.0, 79.0, radius_km=10.0)
        assert len(nearby) == 1
        assert nearby[0]["crime_count"] == 5

    def test_sorted_by_distance(self):
        hotspots = [
            {"centroid_latitude": 13.01, "centroid_longitude": 79.01, "crime_count": 1},
            {"centroid_latitude": 13.0, "centroid_longitude": 79.0, "crime_count": 2},
        ]
        nearby = find_nearby_hotspots(hotspots, 13.0, 79.0, radius_km=10.0)
        assert nearby[0]["crime_count"] == 2
        assert nearby[1]["crime_count"] == 1

    def test_invalid_coords_returns_empty(self):
        nearby = find_nearby_hotspots([], 999.0, 79.0, radius_km=10.0)
        assert nearby == []

    def test_limit_applied(self):
        hotspots = [
            {"centroid_latitude": 13.0 + i * 0.01, "centroid_longitude": 79.0 + i * 0.01, "crime_count": i}
            for i in range(10)
        ]
        nearby = find_nearby_hotspots(hotspots, 13.0, 79.0, radius_km=50.0, limit=3)
        assert len(nearby) == 3

    def test_distance_km_added(self):
        hotspots = [
            {"centroid_latitude": 13.0, "centroid_longitude": 79.0},
        ]
        nearby = find_nearby_hotspots(hotspots, 13.0, 79.0, radius_km=10.0)
        assert "distance_km" in nearby[0]
        assert nearby[0]["distance_km"] == 0.0
