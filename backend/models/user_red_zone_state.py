"""
user_red_zone_state.py
======================
Model tracking the safety state machine for RED zone inactivity monitoring.
States: SAFE -> IN_RED -> WARNING -> AUTO_ALERT_SENT
"""

from datetime import datetime
from database import db


class UserRedZoneState(db.Model):
    __tablename__ = "user_red_zone_states"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    # States: 'SAFE' | 'IN_RED' | 'WARNING' | 'AUTO_ALERT_SENT'
    state = db.Column(db.String(30), default="SAFE", nullable=False, index=True)
    
    entered_red_at = db.Column(db.DateTime, nullable=True)
    last_heartbeat_at = db.Column(db.DateTime, nullable=True)
    last_interaction_at = db.Column(db.DateTime, nullable=True)
    
    warning_prompt_sent_at = db.Column(db.DateTime, nullable=True)
    warning_expires_at = db.Column(db.DateTime, nullable=True)
    last_auto_alert_at = db.Column(db.DateTime, nullable=True)
    
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    accuracy = db.Column(db.Float, nullable=True)
    zone = db.Column(db.String(20), default="green", nullable=True)
    is_stale_heartbeat = db.Column(db.Boolean, default=False, nullable=False)
    
    push_subscription = db.Column(db.JSON, nullable=True)
    
    user = db.relationship("User", backref=db.backref("red_zone_state", uselist=False, cascade="all, delete-orphan"))

    def to_dict(self):
        now = datetime.utcnow()
        seconds_remaining = 0
        if self.state == "WARNING" and self.warning_expires_at:
            diff = (self.warning_expires_at - now).total_seconds()
            seconds_remaining = max(0, int(diff))

        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else "User",
            "state": self.state,
            "zone": self.zone or "green",
            "entered_red_at": self.entered_red_at.isoformat() if self.entered_red_at else None,
            "last_heartbeat_at": self.last_heartbeat_at.isoformat() if self.last_heartbeat_at else None,
            "last_interaction_at": self.last_interaction_at.isoformat() if self.last_interaction_at else None,
            "warning_prompt_sent_at": self.warning_prompt_sent_at.isoformat() if self.warning_prompt_sent_at else None,
            "warning_expires_at": self.warning_expires_at.isoformat() if self.warning_expires_at else None,
            "seconds_remaining": seconds_remaining,
            "last_auto_alert_at": self.last_auto_alert_at.isoformat() if self.last_auto_alert_at else None,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "accuracy": self.accuracy,
            "is_stale_heartbeat": self.is_stale_heartbeat,
        }
