import os
import time
from functools import wraps
import jwt
from flask import request, jsonify, g
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from models.user import User

JWT_SECRET_KEY = os.getenv("JWT_SECRET") or os.getenv("JWT_SECRET_KEY", "crimesense-secret-jwt-key-2026-super-secure")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRES = 86400  # 24 hours
REFRESH_TOKEN_EXPIRES = 30 * 86400  # 30 days

# Rate limiting simple in-memory tracker
RATE_LIMIT_STORE = {}  # key: ip_or_email, value: list of timestamps


def check_rate_limit(key: str, max_requests: int = 10, window_seconds: int = 60) -> bool:
    """Returns True if request is allowed, False if rate limit exceeded."""
    now = time.time()
    timestamps = RATE_LIMIT_STORE.get(key, [])
    timestamps = [ts for ts in timestamps if now - ts < window_seconds]
    if len(timestamps) >= max_requests:
        RATE_LIMIT_STORE[key] = timestamps
        return False
    timestamps.append(now)
    RATE_LIMIT_STORE[key] = timestamps
    return True


def generate_access_token(user: User) -> str:
    payload = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "name": user.name,
        "type": "access",
        "exp": int(time.time()) + ACCESS_TOKEN_EXPIRES,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def generate_refresh_token(user: User) -> str:
    payload = {
        "user_id": user.id,
        "type": "refresh",
        "exp": int(time.time()) + REFRESH_TOKEN_EXPIRES,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str):
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None


def get_token_from_request():
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1]
    return request.cookies.get("access_token")


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_request()
        if not token:
            return jsonify({"success": False, "message": "Authentication required. Token missing."}), 401
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            return jsonify({"success": False, "message": "Invalid or expired access token."}), 401
        user = User.query.get(payload.get("user_id"))
        if not user or not user.is_active:
            return jsonify({"success": False, "message": "User account is inactive or deleted."}), 401
        g.current_user = user
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if getattr(g, "current_user", None) is None or g.current_user.role != "admin":
            return jsonify({"success": False, "message": "Access denied. Admin privileges required."}), 403
        return f(*args, **kwargs)
    return decorated


def verify_google_id_token(token_str: str):
    """
    Verify Google ID token with google.oauth2.id_token.verify_oauth2_token.
    Validates:
    - Audience == GOOGLE_CLIENT_ID (when configured)
    - Issuer in ('accounts.google.com', 'https://accounts.google.com')
    - Expiry
    - email_verified == True
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID") or os.getenv("VITE_GOOGLE_CLIENT_ID")
    if client_id:
        client_id = client_id.strip()

    try:
        idinfo = id_token.verify_oauth2_token(
            token_str,
            google_requests.Request(),
            audience=client_id if client_id else None
        )
    except Exception as e:
        # Fallback to tokeninfo endpoint if certificate refresh requires HTTP
        try:
            import requests
            resp = requests.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={token_str}", timeout=5)
            if resp.status_code == 200:
                idinfo = resp.json()
            else:
                raise ValueError(f"Google ID token verification failed: {e}")
        except Exception:
            raise ValueError(f"Google ID token verification failed: {e}")

    # 1. Issuer check
    iss = idinfo.get("iss")
    if iss not in ["accounts.google.com", "https://accounts.google.com"]:
        raise ValueError(f"Invalid Google token issuer: '{iss}'")

    # 2. Audience check (if client_id configured)
    if client_id:
        aud = idinfo.get("aud")
        if aud != client_id:
            raise ValueError(f"Google Client ID audience mismatch: expected '{client_id}', got '{aud}'")

    # 3. Expiry check
    exp = idinfo.get("exp")
    if exp and float(exp) < time.time():
        raise ValueError("Google ID token has expired. Please sign in again.")

    # 4. Email verification check
    email_verified = idinfo.get("email_verified")
    if email_verified not in [True, "true", "True", 1]:
        raise ValueError("Google account email is not verified. Please verify your email with Google first.")

    google_id = idinfo.get("sub")
    email = (idinfo.get("email") or "").strip().lower()
    if not email or not google_id:
        raise ValueError("Google ID token is missing required user email or ID.")

    name = idinfo.get("name") or (email.split("@")[0] if email else "Google User")
    avatar_url = idinfo.get("picture")

    return {
        "google_id": google_id,
        "email": email,
        "name": name,
        "avatar_url": avatar_url,
    }


def create_account(name, email, password, role="USER"):
    from database import db
    from models.user import User
    from services.errors import ConflictError, ValidationError
    if not email:
        raise ValidationError("Email is required")
    if not password:
        raise ValidationError("Password is required")
    existing = User.query.filter(User.email == email.lower().strip()).first()
    if existing:
        raise ConflictError("An account with this email already exists")
    user = User(
        name=name.strip(),
        email=email.lower().strip(),
        role=role.lower() if role else "user",
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def register_user(data):
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    role = data.get("role") or "USER"
    return create_account(name, email, password, role)


def authenticate(email, password):
    from models.user import User
    from services.errors import UnauthorizedError, ValidationError
    if not email or not password:
        raise ValidationError("Email and password are required")
    user = User.query.filter(User.email == email.lower().strip()).first()
    if not user or not user.check_password(password):
        raise UnauthorizedError("Invalid email or password")
    return user


def create_token(user, expires_in_hours=None):
    return generate_access_token(user)


def build_session(user):
    token = generate_access_token(user)
    return {
        "token": token,
        "access_token": token,
        "user": user.to_dict() if hasattr(user, "to_dict") else {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }


def get_authenticated_user(user_id):
    from database import db
    from models.user import User
    return db.session.get(User, user_id)


