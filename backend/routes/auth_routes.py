from datetime import datetime
from flask import Blueprint, request, jsonify, g, make_response
from database import db
from models.user import User
from services.auth_service import (
    generate_access_token,
    generate_refresh_token,
    decode_token,
    login_required,
    check_rate_limit,
    verify_google_id_token,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def build_auth_response(user: User, status_code=200, message="Authentication successful", extra_data=None):
    access_token = generate_access_token(user)
    refresh_token = generate_refresh_token(user)

    user.last_login_at = datetime.utcnow()
    db.session.commit()

    resp_data = {
        "success": True,
        "message": message,
        "token": access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict(),
        "role": user.role,
    }
    if extra_data:
        resp_data.update(extra_data)

    response = make_response(jsonify(resp_data), status_code)
    response.set_cookie("access_token", access_token, httponly=True, samesite="Lax", max_age=86400)
    response.set_cookie("refresh_token", refresh_token, httponly=True, samesite="Lax", max_age=30 * 86400)
    return response


@auth_bp.route("/signup", methods=["POST"])
@auth_bp.route("/register", methods=["POST"])
def signup():
    ip_addr = request.remote_addr or "127.0.0.1"
    if not check_rate_limit(f"signup_{ip_addr}", max_requests=10, window_seconds=60):
        return jsonify({"success": False, "message": "Too many signup attempts. Please try again later."}), 429

    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"success": False, "message": "Name, email, and password are required."}), 400

    if len(password) < 6:
        return jsonify({"success": False, "message": "Password must be at least 6 characters long."}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"success": False, "message": "An account with this email already exists."}), 400

    if request.path.endswith("/register"):
        role = data.get("role") or "USER"
    else:
        role = data.get("role") or "user"

    new_user = User(name=name, email=email, role=role)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return build_auth_response(new_user, status_code=201, message="Account created successfully.")



@auth_bp.route("/login", methods=["POST"])
def login():
    ip_addr = request.remote_addr or "127.0.0.1"
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    rate_key = f"login_{ip_addr}_{email}"
    if not check_rate_limit(rate_key, max_requests=10, window_seconds=60):
        return jsonify({"success": False, "message": "Too many login attempts. Please wait 1 minute before retrying."}), 429

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required."}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"success": False, "message": "Invalid email or password."}), 401

    if not user.is_active:
        return jsonify({"success": False, "message": "Your account has been deactivated. Please contact administrator."}), 403

    return build_auth_response(user, status_code=200, message="Login successful.")


@auth_bp.route("/google", methods=["POST"])
def google_auth():
    """
    POST /api/auth/google
    Authenticate or register user with a verified Google ID token credential.
    """
    data = request.get_json() or {}
    token_str = data.get("credential") or data.get("id_token") or data.get("google_token")

    if not token_str:
        return jsonify({
            "success": False,
            "message": "Google credential (ID token) is required."
        }), 400

    try:
        g_info = verify_google_id_token(token_str)
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Google authentication failed: {str(e)}"
        }), 400

    google_id = g_info["google_id"]
    email = g_info["email"]

    # 1. Find user by google_id
    user = User.query.filter_by(google_id=google_id).first()

    # 2. Else find user by email (link Google account to existing user)
    if not user:
        user = User.query.filter_by(email=email).first()
        if user:
            user.google_id = google_id
            if g_info.get("avatar_url") and not user.avatar_url:
                user.avatar_url = g_info["avatar_url"]
        else:
            # 3. Else create a new user
            user = User(
                name=g_info["name"],
                email=email,
                google_id=google_id,
                avatar_url=g_info.get("avatar_url"),
                role="user",
                is_active=True,
            )
            db.session.add(user)
    else:
        # Existing user by google_id: update avatar if present
        if g_info.get("avatar_url") and not user.avatar_url:
            user.avatar_url = g_info["avatar_url"]

    # Reject inactive/deactivated users
    if not user.is_active:
        return jsonify({
            "success": False,
            "message": "Your account has been deactivated. Please contact support or administrator."
        }), 403

    db.session.commit()

    # Determine post-login redirect path
    from models.sos_contact import SOSContact
    sos_count = SOSContact.query.filter_by(user_id=user.id).count() if user.id else 0
    needs_onboarding = bool(user.role == "user" and sos_count == 0)

    if user.role == "admin":
        redirect_url = "/admin"
    elif needs_onboarding:
        redirect_url = "/app"  # Modal prompts for onboarding or /onboarding
    else:
        redirect_url = "/app"

    return build_auth_response(
        user,
        status_code=200,
        message="Google authentication successful.",
        extra_data={
            "redirect_url": redirect_url,
            "needs_onboarding": needs_onboarding,
            "role": user.role,
        }
    )



@auth_bp.route("/me", methods=["GET"])
@login_required
def get_me():
    return jsonify({
        "success": True,
        "user": g.current_user.to_dict()
    })


@auth_bp.route("/logout", methods=["POST"])
def logout():
    response = make_response(jsonify({"success": True, "message": "Logged out successfully."}))
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response


@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    data = request.get_json() or {}
    refresh_token = data.get("refresh_token") or request.cookies.get("refresh_token")
    if not refresh_token:
        return jsonify({"success": False, "message": "Refresh token missing."}), 401

    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        return jsonify({"success": False, "message": "Invalid or expired refresh token."}), 401

    user = User.query.get(payload.get("user_id"))
    if not user or not user.is_active:
        return jsonify({"success": False, "message": "User not active."}), 401

    new_access_token = generate_access_token(user)
    response = make_response(jsonify({"success": True, "token": new_access_token, "user": user.to_dict()}))
    response.set_cookie("access_token", new_access_token, httponly=True, samesite="Lax", max_age=86400)
    return response
