import sys
import os
from pathlib import Path
from flask import Flask, jsonify, request
from dotenv import load_dotenv

load_dotenv()

# Ensure backend directory has top priority on sys.path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) in sys.path:
    sys.path.remove(str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR))

# Ensure repository root is on sys.path for top-level ml and config packages
PROJECT_ROOT = BACKEND_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))


from database import db
from models.crime import Crime
from models.user import User

from routes.crime_routes import crime_bp
from routes.alert_routes import alert_bp
from routes.auth_routes import auth_bp
from routes.user_routes import user_bp
from routes.sos_routes import sos_bp
from routes.share_routes import share_bp
from routes.admin_routes import admin_bp
from models.audit_log import AuditLog
from services.auth_service import verify_google_id_token


import os


def seed_admin_user(app_instance):
    """Seed default admin user and demo citizen user from environment variables if none exists."""
    with app_instance.app_context():
        admin_email = os.getenv("ADMIN_EMAIL", "admin@crimesense.com").strip().lower()
        admin_password = os.getenv("ADMIN_PASSWORD", "Admin@123")
        admin_name = os.getenv("ADMIN_NAME", "System Administrator")

        admin_user = User.query.filter_by(role="admin").first()
        if not admin_user:
            existing_user = User.query.filter_by(email=admin_email).first()
            if existing_user:
                existing_user.role = "admin"
                existing_user.set_password(admin_password)
            else:
                new_admin = User(
                    name=admin_name,
                    email=admin_email,
                    role="admin",
                    is_active=True
                )
                new_admin.set_password(admin_password)
                db.session.add(new_admin)
            db.session.commit()
            print(f"[Seed] Admin user verified: {admin_email}")

        # Demo Citizen user (for login quick-fill / demo evaluation)
        demo_user_email = os.getenv("DEMO_USER_EMAIL", "user@crimesense.com").strip().lower()
        demo_user_password = os.getenv("DEMO_USER_PASSWORD", "User@123")
        demo_user_name = os.getenv("DEMO_USER_NAME", "Demo Citizen User")

        demo_user = User.query.filter_by(email=demo_user_email).first()
        if not demo_user:
            new_citizen = User(
                name=demo_user_name,
                email=demo_user_email,
                role="user",
                is_active=True
            )
            new_citizen.set_password(demo_user_password)
            db.session.add(new_citizen)
            db.session.commit()
            print(f"[Seed] Demo citizen user verified: {demo_user_email}")


app = Flask(__name__)

from services.errors import ApiError


@app.errorhandler(ApiError)
def handle_api_error(error):
    """Handle all ApiError subclasses and return consistent JSON responses."""
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.errorhandler(404)
def handle_404(error):
    """Ensure any missing /api endpoints return JSON rather than HTML."""
    if request.path.startswith("/api"):
        return jsonify({
            "success": False,
            "message": f"Endpoint not found: {request.path}",
            "status_code": 404
        }), 404
    return jsonify({"error": "Not Found", "message": "Resource not found."}), 404


@app.errorhandler(500)
def handle_500(error):
    """Ensure internal server errors on /api endpoints return structured JSON."""
    if request.path.startswith("/api"):
        return jsonify({
            "success": False,
            "message": "Internal server error. Please try again later.",
            "status_code": 500
        }), 500
    return jsonify({"error": "Internal Server Error"}), 500



# --------------------------------------------------------------------------- #
# Database configuration (Supports DATABASE_URL or SQLite)
# --------------------------------------------------------------------------- #
custom_db_url = os.getenv("DATABASE_URL", "").strip()

if custom_db_url:
    # Fix Heroku/Render postgres:// URI to postgresql:// for SQLAlchemy
    if custom_db_url.startswith("postgres://"):
        custom_db_url = custom_db_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = custom_db_url
    print(f"[Database] Using cloud DATABASE_URL: {custom_db_url.split('@')[-1] if '@' in custom_db_url else 'configured'}")
else:
    BASE_DIR = Path(__file__).resolve().parent
    DB_DIR = BASE_DIR / "instance"
    DB_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH = (DB_DIR / "crimesense.db").resolve()
    print(f"[Database] SQLite database path: {DB_PATH.as_posix()}")

    if not DB_PATH.exists():
        print(f"[Database] SQLite DB file '{DB_PATH}' will be initialized automatically.")

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + DB_PATH.as_posix()
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "connect_args": {
            "timeout": 30,
            "check_same_thread": False,
        }
    }

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False



# --------------------------------------------------------------------------- #
# CORS & Security Headers
# --------------------------------------------------------------------------- #
ALLOWED_ORIGINS = {
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
}
env_origins = os.getenv("CORS_ALLOWED_ORIGINS", "").strip()
if env_origins:
    ALLOWED_ORIGINS.update([o.strip() for o in env_origins.split(",") if o.strip()])


@app.before_request
def _cors_preflight():
    if request.method == "OPTIONS":
        resp = jsonify({})
        resp.status_code = 204
        origin = request.headers.get("Origin")
        is_allowed = (
            origin in ALLOWED_ORIGINS
            or (origin and (origin.endswith(".web.app") or origin.endswith(".firebaseapp.com")))
            or os.getenv("CORS_ALLOW_ALL", "").lower() in ("true", "1")
        )
        if is_allowed and origin:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Credentials"] = "true"
            resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            resp.headers["Access-Control-Max-Age"] = "600"
            resp.headers["Vary"] = "Origin"
        return resp


@app.after_request
def _apply_security_and_cors_headers(response):
    origin = request.headers.get("Origin")
    is_allowed = (
        origin in ALLOWED_ORIGINS
        or (origin and (origin.endswith(".web.app") or origin.endswith(".firebaseapp.com")))
        or os.getenv("CORS_ALLOW_ALL", "").lower() in ("true", "1")
    )
    if is_allowed and origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, PUT, DELETE, OPTIONS"
        )
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type, Authorization"
        )
        response.headers["Access-Control-Max-Age"] = "600"
        response.headers["Vary"] = "Origin"

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    if os.getenv("FLASK_ENV") == "production" or request.is_secure:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response


# Connect SQLAlchemy with the Flask application
db.init_app(app)


def ensure_schema_migrations():
    """Ensure newly introduced columns exist in SQLite database."""
    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
            # Check sos_events table columns
            res = conn.execute(text("PRAGMA table_info(sos_events)")).fetchall()
            existing_cols = [r[1] for r in res]
            if "accuracy" not in existing_cols:
                conn.execute(text("ALTER TABLE sos_events ADD COLUMN accuracy REAL"))
            if "live_tracking_until" not in existing_cols:
                conn.execute(text("ALTER TABLE sos_events ADD COLUMN live_tracking_until DATETIME"))
            if "admin_notes" not in existing_cols:
                conn.execute(text("ALTER TABLE sos_events ADD COLUMN admin_notes TEXT"))

            # Check saved_locations table columns
            res_saved = conn.execute(text("PRAGMA table_info(saved_locations)")).fetchall()
            saved_cols = [r[1] for r in res_saved]
            if "is_pinned" not in saved_cols:
                conn.execute(text("ALTER TABLE saved_locations ADD COLUMN is_pinned BOOLEAN DEFAULT 0"))
            if "last_checked_at" not in saved_cols:
                conn.execute(text("ALTER TABLE saved_locations ADD COLUMN last_checked_at DATETIME"))

            # Check shared_links table columns
            res_shared = conn.execute(text("PRAGMA table_info(shared_links)")).fetchall()
            shared_cols = [r[1] for r in res_shared]
            if "label" not in shared_cols:
                conn.execute(text("ALTER TABLE shared_links ADD COLUMN label VARCHAR(100)"))
            if "address" not in shared_cols:
                conn.execute(text("ALTER TABLE shared_links ADD COLUMN address VARCHAR(300)"))
            if "accuracy" not in shared_cols:
                conn.execute(text("ALTER TABLE shared_links ADD COLUMN accuracy REAL"))
            if "zone" not in shared_cols:
                conn.execute(text("ALTER TABLE shared_links ADD COLUMN zone VARCHAR(20) DEFAULT 'green'"))
            if "is_revoked" not in shared_cols:
                conn.execute(text("ALTER TABLE shared_links ADD COLUMN is_revoked BOOLEAN DEFAULT 0"))
            if "updated_at" not in shared_cols:
                conn.execute(text("ALTER TABLE shared_links ADD COLUMN updated_at DATETIME"))

            # Ensure indexes on (latitude, longitude), user_id, and dates
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_crimes_lat_lng ON crimes (latitude, longitude)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_crimes_published_date ON crimes (published_date)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_crimes_crime_date ON crimes (crime_date)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_loc_lat_lng ON user_locations (latitude, longitude)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_saved_loc_lat_lng ON saved_locations (latitude, longitude)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sos_event_lat_lng ON sos_events (latitude, longitude)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_shared_link_lat_lng ON shared_links (latitude, longitude)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_alerts_lat_lng ON alerts (latitude, longitude)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_alerts_user_id ON alerts (user_id)"))

            # Check users table columns for verification and password reset
            res_users = conn.execute(text("PRAGMA table_info(users)")).fetchall()
            user_cols = [r[1] for r in res_users]
            if "is_verified" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT 0"))
                conn.execute(text("UPDATE users SET is_verified = 1"))
            if "verification_token_hash" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN verification_token_hash VARCHAR(64)"))
            if "verification_token_expires_at" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN verification_token_expires_at DATETIME"))
            if "reset_token_hash" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN reset_token_hash VARCHAR(64)"))
            if "reset_token_expires_at" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN reset_token_expires_at DATETIME"))

            # Ensure compatibility view for audit_log -> audit_logs
            conn.execute(text("CREATE VIEW IF NOT EXISTS audit_log AS SELECT * FROM audit_logs"))

            conn.commit()
    except Exception as e:
        print(f"[Migration] Schema check note: {e}")



# Create database tables automatically (idempotent: never drops existing data)
with app.app_context():
    db.create_all()
    ensure_schema_migrations()
    # Seed initial admin user if not present
    seed_admin_user(app)



# Register API route blueprints
app.register_blueprint(crime_bp)
app.register_blueprint(alert_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(sos_bp)
app.register_blueprint(share_bp)
app.register_blueprint(admin_bp)

# Start Red Zone Inactivity Monitoring background daemon
try:
    from services.red_zone_scheduler import start_red_zone_scheduler
    start_red_zone_scheduler(app, interval_seconds=30)
except Exception as e:
    print(f"[Scheduler] Could not start background scheduler: {e}")




@app.route("/")
def home():
    return jsonify({
        "message": "Welcome to CrimeSense Backend",
        "status": "Backend is running successfully"
    })


@app.route("/api/health")
def health_check():
    from datetime import datetime, timezone
    from sqlalchemy import text
    from models.crime import Crime
    from models.user import User
    from models.sos_event import SOSEvent

    server_time = datetime.now(timezone.utc).isoformat()
    try:
        # Perform real SELECT 1 query against SQLite database
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1")).fetchone()

        crimes_count = Crime.query.count()
        users_count = User.query.count()
        sos_events_count = SOSEvent.query.count()

        return jsonify({
            "status": "healthy",
            "service": "CrimeSense Backend",
            "db_connected": True,
            "crimes_count": crimes_count,
            "users_count": users_count,
            "sos_events_count": sos_events_count,
            "db_initialized": True,
            "server_time": server_time,
        }), 200

    except Exception as e:
        app.logger.error(f"Database health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "service": "CrimeSense Backend",
            "db_connected": False,
            "error": str(e),
            "db_initialized": False,
            "server_time": server_time,
        }), 503



@app.route("/api/project-info")
def project_info():
    return jsonify({
        "project_name": "CrimeSense",
        "description": (
            "AI-powered Crime Hotspot Analysis "
            "and Proximity Alert System"
        ),
        "features": [
            "Crime hotspot analysis",
            "Crime prediction",
            "Location-based risk analysis",
            "Proximity alerts",
            "Crime data visualization"
        ]
    })


@app.route("/api/system/info")
def system_info():
    """Return system information and operational status."""
    return jsonify({
        "success": True,
        "name": "CrimeSense API",
        "version": "1.0.0",
        "status": "online",
        "python_version": sys.version.split()[0],
        "database": "SQLite (SQLAlchemy)",
        "features": {
            "ml_hotspots": True,
            "proximity_alerts": True,
            "citizen_reporting": True,
            "admin_triage": True
        }
    }), 200


if __name__ == "__main__":
    app.run(debug=True)