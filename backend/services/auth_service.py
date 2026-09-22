"""
Authentication service layer.

Contains validation, password hashing and signed-token handling
plus the registration / login business logic. Routes call these
functions instead of touching the database directly.

Tokens are stateless HMAC-SHA256 signed payloads, so no extra
dependency (JWT library) is needed - only the Python standard
library and Werkzeug, which Flask already ships with.
"""

import base64
import binascii
import hashlib
import hmac
import json
import re
import time

from config.config import (
    DEFAULT_ADMIN_EMAIL,
    DEFAULT_ADMIN_NAME,
    DEFAULT_ADMIN_PASSWORD,
    SECRET_KEY,
    SEED_DEFAULT_ADMIN,
    TOKEN_EXPIRY_HOURS,
)

from services import user_service

from services.errors import (
    UnauthorizedError,
    ValidationError,
)


# Roles must stay in sync with models.user.VALID_ROLES.
VALID_ROLES = ("USER", "ADMIN")

DEFAULT_ROLE = "USER"

MIN_PASSWORD_LENGTH = 6

EMAIL_PATTERN = re.compile(
    r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$"
)


# ---- Token helpers ------------------------------------------ #

def _base64_encode(raw_bytes):
    return (
        base64.urlsafe_b64encode(raw_bytes)
        .decode("utf-8")
        .rstrip("=")
    )


def _base64_decode(encoded):
    padding = "=" * (-len(encoded) % 4)

    return base64.urlsafe_b64decode(
        encoded + padding
    )


def _sign(body):
    return hmac.new(
        SECRET_KEY.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256
    ).digest()


def create_token(user, expires_in_hours=None):
    """Build a signed token that identifies the account."""

    lifetime = (
        TOKEN_EXPIRY_HOURS
        if expires_in_hours is None
        else expires_in_hours
    )

    payload = {
        "uid": user.id,
        "email": user.email,
        "role": user.role,
        "exp": int(time.time()) + int(
            float(lifetime) * 3600
        )
    }

    body = _base64_encode(
        json.dumps(
            payload,
            separators=(",", ":")
        ).encode("utf-8")
    )

    return f"{body}.{_base64_encode(_sign(body))}"


def decode_token(token):
    """
    Validate a token and return its payload.

    Raises UnauthorizedError (HTTP 401) when the token is
    missing, malformed, tampered with or expired.
    """

    if (
        not token
        or not isinstance(token, str)
        or token.count(".") != 1
    ):
        raise UnauthorizedError(
            "A valid authentication token is required"
        )

    body, signature = token.split(".")

    try:

        expected_signature = _sign(body)

        supplied_signature = _base64_decode(
            signature
        )

    except (
        TypeError,
        ValueError,
        binascii.Error
    ):
        raise UnauthorizedError(
            "A valid authentication token is required"
        )

    if not hmac.compare_digest(
        expected_signature,
        supplied_signature
    ):
        raise UnauthorizedError(
            "The authentication token is invalid"
        )

    try:

        payload = json.loads(
            _base64_decode(body).decode("utf-8")
        )

    except (
        TypeError,
        ValueError,
        UnicodeDecodeError,
        binascii.Error
    ):
        raise UnauthorizedError(
            "The authentication token is invalid"
        )

    if not isinstance(payload, dict) or "uid" not in payload:
        raise UnauthorizedError(
            "The authentication token is invalid"
        )

    try:
        expires_at = int(payload.get("exp", 0))
    except (TypeError, ValueError):
        raise UnauthorizedError(
            "The authentication token is invalid"
        )

    if expires_at < int(time.time()):
        raise UnauthorizedError(
            "Your session has expired. Please sign in again"
        )

    return payload


# ---- Validation helpers ------------------------------------- #

def normalize_role(role):
    """Coerce any input into a known role (defaults to USER)."""

    if role is None:
        return DEFAULT_ROLE

    candidate = str(role).strip().upper()

    if candidate not in VALID_ROLES:
        return DEFAULT_ROLE

    return candidate


def _validate_email(email):

    if not isinstance(email, str) or not email.strip():
        raise ValidationError("Email is required")

    cleaned_email = email.strip().lower()

    if not EMAIL_PATTERN.match(cleaned_email):
        raise ValidationError(
            "Please provide a valid email address"
        )

    return cleaned_email


def _validate_password(password):

    if not isinstance(password, str) or not password:
        raise ValidationError("Password is required")

    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(
            "Password must be at least "
            f"{MIN_PASSWORD_LENGTH} characters long"
        )

    return password


# ---- Account operations ------------------------------------- #

def create_account(
    name,
    email,
    password,
    role=DEFAULT_ROLE
):
    """Validate the input and persist a new account."""

    if not isinstance(name, str) or not name.strip():
        raise ValidationError("Name is required")

    return user_service.create_user(
        name=name,
        email=_validate_email(email),
        password=_validate_password(password),
        role=normalize_role(role)
    )


def register_user(data):
    """
    Create a standard USER account from a registration payload.

    The role is always forced to USER: administrator accounts
    are provisioned with backend/seed_admin.py so the role can
    never be self-assigned through the public endpoint.
    """

    if not isinstance(data, dict) or not data:
        raise ValidationError(
            "Request body must contain account "
            "details as JSON"
        )

    return create_account(
        name=data.get("name"),
        email=data.get("email"),
        password=data.get("password"),
        role=DEFAULT_ROLE
    )


def authenticate(email, password):
    """Return the matching account or raise 401."""

    if (
        not isinstance(email, str)
        or not isinstance(password, str)
        or not email.strip()
        or not password
    ):
        raise ValidationError(
            "Email and password are required"
        )

    user = user_service.get_user_by_email(email)

    # The same message covers an unknown email and a wrong
    # password so the endpoint does not reveal which emails are
    # registered.
    if user is None or not user.check_password(password):
        raise UnauthorizedError(
            "Incorrect email or password"
        )

    return user


def get_authenticated_user(user_id):
    """Load the account behind a validated token."""

    return user_service.get_user(user_id)


def build_session(user):
    """Token + account payload returned to the frontend."""

    return {
        "token": create_token(user),
        "user": user.to_dict()
    }


def ensure_default_admin():
    """
    Create the initial ADMIN account when the database does not
    contain one yet.

    Controlled by config.config.SEED_DEFAULT_ADMIN so it can be
    switched off in a production deployment.
    """

    if not SEED_DEFAULT_ADMIN:
        return None

    if user_service.count_users_by_role("ADMIN") > 0:
        return None

    existing = user_service.get_user_by_email(
        DEFAULT_ADMIN_EMAIL
    )

    if existing is not None:

        # An account already uses the configured email but is
        # not an administrator. Promote it instead of failing.
        return user_service.update_user_role(
            existing.id,
            "ADMIN"
        )

    return user_service.create_user(
        name=DEFAULT_ADMIN_NAME,
        email=DEFAULT_ADMIN_EMAIL,
        password=DEFAULT_ADMIN_PASSWORD,
        role="ADMIN"
    )


