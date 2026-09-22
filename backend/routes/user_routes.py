"""
Account management routes (administrators only).

Endpoints:
    GET   /api/users            - list every account
    PATCH /api/users/<id>/role  - change an account role
"""

from flask import Blueprint, g, jsonify, request

from services import auth_service, user_service

from services.errors import ValidationError

from utils.decorators import role_required


user_bp = Blueprint("user", __name__)


@user_bp.route("/api/users", methods=["GET"])
@role_required("ADMIN")
def list_users():
    """Return every account (passwords excluded)."""

    users = user_service.list_users()

    return jsonify({
        "success": True,
        "count": len(users),
        "data": users
    })


@user_bp.route(
    "/api/users/<int:user_id>/role",
    methods=["PATCH"]
)
@role_required("ADMIN")
def update_user_role(user_id):
    """Promote or demote an account."""

    payload = request.get_json(
        silent=True
    ) or {}

    requested_role = auth_service.normalize_role(
        payload.get("role")
    )

    # An administrator must not be able to lock themselves out.
    if user_id == g.current_user.id and requested_role != "ADMIN":
        raise ValidationError(
            "You cannot change your own role"
        )

    user = user_service.update_user_role(
        user_id,
        requested_role
    )

    return jsonify({
        "success": True,
        "message": "Account role updated successfully",
        "data": user.to_dict()
    })
