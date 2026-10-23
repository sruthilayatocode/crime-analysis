from datetime import datetime
from database import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    admin_email = db.Column(db.String(150), nullable=True)
    admin_name = db.Column(db.String(150), nullable=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    target_entity = db.Column(db.String(150), nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    @classmethod
    def record(cls, action: str, admin=None, target_entity: str = None, details: str = None, ip_address: str = None):
        """Helper to create and persist an audit log entry."""
        admin_id = admin.id if admin else None
        admin_email = admin.email if admin else "System"
        admin_name = admin.name if admin else "System"

        log_entry = cls(
            admin_id=admin_id,
            admin_email=admin_email,
            admin_name=admin_name,
            action=action,
            target_entity=target_entity,
            details=details,
            ip_address=ip_address,
            created_at=datetime.utcnow(),
        )
        db.session.add(log_entry)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
        return log_entry

    def to_dict(self):
        return {
            "id": self.id,
            "admin_id": self.admin_id,
            "admin_email": self.admin_email,
            "admin_name": self.admin_name,
            "action": self.action,
            "target_entity": self.target_entity,
            "details": self.details,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
