"""
config.py
=========
Global configuration module for CrimeSense backend services.
"""

from zone_config import (
    ZONE_THRESHOLDS,
    MIN_SCORE,
    MAX_SCORE,
    DEFAULT_RADIUS_METERS,
    RECENCY_CONFIG,
    SAFETY_TIPS,
    LIMITED_DATA_NOTE,
)

__all__ = [
    "ZONE_THRESHOLDS",
    "MIN_SCORE",
    "MAX_SCORE",
    "DEFAULT_RADIUS_METERS",
    "RECENCY_CONFIG",
    "SAFETY_TIPS",
    "LIMITED_DATA_NOTE",
]
