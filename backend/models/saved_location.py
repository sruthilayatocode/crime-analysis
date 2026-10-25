from datetime import datetime
from database import db


class SavedLocation(db.Model):
    __tablename__ = "saved_locations"

    __table_args__ = (
        db.Index("idx_saved_loc_lat_lng", "latitude", "longitude"),
        db.Index("idx_saved_loc_user_pinned", "user_id", "is_pinned"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    label = db.Column(db.String(100), nullable=False)  # e.g., 'Home', 'Work', 'College'
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(300), nullable=True)
    zone = db.Column(db.String(20), default="green", nullable=False)  # 'red' | 'yellow' | 'green'
    is_pinned = db.Column(db.Boolean, default=False, nullable=False)
    last_checked_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", backref=db.backref("saved_locations", lazy=True, cascade="all, delete-orphan"))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "label": self.label,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "address": self.address,
            "zone": self.zone,
            "is_pinned": bool(self.is_pinned),
            "last_checked_at": self.last_checked_at.isoformat() if self.last_checked_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
