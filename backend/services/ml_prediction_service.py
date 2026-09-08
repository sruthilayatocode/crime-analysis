"""
Backend ML analytics service for CrimeSense.

Despite the filename, this is NOT a supervised prediction service.
It wraps unsupervised spatial hotspot detection and descriptive
temporal/pattern analysis.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ml.crime_pattern_analysis import analyze_crime_patterns
from ml.hotspot_model import HotspotModel
from ml.temporal_analysis import analyze_temporal_patterns


class MLAnalyticsService:
    """
    Service layer for unsupervised ML analytics.

    Responsibilities:
        * Retrieve crime records (caller supplies records).
        * Run hotspot clustering.
        * Run temporal analysis.
        * Run crime pattern analysis.
        * Return structured analytics results.
        * Handle empty/invalid data safely.
    """

    def get_hotspot_analysis(
        self,
        records: List[Dict[str, Any]],
        eps_km: Optional[float] = None,
        min_samples: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run DBSCAN hotspot detection on valid coordinates.

        Parameters
        ----------
        records : list of dict
            Crime records.
        eps_km : float or None
            DBSCAN epsilon in km. Uses project config default if None.
        min_samples : int or None
            Minimum cluster samples. Uses project config default if None.

        Returns
        -------
        dict
            Structured hotspot analysis results.
        """
        try:
            from config.config import DBSCAN_EPS_KM, DBSCAN_MIN_SAMPLES
            eps_km = eps_km if eps_km is not None else float(DBSCAN_EPS_KM)
            min_samples = min_samples if min_samples is not None else int(DBSCAN_MIN_SAMPLES)
        except Exception:
            eps_km = eps_km if eps_km is not None else 1.0
            min_samples = min_samples if min_samples is not None else 2

        coordinates = [
            (r.get("latitude"), r.get("longitude"))
            for r in records
        ]

        model = HotspotModel(
            eps_km=eps_km,
            min_samples=min_samples,
        )
        model.fit(coordinates)

        clusters = model.get_clusters()
        summary = model.get_cluster_summary(records=records)

        noise_count = model.noise_count()
        valid_count = model.valid_count()

        noise_percentage = 0.0
        if valid_count > 0:
            noise_percentage = round((noise_count / valid_count) * 100, 2)

        return {
            "status": "success",
            "method": "DBSCAN",
            "analysis_type": "unsupervised_hotspot_detection",
            "parameters": {
                "eps_km": eps_km,
                "min_samples": min_samples,
            },
            "metrics": {
                "total_records": len(records),
                "valid_coordinates": valid_count,
                "cluster_count": sum(1 for c in clusters if not c.get("noise")),
                "noise_points": noise_count,
                "noise_percentage": noise_percentage,
                "silhouette_score": None,
                "silhouette_note": (
                    "Silhouette score is not reported because the "
                    "current dataset is too small and/or produces too "
                    "few clusters for a mathematically valid score."
                ),
            },
            "hotspots": summary,
            "limitations": (
                "Hotspot detection is based on spatial proximity only. "
                "It does not predict future crime events."
            ),
        }

    def get_temporal_analysis(
        self,
        records: List[Dict[str, Any]],
        date_field: str = "crime_date",
    ) -> Dict[str, Any]:
        """
        Run descriptive publication-date analysis.

        Parameters
        ----------
        records : list of dict
            Crime records.
        date_field : str
            Name of the date field.

        Returns
        -------
        dict
            Temporal analysis results.
        """
        result = analyze_temporal_patterns(records, date_field=date_field)

        return {
            "status": "success",
            "analysis_type": "descriptive_publication_date_analysis",
            "data": result,
            "limitations": result.get("limitations", ""),
        }

    def get_pattern_analysis(
        self,
        records: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Run descriptive crime pattern analysis.

        Parameters
        ----------
        records : list of dict
            Crime records.

        Returns
        -------
        dict
            Pattern analysis results.
        """
        result = analyze_crime_patterns(records)

        return {
            "status": "success",
            "analysis_type": "descriptive_pattern_analysis",
            "data": result,
            "limitations": result.get("limitations", ""),
        }

    def get_full_analysis(
        self,
        records: List[Dict[str, Any]],
        eps_km: Optional[float] = None,
        min_samples: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run all available unsupervised analyses.

        Parameters
        ----------
        records : list of dict
            Crime records.
        eps_km : float or None
            DBSCAN epsilon override.
        min_samples : int or None
            DBSCAN min_samples override.

        Returns
        -------
        dict
            Combined analysis results.
        """
        hotspots = self.get_hotspot_analysis(records, eps_km=eps_km, min_samples=min_samples)
        temporal = self.get_temporal_analysis(records)
        pattern = self.get_pattern_analysis(records)

        return {
            "status": "success",
            "analysis_type": "unsupervised_composite_analysis",
            "hotspots": hotspots,
            "temporal": temporal,
            "patterns": pattern,
            "limitations": (
                "All analyses are descriptive/unsupervised. "
                "No supervised prediction is performed."
            ),
        }
