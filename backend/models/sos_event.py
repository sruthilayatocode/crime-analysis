from datetime import datetime
from database import db


class SOSEvent(db.Model):
    __tablename__ = "sos_events"

    __table_args__ = (
        db.Index("idx_sos_event_lat_lng", "latitude", "longitude"),
        db.Index("idx_sos_event_status_user", "status", "user_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    type = db.Column(
        db.String(30),
        default="manual",
        nullable=False
    )  # 'manual' | 'auto_red_zone'
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    accuracy = db.Column(db.Float, nullable=True)
    zone = db.Column(db.String(20), nullable=True)  # 'red' | 'yellow' | 'green'
    status = db.Column(
        db.String(30),
        default="active",
        nullable=False
    )  # 'active' | 'resolved' | 'cancelled'
    contacts_notified = db.Column(db.JSON, default=list, nullable=True)
    live_tracking_until = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    resolved_at = db.Column(db.DateTime, nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)

    # Optional relationship to user
    user = db.relationship("User", backref=db.backref("sos_events", lazy=True, cascade="all, delete-orphan"))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else "Anonymous User",
            "user_email": self.user.email if self.user else None,
            "type": self.type,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "accuracy": self.accuracy,
            "zone": self.zone,
            "status": self.status,
            "contacts_notified": self.contacts_notified or [],
            "live_tracking_until": self.live_tracking_until.isoformat() if self.live_tracking_until else None,
            "maps_url": f"https://maps.google.com/?q={self.latitude:.6f},{self.longitude:.6f}",
            "admin_notes": self.admin_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
