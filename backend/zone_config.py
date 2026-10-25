"""
zone_config.py
==============
Configuration for the CrimeSense Zone Analysis Service.
Defines risk thresholds, distance decay settings, recency decay weights,
and safety tips for zone evaluation.
"""

# Risk score thresholds on a 0-100 scale:
# >= 60 RED
# 30-59 YELLOW
# < 30 GREEN
ZONE_THRESHOLDS = {
    "RED": 60.0,
    "YELLOW": 30.0,
    "GREEN": 0.0,
}

# Normalization bounds
MIN_SCORE = 0.0
MAX_SCORE = 100.0

# Search radius defaults in meters
DEFAULT_RADIUS_METERS = 1000.0

# Recency weighting rules:
# - Incidents newer than 6 months (~182.5 days): weight = 1.0
# - Incidents between 6 and 24 months (~182.5 to 730 days): weight = 0.7
# - Incidents older than 24 months (> 730 days): weight = 0.4
RECENCY_CONFIG = {
    "NEW_THRESHOLD_DAYS": 182.5,
    "MEDIUM_THRESHOLD_DAYS": 730.0,
    "WEIGHT_NEW": 1.0,
    "WEIGHT_MEDIUM": 0.7,
    "WEIGHT_OLD": 0.4,
    "DEFAULT_WEIGHT": 0.4,  # Used when published date is missing or unparseable
}

# Plain-language safety tips by zone
SAFETY_TIPS = {
    "RED": (
        "High risk zone: Frequent or severe crime incidents reported in this area. "
        "Avoid poorly lit or isolated paths at night, travel in groups where possible, "
        "and keep emergency contacts readily accessible."
    ),
    "YELLOW": (
        "Moderate risk zone: Moderate incident activity reported nearby. "
        "Stay vigilant, keep personal belongings secure, and prefer well-traveled main routes after dark."
    ),
    "GREEN": (
        "Low risk zone: Low crime activity recorded within this vicinity. "
        "Maintain routine situational awareness and practice standard personal safety habits."
    ),
    "GREEN_LOW_CONFIDENCE": (
        "Low risk zone (Limited data coverage): No or very few incidents are recorded "
        "within this radius. Exercise standard caution and remain observant of your surroundings."
    ),
}

# Informational notes
LIMITED_DATA_NOTE = "Data coverage is limited within the specified radius."
