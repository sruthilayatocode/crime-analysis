from datetime import datetime
from database import db


class Crime(db.Model):

    __tablename__ = "crimes"

    __table_args__ = (
        db.Index("idx_crimes_lat_lng", "latitude", "longitude"),
        db.Index("idx_crimes_published_date", "published_date"),
        db.Index("idx_crimes_crime_date", "crime_date"),
    )

    # Integer primary key kept for compatibility with the
    # existing architecture (CRUD routes reference <int:crime_id>).
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # Unique identifier from the validated data pipeline.
    article_id = db.Column(
        db.String(64),
        unique=False,
        nullable=True,
        index=True
    )

    title = db.Column(
        db.String(500),
        nullable=True
    )

    published_date = db.Column(
        db.String(50),
        nullable=True,
        index=True
    )

    source = db.Column(
        db.String(200),
        nullable=True
    )

    url = db.Column(
        db.String(1000),
        nullable=True
    )

    crime_type = db.Column(
        db.String(100),
        nullable=False,
        index=True
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    district = db.Column(
        db.String(100),
        nullable=True
    )

    locality = db.Column(
        db.String(200),
        nullable=True,
        index=True
    )

    # Nullable: most validated records genuinely have no
    # reliable coordinates. Never fabricate values here.
    latitude = db.Column(
        db.Float,
        nullable=True,
        index=True
    )

    longitude = db.Column(
        db.Float,
        nullable=True,
        index=True
    )

    location_confidence = db.Column(
        db.String(20),
        nullable=True,
        index=True
    )

    location_source = db.Column(
        db.String(100),
        nullable=True
    )

    # Incident-level severity/risk from the completed
    # scoring pipeline. Do not overwrite these with
    # dynamically derived counts.
    severity_score = db.Column(
        db.Float,
        nullable=True
    )

    risk_level = db.Column(
        db.String(30),
        nullable=True,
        index=True
    )

    # ---- Legacy fields retained for backwards compatibility ----

    location_name = db.Column(
        db.String(200),
        nullable=True
    )

    crime_date = db.Column(
        db.String(50),
        nullable=True
    )

    severity = db.Column(
        db.String(30),
        nullable=True
    )

    status = db.Column(
        db.String(20),
        default="APPROVED",
        nullable=True
    )

    reported_by_id = db.Column(
        db.Integer,
        nullable=True
    )

    reported_by_name = db.Column(
        db.String(150),
        nullable=True
    )

    admin_notes = db.Column(
        db.Text,
        nullable=True
    )

    reviewed_at = db.Column(
        db.DateTime,
        nullable=True
    )

    reviewed_by_id = db.Column(
        db.Integer,
        nullable=True
    )

    reviewed_by_name = db.Column(
        db.String(150),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=True
    )

    def to_dict(self):

        return {
            "id": self.id,
            "article_id": self.article_id,
            "title": self.title,
            "published_date": self.published_date,
            "source": self.source,
            "url": self.url,
            "crime_type": self.crime_type,
            "description": self.description,
            "district": self.district,
            "locality": self.locality,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "location_confidence": self.location_confidence,
            "location_source": self.location_source,
            "severity_score": self.severity_score,
            "risk_level": self.risk_level,
            "status": self.status or "APPROVED",
            "reported_by_id": self.reported_by_id,
            "reported_by_name": self.reported_by_name,
            "admin_notes": self.admin_notes,
            "reviewed_at": self.reviewed_at.isoformat() if isinstance(self.reviewed_at, datetime) else self.reviewed_at,
            "reviewed_by_id": self.reviewed_by_id,
            "reviewed_by_name": self.reviewed_by_name,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else str(self.created_at) if self.created_at else None,
            # Legacy fields (kept so old clients keep working)
            "location_name": self.location_name or self.locality,
            "crime_date": self.crime_date or self.published_date,
            "severity": self.severity or self.risk_level
        }

