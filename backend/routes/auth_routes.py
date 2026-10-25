import re
import os
from datetime import datetime, timedelta
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
from services.email_service import email_service, generate_secure_token, hash_token

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


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

    if not EMAIL_REGEX.match(email):
        return jsonify({"success": False, "message": "Please enter a valid email address format."}), 400

    if len(password) < 6:
        return jsonify({"success": False, "message": "Password must be at least 6 characters long."}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"success": False, "message": "An account with this email already exists."}), 400

    # Public registration strictly assigns citizen/user role; admin cannot be self-assigned
    if request.path.endswith("/register"):
        role = "USER"
    else:
        role = "user"

    raw_token, token_hash = generate_secure_token()
    new_user = User(
        name=name,
        email=email,
        role=role,
        is_verified=False,
        verification_token_hash=token_hash,
        verification_token_expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    # Dispatch verification email (or log link in development mode)
    email_result = email_service.send_verification_email(new_user.email, new_user.name, raw_token)

    extra_data = {
        "email_delivery": email_result,
        "is_verified": False,
        "verification_notice": "A verification link has been sent to your email address."
    }

    return build_auth_response(new_user, status_code=201, message="Account created successfully.", extra_data=extra_data)


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

    # Check optional strict verification policy (default: False for local dev convenience)
    require_verified = os.getenv("REQUIRE_EMAIL_VERIFICATION", "false").strip().lower() in ("true", "1", "yes")
    if require_verified and not user.is_verified:
        return jsonify({
            "success": False,
            "message": "Please verify your email address before logging in. Check your inbox for the verification link.",
            "requires_verification": True
        }), 403

    return build_auth_response(user, status_code=200, message="Login successful.")


@auth_bp.route("/verify-email", methods=["GET", "POST"])
def verify_email():
    """Verify user email via single-use expiring cryptographic token."""
    ip_addr = request.remote_addr or "127.0.0.1"
    if not check_rate_limit(f"verify_{ip_addr}", max_requests=20, window_seconds=60):
        return jsonify({"success": False, "message": "Too many verification requests. Please try again later."}), 429

    token = request.args.get("token")
    if not token and request.is_json:
        token = (request.get_json() or {}).get("token")

    if not token:
        return jsonify({"success": False, "message": "Verification token is required."}), 400

    token_hash = hash_token(token)
    user = User.query.filter_by(verification_token_hash=token_hash).first()

    if not user:
        return jsonify({
            "success": False,
            "message": "Invalid, expired, or already used verification token."
        }), 400

    if user.verification_token_expires_at and datetime.utcnow() > user.verification_token_expires_at:
        return jsonify({
            "success": False,
            "message": "Verification token has expired. Please request a new verification link."
        }), 400

    user.is_verified = True
    user.verification_token_hash = None
    user.verification_token_expires_at = None
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Email address verified successfully! You now have full access to CrimeSense.",
        "user": user.to_dict()
    }), 200


@auth_bp.route("/resend-verification", methods=["POST"])
def resend_verification():
    """Resend email verification link with rate limiting."""
    ip_addr = request.remote_addr or "127.0.0.1"
    if not check_rate_limit(f"resend_verify_{ip_addr}", max_requests=5, window_seconds=300):
        return jsonify({"success": False, "message": "Too many resend attempts. Please wait 5 minutes before trying again."}), 429

    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()

    if not email:
        return jsonify({"success": False, "message": "Email address is required."}), 400

    user = User.query.filter_by(email=email).first()
    if user and not user.is_verified:
        raw_token, token_hash = generate_secure_token()
        user.verification_token_hash = token_hash
        user.verification_token_expires_at = datetime.utcnow() + timedelta(hours=24)
        db.session.commit()
        email_service.send_verification_email(user.email, user.name, raw_token)

    # Return uniform message to avoid revealing account existence
    return jsonify({
        "success": True,
        "message": "If an unverified account exists for this email, a new verification link has been sent."
    }), 200


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    """Initiate password recovery workflow by emailing a single-use reset token."""
    ip_addr = request.remote_addr or "127.0.0.1"
    if not check_rate_limit(f"forgot_pw_{ip_addr}", max_requests=5, window_seconds=300):
        return jsonify({"success": False, "message": "Too many password reset requests. Please wait 5 minutes before retrying."}), 429

    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()

    if not email:
        return jsonify({"success": False, "message": "Email address is required."}), 400

    user = User.query.filter_by(email=email).first()
    if user and user.is_active:
        raw_token, token_hash = generate_secure_token()
        user.reset_token_hash = token_hash
        user.reset_token_expires_at = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
        email_service.send_password_reset_email(user.email, user.name, raw_token)

    # Generic response prevents account enumeration attacks
    return jsonify({
        "success": True,
        "message": "If that email address is registered, a password reset link has been sent to your inbox."
    }), 200


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    """Reset user password using a verified, single-use token."""
    ip_addr = request.remote_addr or "127.0.0.1"
    if not check_rate_limit(f"reset_pw_{ip_addr}", max_requests=10, window_seconds=60):
        return jsonify({"success": False, "message": "Too many reset attempts. Please try again later."}), 429

    data = request.get_json() or {}
    token = data.get("token", "").strip()
    new_password = data.get("password", "")

    if not token or not new_password:
        return jsonify({"success": False, "message": "Token and new password are required."}), 400

    if len(new_password) < 6:
        return jsonify({"success": False, "message": "New password must be at least 6 characters long."}), 400

    token_hash = hash_token(token)
    user = User.query.filter_by(reset_token_hash=token_hash).first()

    if not user:
        return jsonify({
            "success": False,
            "message": "Invalid, expired, or already used password reset link."
        }), 400

    if user.reset_token_expires_at and datetime.utcnow() > user.reset_token_expires_at:
        return jsonify({
            "success": False,
            "message": "Password reset link has expired. Please request a new one."
        }), 400

    user.set_password(new_password)
    user.reset_token_hash = None
    user.reset_token_expires_at = None
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Your password has been successfully reset. You can now log in with your new password."
    }), 200


@auth_bp.route("/google", methods=["POST"])
def google_auth():
    """
    POST /api/auth/google
    Authenticate or register user with a verified Google ID token credential.
    """
    ip_addr = request.remote_addr or "127.0.0.1"
    if not check_rate_limit(f"google_auth_{ip_addr}", max_requests=20, window_seconds=60):
        return jsonify({
            "success": False,
            "message": "Too many Google sign-in attempts. Please try again later."
        }), 429

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
            # Prevent account takeover if the existing user is already linked to a different Google account
            if user.google_id and user.google_id != google_id:
                return jsonify({
                    "success": False,
                    "message": "This email account is already associated with a different Google account."
                }), 409

            # Prevent takeover of administrator accounts via Google sign-in
            if str(user.role or "").strip().lower() == "admin":
                return jsonify({
                    "success": False,
                    "message": "Administrator accounts cannot be linked via Google Sign-In. Please sign in using your administrator password."
                }), 403

            # Link Google account to existing citizen account and mark email verified
            user.google_id = google_id
            user.is_verified = True
            if g_info.get("avatar_url") and not user.avatar_url:
                user.avatar_url = g_info["avatar_url"]
        else:
            # 3. Create a new user with normal citizen role (never admin)
            user = User(
                name=g_info["name"],
                email=email,
                google_id=google_id,
                avatar_url=g_info.get("avatar_url"),
                role="user",
                is_active=True,
                is_verified=True,
            )
            db.session.add(user)
    else:
        # Existing user matched by google_id: update avatar if present
        if g_info.get("avatar_url") and not user.avatar_url:
            user.avatar_url = g_info["avatar_url"]
        user.is_verified = True

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
    user_role = str(user.role or "").strip().lower()
    needs_onboarding = bool(user_role == "user" and sos_count == 0)

    if user_role == "admin":
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
