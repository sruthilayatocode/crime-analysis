"""
Authentication / authorisation decorators for API routes.

Usage:

    from utils.decorators import role_required, token_required

    @auth_bp.route("/api/auth/me", methods=["GET"])
    @token_required
    def current_user():
        return jsonify({"user": g.current_user.to_dict()})

    @user_bp.route("/api/users", methods=["GET"])
    @role_required("ADMIN")
    def list_accounts():
        ...

The token is read from the "Authorization: Bearer <token>"
header, with "X-Auth-Token" supported as a fallback.
"""

from functools import wraps

from flask import g, request

from services import auth_service

from services.errors import ForbiddenError


def _read_token():
    """Extract the raw token from the incoming request."""

    header = request.headers.get(
        "Authorization",
        ""
    )

    if header:

        parts = header.split(None, 1)

        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1].strip()

    return (
        request.headers.get(
            "X-Auth-Token",
            ""
        ).strip()
        or None
    )


def _resolve_user():
    """Validate the request token and load its account."""
    raw = _read_token()
    if not raw:
        from services.errors import UnauthorizedError
        raise UnauthorizedError("Authentication token is required")

    payload = auth_service.decode_token(raw)
    if not payload:
        from services.errors import UnauthorizedError
        raise UnauthorizedError("Invalid or expired authentication token")

    user_id = payload.get("user_id") or payload.get("uid") or payload.get("sub")
    user = auth_service.get_authenticated_user(user_id)
    if not user:
        from services.errors import UnauthorizedError
        raise UnauthorizedError("User account not found")

    return user



def _current_user():
    """Account for this request, resolving it based on request token."""

    token = _read_token()

    if getattr(g, "_auth_token", None) != token or not hasattr(g, "current_user"):
        g.current_user = _resolve_user()
        g._auth_token = token

    return g.current_user


def token_required(view):
    """Require a valid token; exposes g.current_user."""

    @wraps(view)
    def wrapper(*args, **kwargs):

        _current_user()

        return view(*args, **kwargs)

    return wrapper


def role_required(*allowed_roles):
    """
    Require an authenticated account holding one of the given
    roles. Also works on its own (it resolves the account when
    token_required has not already done so).
    """

    allowed = tuple(
        str(role).strip().upper()
        for role in allowed_roles
        if str(role).strip()
    )

    def decorator(view):

        @wraps(view)
        def wrapper(*args, **kwargs):

            user = _current_user()

            current_role = (
                user.role or ""
            ).strip().upper()

            if allowed and current_role not in allowed:

                raise ForbiddenError(
                    "This action requires one of the "
                    "following roles: "
                    + ", ".join(allowed)
                )

            return view(*args, **kwargs)

        return wrapper

    return decorator
