"""
Proximity alert service for CrimeSense.

This service determines whether a user's current location
is near historical crime locations or detected hotspots.

It does NOT predict future crime. It only reports spatial
proximity to historically recorded crime locations.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class AlertService:
    """
    Service layer for proximity alert decisions.

    Responsibilities:
        * Accept validated user coordinates.
        * Check nearby crimes/hotspots.
        * Determine whether an alert condition is met.
        * Return structured alert information.
        * Handle empty results safely.
    """

    def __init__(self, proximity_service, ml_analytics_service=None):
        """
        Parameters
        ----------
        proximity_service : module or object
            The proximity_service module or compatible object.
        ml_analytics_service : MLAnalyticsService or None
            Optional ML analytics service for hotspot detection.
        """
        self.proximity = proximity_service
        self.ml_analytics = ml_analytics_service

    def check_alert(
        self,
        user_latitude: float,
        user_longitude: float,
        crimes: List[Dict[str, Any]],
        hotspots: Optional[List[Dict[str, Any]]] = None,
        alert_radius_meters: float = 500.0,
        max_results: int = 50,
    ) -> Dict[str, Any]:
        """
        Determine whether the user is near any crime or hotspot.

        Parameters
        ----------
        user_latitude : float
            User latitude in degrees.
        user_longitude : float
            User longitude in degrees.
        crimes : list of dict
            Crime records from the database.
        hotspots : list of dict or None
            Hotspot records. If None, no hotspot check is performed.
        alert_radius_meters : float
            Alert radius in metres.
        max_results : int
            Maximum number of nearby results to return.

        Returns
        -------
        dict
            Structured alert response.
        """
        radius_km = alert_radius_meters / 1000.0

        nearby_crimes = self.proximity.find_nearby_crimes(
            crimes=crimes,
            latitude=user_latitude,
            longitude=user_longitude,
            radius_km=radius_km,
            limit=max_results,
        )

        nearby_hotspots = []

        if hotspots is not None and self.ml_analytics is not None:
            nearby_hotspots = self.proximity.find_nearby_hotspots(
                hotspots=hotspots,
                latitude=user_latitude,
                longitude=user_longitude,
                radius_km=radius_km,
                limit=max_results,
            )

        alert_triggered = bool(nearby_crimes or nearby_hotspots)

        if alert_triggered:
            message = (
                "Warning: You are near a "
                "historical crime hotspot."
            )
        else:
            message = (
                "You are outside the "
                "crime hotspot alert radius."
            )

        return {
            "status": "success",
            "alert": alert_triggered,
            "message": message,
            "nearby_crimes": nearby_crimes,
            "nearby_hotspots": nearby_hotspots,
            "checked_radius_km": round(radius_km, 3),
            "checked_radius_meters": alert_radius_meters,
            "limitations": (
                "This alert is based on historical crime locations "
                "only. It does not predict future crime events."
            ),
        }
