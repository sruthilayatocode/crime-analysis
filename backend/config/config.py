"""
Application configuration.

Loads environment variables from backend/.env and exposes
the Supabase client when credentials are available.

Supabase credentials are NEVER hard-coded in source files.
"""

import os

from dotenv import load_dotenv


# backend/ directory (parent of the config package)
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

ENV_FILE = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_FILE)


# Supabase PostgreSQL credentials (from environment)
SUPABASE_URL = os.getenv(
    "SUPABASE_URL",
    ""
).strip()

SUPABASE_KEY = os.getenv(
    "SUPABASE_KEY",
    ""
).strip()

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


_supabase_client = None


def supabase_enabled():
    """
    Return True when Supabase credentials
    are configured through environment variables.
    """

    return bool(SUPABASE_URL and SUPABASE_KEY)


def get_supabase_client():
    """
    Create (once) and return the Supabase client
    built from environment variables.
    """

    global _supabase_client

    if _supabase_client is None:

        from supabase import create_client

        _supabase_client = create_client(
            SUPABASE_URL,
            SUPABASE_KEY
        )

    return _supabase_client