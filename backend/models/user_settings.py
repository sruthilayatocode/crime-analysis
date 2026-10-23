from database import db


class UserSettings(db.Model):
    __tablename__ = "user_settings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    location_sharing_enabled = db.Column(db.Boolean, default=False, nullable=False)
    red_zone_alert_enabled = db.Column(db.Boolean, default=True, nullable=False)
    inactivity_minutes = db.Column(db.Integer, default=10, nullable=False)
    alert_radius_m = db.Column(db.Integer, default=500, nullable=False)
    share_live_location_with_admin = db.Column(db.Boolean, default=False, nullable=False)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "location_sharing_enabled": self.location_sharing_enabled,
            "red_zone_alert_enabled": self.red_zone_alert_enabled,
            "inactivity_minutes": self.inactivity_minutes,
            "alert_radius_m": self.alert_radius_m,
            "share_live_location_with_admin": self.share_live_location_with_admin,
        }
