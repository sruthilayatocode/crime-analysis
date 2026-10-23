"""
test_zone_service.py
====================
Unit tests for the CrimeSense Zone Risk Analysis Service and GET /api/zone endpoint.

Covers:
- Haversine distance and bounding box calculations
- Distance decay and recency weighting
- Zone classification and boundary scores (< 30, 30-59, >= 60)
- Edge cases (zero incidents, empty areas, cap at 100, tied severity)
- Known coordinates (Katpadi, Sathuvachari)
- Flask API endpoint integration and parameter validation
"""

import os
import sys
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from zone_config import ZONE_THRESHOLDS, RECENCY_CONFIG, SAFETY_TIPS, LIMITED_DATA_NOTE
from services.zone_service import (
    haversine_distance_meters,
    get_bounding_box,
    calculate_recency_weight,
    classify_zone,
    calculate_zone_risk,
)
from app import app


class TestZoneServiceUnit(unittest.TestCase):
    """Unit tests for core zone_service algorithms and calculations."""

    def test_haversine_distance(self):
        """Haversine distance should be 0 for identical points and accurate for known distances."""
        # Same point
        dist_zero = haversine_distance_meters(12.9806, 79.1368, 12.9806, 79.1368)
        self.assertAlmostEqual(dist_zero, 0.0, places=3)

        # 1 degree of latitude is approximately 111,195 meters (~111.2 km)
        dist_1deg = haversine_distance_meters(12.0, 79.0, 13.0, 79.0)
        self.assertTrue(110000 <= dist_1deg <= 112000)

    def test_bounding_box(self):
        """Bounding box must encompass the query radius."""
        lat, lng, radius = 12.9806, 79.1368, 1000.0
        bbox = get_bounding_box(lat, lng, radius)

        self.assertLess(bbox["min_lat"], lat)
        self.assertGreater(bbox["max_lat"], lat)
        self.assertLess(bbox["min_lng"], lng)
        self.assertGreater(bbox["max_lng"], lng)

        # Confirm that a point at exactly 1000m north is within bbox lat range
        # (1000m north is ~ lat + 1000/111139 = lat + 0.00899)
        self.assertGreater(bbox["max_lat"], lat + 0.00899)

    def test_recency_weighting(self):
        """Recency weights must fall into < 6 months, 6-24 months, and > 24 months brackets."""
        ref_time = datetime(2026, 10, 1, tzinfo=timezone.utc)

        # Newer than 6 months (e.g. 60 days old) -> 1.0
        date_new = ref_time - timedelta(days=60)
        weight, _ = calculate_recency_weight(date_new, reference_time=ref_time)
        self.assertEqual(weight, 1.0)

        # 6 to 24 months (e.g. 300 days old) -> 0.7
        date_mid = ref_time - timedelta(days=300)
        weight, _ = calculate_recency_weight(date_mid, reference_time=ref_time)
        self.assertEqual(weight, 0.7)

        # Older than 24 months (e.g. 800 days old) -> 0.4
        date_old = ref_time - timedelta(days=800)
        weight, _ = calculate_recency_weight(date_old, reference_time=ref_time)
        self.assertEqual(weight, 0.4)

        # Missing or invalid date -> default weight 0.4
        weight_none, _ = calculate_recency_weight(None, reference_time=ref_time)
        self.assertEqual(weight_none, RECENCY_CONFIG["DEFAULT_WEIGHT"])

        weight_invalid, _ = calculate_recency_weight("not-a-valid-date", reference_time=ref_time)
        self.assertEqual(weight_invalid, RECENCY_CONFIG["DEFAULT_WEIGHT"])

    def test_zone_boundary_scores(self):
        """Score boundary mapping: >= 60 RED, 30-59 YELLOW, < 30 GREEN."""
        self.assertEqual(classify_zone(0.0), "GREEN")
        self.assertEqual(classify_zone(15.5), "GREEN")
        self.assertEqual(classify_zone(29.9), "GREEN")

        # Boundary at 30.0
        self.assertEqual(classify_zone(30.0), "YELLOW")
        self.assertEqual(classify_zone(45.0), "YELLOW")
        self.assertEqual(classify_zone(59.9), "YELLOW")

        # Boundary at 60.0
        self.assertEqual(classify_zone(60.0), "RED")
        self.assertEqual(classify_zone(85.0), "RED")
        self.assertEqual(classify_zone(100.0), "RED")

    def test_zero_incidents_edge_case(self):
        """Zero incidents within radius must return GREEN with confidence 'low' and limited data note."""
        result = calculate_zone_risk(
            lat=15.0,
            lng=75.0,
            radius=1000.0,
            candidate_crimes=[],
        )

        self.assertEqual(result["zone"], "GREEN")
        self.assertEqual(result["score"], 0.0)
        self.assertEqual(result["incident_count"], 0)
        self.assertEqual(result["top_3_crime_types"], [])
        self.assertIsNone(result["nearest_incident_distance"])
        self.assertIsNone(result["most_severe_recent_incident"])
        self.assertEqual(result["confidence"], "low")
        self.assertIn("limited", result["note"].lower())
        self.assertEqual(result["safety_tip"], SAFETY_TIPS["GREEN_LOW_CONFIDENCE"])

    def test_single_incident_calculation(self):
        """Single incident: severity_score * distance_decay * recency_weight."""
        ref_time = datetime(2026, 10, 1, tzinfo=timezone.utc)
        # Incident at exact same coordinates (distance = 0m, decay = 1.0)
        # Date is 30 days old (recency = 1.0)
        # Severity = 10.0
        # Expected raw score = 10.0 * 1.0 * 1.0 = 10.0 (< 30 -> GREEN)
        crimes = [
            {
                "latitude": 12.9800,
                "longitude": 79.1300,
                "severity_score": 10.0,
                "published_date": (ref_time - timedelta(days=30)).isoformat(),
                "crime_type": "Theft",
                "title": "Recent Severe Theft",
                "url": "http://example.com/theft1",
            }
        ]

        result = calculate_zone_risk(
            lat=12.9800,
            lng=79.1300,
            radius=1000.0,
            reference_time=ref_time,
            candidate_crimes=crimes,
        )

        self.assertEqual(result["zone"], "GREEN")
        self.assertEqual(result["score"], 10.0)
        self.assertEqual(result["incident_count"], 1)
        self.assertEqual(result["top_3_crime_types"], ["Theft"])
        self.assertEqual(result["nearest_incident_distance"], 0.0)
        self.assertIsNotNone(result["most_severe_recent_incident"])
        self.assertEqual(result["most_severe_recent_incident"]["title"], "Recent Severe Theft")
        self.assertEqual(result["confidence"], "high")

    def test_boundary_score_yellow_and_red_transition(self):
        """Verify transitions to YELLOW (>= 30) and RED (>= 60) and cap at 100."""
        ref_time = datetime(2026, 10, 1, tzinfo=timezone.utc)

        # 3 incidents of severity 10 at 0m distance with recency 1.0 -> score = 30.0 (YELLOW)
        yellow_crimes = [
            {
                "latitude": 12.0,
                "longitude": 79.0,
                "severity_score": 10.0,
                "published_date": (ref_time - timedelta(days=10)).isoformat(),
                "crime_type": "Robbery",
                "title": f"Incident {i}",
                "url": f"http://example.com/{i}",
            }
            for i in range(3)
        ]

        res_yellow = calculate_zone_risk(
            lat=12.0,
            lng=79.0,
            radius=1000.0,
            reference_time=ref_time,
            candidate_crimes=yellow_crimes,
        )
        self.assertEqual(res_yellow["score"], 30.0)
        self.assertEqual(res_yellow["zone"], "YELLOW")

        # 6 incidents of severity 10 at 0m distance with recency 1.0 -> score = 60.0 (RED)
        red_crimes = [
            {
                "latitude": 12.0,
                "longitude": 79.0,
                "severity_score": 10.0,
                "published_date": (ref_time - timedelta(days=10)).isoformat(),
                "crime_type": "Robbery",
                "title": f"Incident {i}",
                "url": f"http://example.com/{i}",
            }
            for i in range(6)
        ]

        res_red = calculate_zone_risk(
            lat=12.0,
            lng=79.0,
            radius=1000.0,
            reference_time=ref_time,
            candidate_crimes=red_crimes,
        )
        self.assertEqual(res_red["score"], 60.0)
        self.assertEqual(res_red["zone"], "RED")

        # 15 incidents of severity 10 -> raw score = 150.0 -> must be capped at 100.0
        res_capped = calculate_zone_risk(
            lat=12.0,
            lng=79.0,
            radius=1000.0,
            reference_time=ref_time,
            candidate_crimes=red_crimes * 3,
        )
        self.assertEqual(res_capped["score"], 100.0)
        self.assertEqual(res_capped["zone"], "RED")

    def test_top_3_crime_types_ordering(self):
        """Top 3 crime types should be sorted by occurrence frequency."""
        ref_time = datetime(2026, 10, 1, tzinfo=timezone.utc)
        crimes = (
            [{"latitude": 12.0, "longitude": 79.0, "crime_type": "Theft", "severity_score": 5.0, "published_date": ref_time.isoformat()}] * 5
            + [{"latitude": 12.0, "longitude": 79.0, "crime_type": "Assault", "severity_score": 5.0, "published_date": ref_time.isoformat()}] * 4
            + [{"latitude": 12.0, "longitude": 79.0, "crime_type": "Robbery", "severity_score": 5.0, "published_date": ref_time.isoformat()}] * 3
            + [{"latitude": 12.0, "longitude": 79.0, "crime_type": "Fraud", "severity_score": 5.0, "published_date": ref_time.isoformat()}] * 1
        )

        res = calculate_zone_risk(lat=12.0, lng=79.0, candidate_crimes=crimes, reference_time=ref_time)
        self.assertEqual(res["top_3_crime_types"], ["Theft", "Assault", "Robbery"])

    def test_most_severe_recent_incident_tiebreaking(self):
        """When multiple incidents share the highest severity score, pick the most recent."""
        crimes = [
            {
                "latitude": 12.0,
                "longitude": 79.0,
                "severity_score": 10.0,
                "published_date": "2024-01-01T00:00:00Z",
                "title": "Older Incident",
                "crime_type": "Assault",
                "url": "http://old",
            },
            {
                "latitude": 12.0,
                "longitude": 79.0,
                "severity_score": 10.0,
                "published_date": "2026-05-01T00:00:00Z",
                "title": "Newer Incident",
                "crime_type": "Assault",
                "url": "http://new",
            },
            {
                "latitude": 12.0,
                "longitude": 79.0,
                "severity_score": 8.0,
                "published_date": "2026-09-01T00:00:00Z",
                "title": "Most Recent but Lower Severity",
                "crime_type": "Theft",
                "url": "http://recent-low",
            },
        ]

        res = calculate_zone_risk(lat=12.0, lng=79.0, candidate_crimes=crimes)
        self.assertEqual(res["most_severe_recent_incident"]["title"], "Newer Incident")


class TestZoneServiceKnownCoordinates(unittest.TestCase):
    """Integration tests querying live database for known locations (Katpadi, Sathuvachari)."""

    def setUp(self):
        self.app = app
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_known_coordinate_katpadi(self):
        """Katpadi epicenter (12.9806, 79.1368) has high crime density -> RED zone."""
        res = calculate_zone_risk(lat=12.9806, lng=79.1368, radius=1000.0)

        self.assertGreater(res["incident_count"], 0)
        self.assertGreaterEqual(res["score"], 60.0)
        self.assertEqual(res["zone"], "RED")
        self.assertIsNotNone(res["nearest_incident_distance"])
        self.assertIsNotNone(res["most_severe_recent_incident"])
        self.assertIn("title", res["most_severe_recent_incident"])
        self.assertIn("date", res["most_severe_recent_incident"])
        self.assertIn("source_url", res["most_severe_recent_incident"])
        self.assertEqual(res["confidence"], "high")

    def test_known_coordinate_sathuvachari(self):
        """Sathuvachari (12.926, 79.168) has zero recorded incidents in radius -> GREEN zone with low confidence."""
        res = calculate_zone_risk(lat=12.926, lng=79.168, radius=1000.0)

        self.assertEqual(res["incident_count"], 0)
        self.assertEqual(res["score"], 0.0)
        self.assertEqual(res["zone"], "GREEN")
        self.assertEqual(res["confidence"], "low")
        self.assertIsNotNone(res["note"])
        self.assertIn("limited", res["note"].lower())
        self.assertIsNone(res["nearest_incident_distance"])
        self.assertIsNone(res["most_severe_recent_incident"])


class TestZoneApiEndpoint(unittest.TestCase):
    """HTTP API endpoint tests for GET /api/zone."""

    def setUp(self):
        self.client = app.test_client()

    def test_api_zone_katpadi(self):
        """GET /api/zone?lat=12.9806&lng=79.1368 returns RED zone response."""
        resp = self.client.get("/api/zone?lat=12.9806&lng=79.1368&radius=1000")
        self.assertEqual(resp.status_code, 200)

        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["zone"], "RED")
        self.assertGreaterEqual(data["score"], 60.0)
        self.assertGreater(data["incident_count"], 0)
        self.assertIsInstance(data["top_3_crime_types"], list)
        self.assertIsInstance(data["nearest_incident_distance"], (int, float))
        self.assertIsInstance(data["most_severe_recent_incident"], dict)
        self.assertIn("title", data["most_severe_recent_incident"])
        self.assertIn("date", data["most_severe_recent_incident"])
        self.assertIn("source_url", data["most_severe_recent_incident"])
        self.assertIn("safety_tip", data)

    def test_api_zone_sathuvachari_low_confidence(self):
        """GET /api/zone?lat=12.926&lng=79.168 returns GREEN with confidence 'low'."""
        resp = self.client.get("/api/zone?lat=12.926&lng=79.168&radius=1000")
        self.assertEqual(resp.status_code, 200)

        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["zone"], "GREEN")
        self.assertEqual(data["score"], 0.0)
        self.assertEqual(data["incident_count"], 0)
        self.assertEqual(data["confidence"], "low")
        self.assertIsNotNone(data["note"])

    def test_api_zone_missing_params(self):
        """GET /api/zone without lat or lng returns 400 Bad Request."""
        resp = self.client.get("/api/zone")
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data["success"])

        resp2 = self.client.get("/api/zone?lat=12.98")
        self.assertEqual(resp2.status_code, 400)

    def test_api_zone_invalid_coords(self):
        """GET /api/zone with non-numeric coordinates returns 400 Bad Request."""
        resp = self.client.get("/api/zone?lat=invalid&lng=79.13")
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data["success"])

    def test_api_zone_out_of_range(self):
        """GET /api/zone with latitude > 90 returns 400 Bad Request."""
        resp = self.client.get("/api/zone?lat=95.0&lng=79.13")
        self.assertEqual(resp.status_code, 400)

    def test_api_zone_invalid_radius(self):
        """GET /api/zone with negative or non-numeric radius returns 400 Bad Request."""
        resp = self.client.get("/api/zone?lat=12.98&lng=79.13&radius=-50")
        self.assertEqual(resp.status_code, 400)

        resp2 = self.client.get("/api/zone?lat=12.98&lng=79.13&radius=abc")
        self.assertEqual(resp2.status_code, 400)


if __name__ == "__main__":
    unittest.main()
