"""Database package bridge for CrimeSense backend."""
try:
    from backend.database import db  # noqa: F401
except ImportError:
    try:
        from database import db  # noqa: F401
    except ImportError:
        pass
