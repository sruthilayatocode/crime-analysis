"""
Application settings and configuration constants.

This module defines all configuration constants used across the Crime Analysis
project. Values are loaded from environment variables with sensible defaults.

TODO:
    - Add environment variable validation.
    - Add support for YAML/JSON config file overrides.
    - Add secret management integration (e.g., HashiCorp Vault).
"""

from typing import Final, Dict, List
import os


# Application
APP_NAME: Final[str] = os.getenv("APP_NAME", "CrimeAnalysis")
APP_ENV: Final[str] = os.getenv("APP_ENV", "development")
APP_DEBUG: Final[bool] = os.getenv("APP_DEBUG", "true").lower() == "true"
APP_SECRET_KEY: Final[str] = os.getenv("APP_SECRET_KEY", "change-me")

# Server
HOST: Final[str] = os.getenv("HOST", "0.0.0.0")
PORT: Final[int] = int(os.getenv("PORT", "8000"))

# GIS defaults (Vellore, Tamil Nadu)
DEFAULT_LATITUDE: Final[float] = 12.9165
DEFAULT_LONGITUDE: Final[float] = 79.1325
DEFAULT_ZOOM: Final[int] = 12
RADIUS_KM: Final[float] = 5.0

# ML Model
MODEL_PATH: Final[str] = os.getenv("MODEL_PATH", "ml/models/crime_hotspot_model.pkl")
MODEL_THRESHOLD: Final[float] = float(os.getenv("MODEL_THRESHOLD", "0.7"))

# IoT / MQTT
MQTT_BROKER: Final[str] = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT: Final[int] = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC: Final[str] = os.getenv("MQTT_TOPIC", "crime/proximity/alerts")
GPS_UPDATE_INTERVAL: Final[int] = int(os.getenv("GPS_UPDATE_INTERVAL", "30"))

# Logging
LOG_LEVEL: Final[str] = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE: Final[str] = os.getenv("LOG_FILE", "logs/app.log")

# Supported cities
SUPPORTED_CITIES: Final[List[str]] = [
    "vellore",
    "chennai",
    "bangalore",
    "hyderabad",
]

# Crime category mapping
CRIME_CATEGORIES: Final[Dict[str, str]] = {
    "theft": "Property Crime",
    "assault": "Violent Crime",
    "burglary": "Property Crime",
    "robbery": "Violent Crime",
    "homicide": "Violent Crime",
    "fraud": "White Collar Crime",
}