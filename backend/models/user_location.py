from datetime import datetime, timedelta
from database import db


class UserLocation(db.Model):
    __tablename__ = "user_locations"

    __table_args__ = (
        db.Index("idx_user_loc_lat_lng", "latitude", "longitude"),
        db.Index("idx_user_loc_user_recorded", "user_id", "recorded_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    accuracy = db.Column(db.Float, nullable=True)  # in meters
    zone = db.Column(db.String(20), nullable=True)  # 'red' | 'yellow' | 'green'
    recorded_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    @classmethod
    def cleanup_old_records(cls, days=30):
        """Purge location points older than the retention limit (30 days default)."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        deleted = cls.query.filter(cls.recorded_at < cutoff).delete()
        db.session.commit()
        return deleted

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "accuracy": self.accuracy,
            "zone": self.zone,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }
