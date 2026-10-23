"""
data_service.py
===============
Unified database access layer for Crime records in SQLite (backend/instance/crimesense.db).
All operations query and write to the database directly via SQLAlchemy.
Zero CSV or JSON file reads.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from database import db
from models.crime import Crime


def get_all_crimes(
    crime_type: Optional[str] = None,
    district: Optional[str] = None,
    locality: Optional[str] = None,
    risk_level: Optional[str] = None,
    search: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[Crime]:
    """Query crime records directly from the SQLite database with optional filters."""
    query = Crime.query

    if crime_type:
        query = query.filter(Crime.crime_type.ilike(f"%{crime_type}%"))
    if district:
        query = query.filter(Crime.district.ilike(f"%{district}%"))
    if locality:
        query = query.filter(Crime.locality.ilike(f"%{locality}%"))
    if risk_level:
        query = query.filter(Crime.risk_level.ilike(f"%{risk_level}%"))
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            db.or_(
                Crime.title.ilike(search_pattern),
                Crime.description.ilike(search_pattern),
                Crime.locality.ilike(search_pattern),
                Crime.article_id.ilike(search_pattern),
            )
        )

    query = query.order_by(Crime.id.desc())

    if offset is not None:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)

    return query.all()


def get_crime_by_id(crime_id: int) -> Optional[Crime]:
    """Retrieve single crime record by primary key."""
    return db.session.get(Crime, crime_id)


def get_crime_by_article_id(article_id: str) -> Optional[Crime]:
    """Retrieve single crime record by article_id."""
    return Crime.query.filter_by(article_id=str(article_id)).first()


def count_crimes() -> int:
    """Return total count of crime records in SQLite database."""
    return Crime.query.count()


def get_verified_crimes() -> List[Crime]:
    """Return all high-confidence geocoded crime records."""
    return (
        Crime.query.filter(
            Crime.location_confidence.in_(["HIGH", "high"]),
            Crime.latitude.isnot(None),
            Crime.longitude.isnot(None),
        )
        .all()
    )


def create_crime(payload: Dict[str, Any]) -> Crime:
    """Insert a new crime record directly into SQLite and commit immediately."""
    new_crime = Crime(
        article_id=payload.get("article_id"),
        title=payload.get("title"),
        published_date=payload.get("published_date") or payload.get("crime_date"),
        source=payload.get("source"),
        url=payload.get("url"),
        crime_type=payload.get("crime_type") or "Unknown",
        description=payload.get("description"),
        district=payload.get("district") or "Vellore",
        locality=payload.get("locality") or payload.get("location_name"),
        latitude=float(payload["latitude"]) if payload.get("latitude") not in (None, "") else None,
        longitude=float(payload["longitude"]) if payload.get("longitude") not in (None, "") else None,
        location_confidence=payload.get("location_confidence"),
        location_source=payload.get("location_source"),
        severity_score=float(payload["severity_score"]) if payload.get("severity_score") not in (None, "") else None,
        risk_level=payload.get("risk_level"),
        location_name=payload.get("location_name") or payload.get("locality"),
        crime_date=payload.get("crime_date") or payload.get("published_date"),
        severity=payload.get("severity") or payload.get("risk_level"),
    )
    db.session.add(new_crime)
    db.session.commit()
    return new_crime


def update_crime(crime_id: int, payload: Dict[str, Any]) -> Optional[Crime]:
    """Update existing crime record in SQLite and commit immediately."""
    crime = db.session.get(Crime, crime_id)
    if not crime:
        return None

    for field in [
        "title",
        "published_date",
        "source",
        "url",
        "crime_type",
        "description",
        "district",
        "locality",
        "location_confidence",
        "location_source",
        "risk_level",
        "location_name",
        "crime_date",
        "severity",
    ]:
        if field in payload and payload[field] is not None:
            setattr(crime, field, payload[field])

    if "latitude" in payload:
        crime.latitude = (
            float(payload["latitude"])
            if payload["latitude"] not in (None, "")
            else None
        )
    if "longitude" in payload:
        crime.longitude = (
            float(payload["longitude"])
            if payload["longitude"] not in (None, "")
            else None
        )
    if "severity_score" in payload:
        crime.severity_score = (
            float(payload["severity_score"])
            if payload["severity_score"] not in (None, "")
            else None
        )

    db.session.commit()
    return crime


def delete_crime(crime_id: int) -> bool:
    """Delete crime record from SQLite and commit immediately."""
    crime = db.session.get(Crime, crime_id)
    if not crime:
        return False

    db.session.delete(crime)
    db.session.commit()
    return True


def get_hotspots() -> List[Dict[str, Any]]:
    """Compute hotspots directly from SQLite DB."""
    from services.hotspot_service import get_hotspots_from_db
    return get_hotspots_from_db()
