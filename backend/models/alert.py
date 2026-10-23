from datetime import datetime
from database import db


class Alert(db.Model):
    __tablename__ = "alerts"

    __table_args__ = (
        db.Index("idx_alerts_user_id", "user_id"),
        db.Index("idx_alerts_lat_lng", "latitude", "longitude"),
        db.Index("idx_alerts_created_at", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    alert_type = db.Column(db.String(50), default="proximity", nullable=False)  # 'proximity' | 'red_zone' | 'broadcast' | 'sos'
    severity = db.Column(db.String(30), default="HIGH", nullable=False)        # 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    radius_m = db.Column(db.Float, default=1000.0, nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = db.relationship("User", backref=db.backref("alerts", lazy=True, cascade="all, delete-orphan"))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "radius_m": self.radius_m,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
