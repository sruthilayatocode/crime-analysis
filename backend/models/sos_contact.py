from datetime import datetime
from database import db


class SOSContact(db.Model):
    __tablename__ = "sos_contacts"

    __table_args__ = (
        db.Index("idx_sos_contacts_user_id", "user_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(30), nullable=False)  # E.164 formatted (+919876543210)
    relationship = db.Column(db.String(50), default="Family", nullable=True)
    is_primary = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", backref=db.backref("sos_contacts", lazy=True, cascade="all, delete-orphan"))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "phone": self.phone,
            "relationship": self.relationship or "Family",
            "is_primary": bool(self.is_primary),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
