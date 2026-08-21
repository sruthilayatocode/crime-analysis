"""
Database configuration and connection settings.

This module provides placeholder configuration variables for database
connections used by the Crime Analysis project.

TODO:
    - Add SQLAlchemy engine creation.
    - Add connection pooling configuration.
    - Add migration support via Alembic.
    - Add read-replica and sharding configuration.
"""

from typing import Optional, Dict, Any
import os


# Database connection parameters
DB_HOST: Optional[str] = os.getenv("DB_HOST", "localhost")
DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
DB_NAME: str = os.getenv("DB_NAME", "crime_analysis")
DB_USER: str = os.getenv("DB_USER", "postgres")
DB_PASSWORD: Optional[str] = os.getenv("DB_PASSWORD", None)

# Connection string
DATABASE_URL: Optional[str] = os.getenv(
    "DATABASE_URL",
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
)

# Connection pool settings
POOL_SIZE: int = 10
MAX_OVERFLOW: int = 20
POOL_TIMEOUT: int = 30
POOL_RECYCLE: int = 1800  # 30 minutes

# Migration settings
MIGRATIONS_DIR: str = "database/migrations"


def get_database_config() -> Dict[str, Any]:
    """
    Return the full database configuration as a dictionary.

    Returns:
        Dict[str, Any]: Database configuration parameters.
    """
    return {
        "host": DB_HOST,
        "port": DB_PORT,
        "name": DB_NAME,
        "user": DB_USER,
        "password": "***" if DB_PASSWORD else None,
        "url": DATABASE_URL,
        "pool_size": POOL_SIZE,
        "max_overflow": MAX_OVERFLOW,
        "pool_timeout": POOL_TIMEOUT,
        "pool_recycle": POOL_RECYCLE,
    }