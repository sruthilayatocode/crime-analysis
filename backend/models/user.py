"""
User model for CrimeSense authentication.

Roles:
    USER  - standard account created through /api/auth/register
    ADMIN - administrator provisioned with backend/seed_admin.py

Passwords are stored as Werkzeug hashes, never as plain text.
"""

from datetime import datetime, timezone

from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

from database import db


VALID_ROLES = ("USER", "ADMIN")

DEFAULT_ROLE = "USER"


class User(db.Model):

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(120),
        nullable=False
    )

    email = db.Column(
        db.String(200),
        nullable=False,
        unique=True,
        index=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False,
        default=DEFAULT_ROLE
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def set_password(self, raw_password):
        """Store a salted hash of the supplied password."""

        self.password_hash = generate_password_hash(
            raw_password
        )

    def check_password(self, raw_password):
        """Return True when the password matches the hash."""

        if not self.password_hash:
            return False

        return check_password_hash(
            self.password_hash,
            raw_password
        )

    def is_admin(self):
        return (self.role or "").upper() == "ADMIN"

    def to_dict(self):
        """Public representation. Never exposes password_hash."""

        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            )
        }
