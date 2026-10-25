import secrets
from datetime import datetime
from database import db


class SharedLink(db.Model):
    __tablename__ = "shared_links"

    __table_args__ = (
        db.Index("idx_shared_link_lat_lng", "latitude", "longitude"),
        db.Index("idx_shared_link_token_revoked", "token", "is_revoked"),
    )

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(
        db.String(64),
        unique=True,
        nullable=False,
        index=True
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    label = db.Column(db.String(100), default="Shared Location", nullable=True)
    address = db.Column(db.String(300), nullable=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    accuracy = db.Column(db.Float, nullable=True)
    zone = db.Column(db.String(20), default="green", nullable=True)
    is_live = db.Column(db.Boolean, default=False, nullable=False)
    is_revoked = db.Column(db.Boolean, default=False, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", backref=db.backref("shared_links", lazy=True, cascade="all, delete-orphan"))

    @classmethod
    def generate_token(cls):
        return secrets.token_urlsafe(24)

    def is_expired(self):
        return datetime.utcnow() > self.expires_at

    def is_active(self):
        return not self.is_revoked and not self.is_expired()

    def to_public_dict(self):
        """Sanitized public payload: strictly reveals only the shared location & zone without private data."""
        active = self.is_active()
        return {
            "token": self.token,
            "label": self.label or "Shared Location",
            "address": self.address,
            "latitude": self.latitude if active else None,
            "longitude": self.longitude if active else None,
            "accuracy": self.accuracy if active else None,
            "zone": self.zone or "green",
            "is_live": self.is_live,
            "is_expired": self.is_expired(),
            "is_revoked": self.is_revoked,
            "is_active": active,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "maps_url": f"https://maps.google.com/?q={self.latitude:.6f},{self.longitude:.6f}" if active else None,
        }

    def to_owner_dict(self):
        """Owner payload with management capabilities."""
        data = self.to_public_dict()
        data["id"] = self.id
        data["user_id"] = self.user_id
        data["created_at"] = self.created_at.isoformat() if self.created_at else None
        return data
