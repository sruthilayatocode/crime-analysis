"""
Application configuration.

Loads environment variables from backend/.env and exposes
the SQLite database URI used by the application.
"""

import os

from dotenv import load_dotenv


# backend/ directory (parent of the config package)
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

ENV_FILE = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_FILE)


# SQLite database URI
SQLALCHEMY_DATABASE_URI = os.getenv(
    "SQLALCHEMY_DATABASE_URI",
    "sqlite:///crimesense.db"
)

CRIMES_TABLE = "crimes"


# DBSCAN hotspot detection configuration.
# eps is the neighborhood radius in kilometres.  Points within
# this distance are considered neighbours by the algorithm.
# min_samples is the minimum number of crimes required to
# form a hotspot cluster.  Smaller values create more clusters
# (including spurious ones); larger values merge nearby areas.
DBSCAN_EPS_KM = float(
    os.getenv("DBSCAN_EPS_KM", "1.0")
)
DBSCAN_MIN_SAMPLES = int(
    os.getenv("DBSCAN_MIN_SAMPLES", "2")
)

PROXIMITY_ALERT_RADIUS_METERS = float(
    os.getenv("PROXIMITY_ALERT_RADIUS_METERS", "500")
)
PROXIMITY_ALERT_MIN_RADIUS_METERS = 10.0
PROXIMITY_ALERT_MAX_RADIUS_METERS = 50000.0

PROXIMITY_MAX_RESULTS = int(
    os.getenv("PROXIMITY_MAX_RESULTS", "50")
)


# Earth radius in kilometres (used to convert km to radians
# for the Haversine metric).
EARTH_RADIUS_KM = 6371.0


# CORS origins allowed to call the API during
# local frontend development.
DEFAULT_CORS_ORIGINS = ",".join([
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
])

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        DEFAULT_CORS_ORIGINS
    ).split(",")
    if origin.strip()
]
