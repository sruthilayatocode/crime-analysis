"""
Authentication routes.

Endpoints:
    POST /api/auth/register - create a standard USER account
    POST /api/auth/login    - exchange credentials for a token
    GET  /api/auth/me       - current account for a token
    POST /api/auth/logout   - client-side token discard
"""

from flask import Blueprint, g, jsonify, request

from services import auth_service

from utils.decorators import token_required


auth_bp = Blueprint("auth", __name__)


@auth_bp.route(
    "/api/auth/register",
    methods=["POST"]
)
def register():
    """Create a standard USER account."""

    account_data = request.get_json(
        silent=True
    )

    user = auth_service.register_user(
        account_data
    )

    session_data = auth_service.build_session(
        user
    )

    return jsonify({
        "success": True,
        "message": "Account created successfully",
        "token": session_data["token"],
        "user": session_data["user"]
    }), 201


@auth_bp.route(
    "/api/auth/login",
    methods=["POST"]
)
def login():
    """Exchange credentials for a signed token."""

    credentials = request.get_json(
        silent=True
    ) or {}

    user = auth_service.authenticate(
        credentials.get("email"),
        credentials.get("password")
    )

    session_data = auth_service.build_session(
        user
    )

    return jsonify({
        "success": True,
        "message": "Signed in successfully",
        "token": session_data["token"],
        "user": session_data["user"]
    })


@auth_bp.route(
    "/api/auth/me",
    methods=["GET"]
)
@token_required
def current_user():
    """Return the account behind the supplied token."""

    return jsonify({
        "success": True,
        "user": g.current_user.to_dict()
    })


@auth_bp.route(
    "/api/auth/logout",
    methods=["POST"]
)
def logout():
    """
    Tokens are stateless, so signing out simply means the
    frontend discards its copy of the token.
    """

    return jsonify({
        "success": True,
        "message": "Signed out successfully"
    })
