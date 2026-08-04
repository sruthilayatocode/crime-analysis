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

    latitude = db.Column(
        db.Float,
        nullable=False
    )

    longitude = db.Column(
        db.Float,
        nullable=False
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

    def to_dict(self):

        return {
            "id": self.id,
            "crime_type": self.crime_type,
            "description": self.description,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "location_name": self.location_name,
            "crime_date": self.crime_date,
            "severity": self.severity
        }