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


# ---- Authentication ----------------------------------------- #

# Key used to sign authentication tokens. Override this with a
# SECRET_KEY entry in backend/.env for any real deployment.
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "crimesense-dev-secret-change-me"
)

# How long an issued token stays valid.
TOKEN_EXPIRY_HOURS = float(
    os.getenv("TOKEN_EXPIRY_HOURS", "12")
)

# Create the first ADMIN account on start-up when the database
# does not contain one yet (development convenience).
SEED_DEFAULT_ADMIN = (
    os.getenv("SEED_DEFAULT_ADMIN", "1") == "1"
)

DEFAULT_ADMIN_NAME = os.getenv(
    "DEFAULT_ADMIN_NAME",
    "System Administrator"
)

DEFAULT_ADMIN_EMAIL = os.getenv(
    "DEFAULT_ADMIN_EMAIL",
    "admin@crimesense.local"
)

DEFAULT_ADMIN_PASSWORD = os.getenv(
    "DEFAULT_ADMIN_PASSWORD",
    "Admin@12345"
)

