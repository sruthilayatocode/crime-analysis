from datetime import datetime, timezone

from database import db


class Crime(db.Model):

    __tablename__ = "crimes"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    crime_type = db.Column(
        db.String(100),
        nullable=False
    )

    description = db.Column(
        db.String(500),
        nullable=True
    )

    # Nullable because the handoff dataset contains
    # records that could not be geocoded.
    latitude = db.Column(
        db.Float,
        nullable=True
    )

    longitude = db.Column(
        db.Float,
        nullable=True
    )

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

    article_id = db.Column(
        db.String(64),
        nullable=True,
        index=True
    )

    title = db.Column(
        db.String(500),
        nullable=True
    )

    source = db.Column(
        db.String(200),
        nullable=True
    )

    url = db.Column(
        db.String(1000),
        nullable=True
    )

    district = db.Column(
        db.String(200),
        nullable=True
    )

    location_confidence = db.Column(
        db.String(50),
        nullable=True
    )

    location_source = db.Column(
        db.String(100),
        nullable=True
    )

    severity_score = db.Column(
        db.Integer,
        nullable=True
    )

    risk_level = db.Column(
        db.String(30),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def to_dict(self):

        return {
            "id": self.id,
            "crime_type": self.crime_type,
            "description": self.description,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "location_name": self.location_name,
            "crime_date": self.crime_date,
            "severity": self.severity,
            "article_id": self.article_id,
            "title": self.title,
            "source": self.source,
            "url": self.url,
            "district": self.district,
            "location_confidence": self.location_confidence,
            "location_source": self.location_source,
            "severity_score": self.severity_score,
            "risk_level": self.risk_level,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            )
        }
