"""
User service layer.

Data access for account records. Mirrors the layering used by
crime_service -> data_service so routes never touch the model
directly.
"""

from services.errors import (
    ConflictError,
    NotFoundError,
    ValidationError,
)


# Roles must stay in sync with models.user.VALID_ROLES.
VALID_ROLES = ("USER", "ADMIN")


def _user_model():
    """Import lazily so the model is loaded inside an app context."""

    from models.user import User

    return User


def list_users():
    """Return every account, passwords excluded."""

    User = _user_model()

    users = (
        User.query
        .order_by(User.id)
        .all()
    )

    return [
        user.to_dict()
        for user in users
    ]


def count_users_by_role(role):
    """Number of accounts holding the given role."""

    User = _user_model()

    return (
        User.query
        .filter_by(role=(role or "").upper())
        .count()
    )


def get_user(user_id):
    """Return one account record or raise 404."""

    from database import db

    User = _user_model()

    user = db.session.get(
        User,
        user_id
    )

    if user is None:
        raise NotFoundError(
            f"User {user_id} was not found"
        )

    return user


def get_user_by_email(email):
    """Return an account for the given email, or None."""

    if not email:
        return None

    User = _user_model()

    return (
        User.query
        .filter_by(email=str(email).strip().lower())
        .first()
    )


def create_user(
    name,
    email,
    password,
    role="USER"
):
    """
    Persist a new account.

    Callers are expected to validate the input first (see
    services.auth_service); this function only guards against
    duplicate email addresses.
    """

    from database import db

    User = _user_model()

    normalized_email = str(email).strip().lower()

    if get_user_by_email(normalized_email) is not None:
        raise ConflictError(
            "An account with this email already exists"
        )

    normalized_role = str(role).strip().upper() or "USER"

    if normalized_role not in VALID_ROLES:
        raise ValidationError(
            "role must be one of: "
            + ", ".join(VALID_ROLES)
        )

    user = User(
        name=str(name).strip(),
        email=normalized_email,
        role=normalized_role
    )

    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return user


def update_user_role(user_id, role):
    """Change the role of an existing account."""

    from database import db

    normalized_role = str(role).strip().upper()

    if normalized_role not in VALID_ROLES:
        raise ValidationError(
            "role must be one of: "
            + ", ".join(VALID_ROLES)
        )

    user = get_user(user_id)

    user.role = normalized_role

    db.session.commit()

    return user


def delete_user(user_id):
    """Remove an account."""

    from database import db

    user = get_user(user_id)

    db.session.delete(user)
    db.session.commit()

    return {
        "id": user_id,
        "deleted": True
    }
