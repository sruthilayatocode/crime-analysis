"""
admin_routes.py
===============
Comprehensive Admin Management Endpoints for CrimeSense.
Guarded by @admin_required decorator.

Covers:
1. Overview & KPIs
2. Crime Data CRUD, Search, Filters, CSV Import / Export
3. Historical Trends & Multi-Year Analytics
4. User Management, Detail Drawer, Role/Status Toggles, Deletion
5. Live Map with Strict Privacy Filtering
6. Alerts & SOS Incident Management (Resolve, Notes)
7. Audit Log Stream
"""

import io
import csv
import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, g, Response, send_file
from sqlalchemy import func, or_, desc, asc

from database import db
from models.crime import Crime
from models.user import User
from models.user_settings import UserSettings
from models.user_location import UserLocation
from models.user_red_zone_state import UserRedZoneState
from models.sos_contact import SOSContact
from models.sos_event import SOSEvent
from models.saved_location import SavedLocation
from models.audit_log import AuditLog
from services.auth_service import admin_required
from services.zone_service import calculate_zone_risk

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def get_client_ip():
    """Extract client IP address."""
    return request.headers.get("X-Forwarded-For", request.remote_addr or "127.0.0.1").split(",")[0].strip()


# =========================================================================== #
# 1. OVERVIEW & KPIS
# =========================================================================== #

@admin_bp.route("/overview", methods=["GET"])
@admin_required
def get_admin_overview():
    """
    GET /api/admin/overview
    Returns aggregate KPIs, risk distributions, and recent statistics.
    """
    total_crimes = Crime.query.count()
    high_severity_crimes = Crime.query.filter(
        or_(
            Crime.severity.in_(["HIGH", "CRITICAL", "High", "Critical"]),
            Crime.risk_level.in_(["HIGH", "CRITICAL", "High", "Critical"]),
            Crime.severity_score >= 7.0
        )
    ).count()

    total_users = User.query.count()

    # Active users now (heartbeat or location within last 15 minutes)
    fifteen_min_ago = datetime.utcnow() - timedelta(minutes=15)
    active_users_now = UserRedZoneState.query.filter(
        UserRedZoneState.last_heartbeat_at >= fifteen_min_ago
    ).count()

    # Active SOS Events
    active_sos_count = SOSEvent.query.filter_by(status="active").count()

    # Red Zone Users
    red_zone_users_count = UserRedZoneState.query.filter(
        UserRedZoneState.zone == "red",
        UserRedZoneState.last_heartbeat_at >= fifteen_min_ago
    ).count()

    # Active Hotspots estimate (unique high risk localities)
    hotspots_count = db.session.query(func.count(func.distinct(Crime.locality))).filter(
        or_(
            Crime.severity.in_(["HIGH", "CRITICAL", "High", "Critical"]),
            Crime.risk_level.in_(["HIGH", "CRITICAL", "High", "Critical"]),
            Crime.severity_score >= 6.0
        )
    ).scalar() or 0

    # Crimes by type distribution
    type_counts = db.session.query(
        Crime.crime_type, func.count(Crime.id)
    ).group_by(Crime.crime_type).order_by(desc(func.count(Crime.id))).limit(8).all()
    crimes_by_type = [{"type": t[0] or "Other", "count": t[1]} for t in type_counts]

    # Severity breakdown
    severity_counts = db.session.query(
        func.coalesce(Crime.severity, Crime.risk_level, "Medium"), func.count(Crime.id)
    ).group_by(func.coalesce(Crime.severity, Crime.risk_level, "Medium")).all()
    severity_breakdown = [{"severity": (s[0] or "Medium").capitalize(), "count": s[1]} for s in severity_counts]

    # Zone distribution estimate from crimes with coordinates
    coords_crimes = Crime.query.filter(Crime.latitude.isnot(None), Crime.longitude.isnot(None)).limit(100).all()
    zone_counts = {"RED": 0, "ORANGE": 0, "YELLOW": 0, "GREEN": 0}
    for c in coords_crimes:
        try:
            risk = calculate_zone_risk(c.latitude, c.longitude, radius=800)
            z = (risk.get("zone") or "GREEN").upper()
            zone_counts[z] = zone_counts.get(z, 0) + 1
        except Exception:
            pass

    # Monthly incident trend (past 12 months)
    current_year = datetime.utcnow().year
    month_crimes = db.session.query(
        Crime.published_date, func.count(Crime.id)
    ).filter(Crime.published_date.isnot(None)).group_by(Crime.published_date).all()

    # Summarize by month
    monthly_trend = {}
    for date_str, count in month_crimes:
        if date_str and len(date_str) >= 7:
            month_key = date_str[:7]  # YYYY-MM
            monthly_trend[month_key] = monthly_trend.get(month_key, 0) + count

    sorted_months = sorted(monthly_trend.items())[-12:]
    monthly_chart_data = [{"month": m[0], "count": m[1]} for m in sorted_months]

    return jsonify({
        "success": True,
        "kpis": {
            "total_crimes": total_crimes,
            "high_severity_count": high_severity_crimes,
            "active_hotspots": hotspots_count,
            "total_users": total_users,
            "active_users_now": active_users_now,
            "active_sos_events": active_sos_count,
            "red_zone_users": red_zone_users_count,
        },
        "charts": {
            "crimes_by_type": crimes_by_type,
            "severity_breakdown": severity_breakdown,
            "zone_distribution": [{"zone": k, "count": v} for k, v in zone_counts.items()],
            "monthly_trend": monthly_chart_data,
        }
    }), 200


# =========================================================================== #
# 2. CRIME DATA CRUD, SEARCH, PAGINATION & CSV IMPORT / EXPORT
# =========================================================================== #

@admin_bp.route("/crimes", methods=["GET"])
@admin_required
def list_crimes():
    """
    GET /api/admin/crimes
    Paginated, searchable, filterable and sortable crime incident records.
    """
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    q = (request.args.get("q") or "").strip()
    crime_type = (request.args.get("crime_type") or "").strip()
    severity = (request.args.get("severity") or "").strip()
    district = (request.args.get("district") or "").strip()
    start_date = (request.args.get("start_date") or "").strip()
    end_date = (request.args.get("end_date") or "").strip()
    sort_by = request.args.get("sort_by", "published_date")
    order = request.args.get("order", "desc")

    query = Crime.query

    if q:
        query = query.filter(
            or_(
                Crime.title.ilike(f"%{q}%"),
                Crime.locality.ilike(f"%{q}%"),
                Crime.district.ilike(f"%{q}%"),
                Crime.description.ilike(f"%{q}%"),
                Crime.article_id.ilike(f"%{q}%"),
            )
        )

    if crime_type and crime_type.lower() != "all":
        query = query.filter(Crime.crime_type.ilike(crime_type))

    if severity and severity.lower() != "all":
        query = query.filter(
            or_(
                Crime.severity.ilike(severity),
                Crime.risk_level.ilike(severity)
            )
        )

    if district and district.lower() != "all":
        query = query.filter(Crime.district.ilike(district))

    if start_date:
        query = query.filter(Crime.published_date >= start_date)

    if end_date:
        query = query.filter(Crime.published_date <= end_date)

    # Sorting
    sort_col = getattr(Crime, sort_by, Crime.published_date)
    if order == "asc":
        query = query.order_by(asc(sort_col))
    else:
        query = query.order_by(desc(sort_col))

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "success": True,
        "total": paginated.total,
        "page": paginated.page,
        "per_page": paginated.per_page,
        "pages": paginated.pages,
        "crimes": [c.to_dict() for c in paginated.items]
    }), 200


@admin_bp.route("/crimes", methods=["POST"])
@admin_required
def create_crime():
    """
    POST /api/admin/crimes
    Create new crime incident with validation and automatic article_id.
    """
    data = request.get_json() or {}
    crime_type = (data.get("crime_type") or "").strip()
    locality = (data.get("locality") or data.get("location_name") or "").strip()
    published_date = (data.get("published_date") or data.get("crime_date") or datetime.utcnow().strftime("%Y-%m-%d")).strip()

    if not crime_type:
        return jsonify({"success": False, "error": "Crime type is required"}), 400

    lat = data.get("latitude")
    lng = data.get("longitude")
    severity = (data.get("severity") or data.get("risk_level") or "Medium").upper()

    try:
        lat = float(lat) if lat is not None and str(lat).strip() != "" else None
        lng = float(lng) if lng is not None and str(lng).strip() != "" else None
    except (ValueError, TypeError):
        lat, lng = None, None

    # Generate unique article_id
    import uuid
    article_id = f"ADM_{datetime.utcnow().strftime('%Y%m%d')}_{uuid.uuid4().hex[:6]}"

    new_crime = Crime(
        article_id=article_id,
        title=data.get("title") or f"{crime_type} reported at {locality or 'Vellore'}",
        published_date=published_date,
        crime_type=crime_type,
        district=data.get("district") or "Vellore",
        locality=locality or "Vellore",
        description=data.get("description") or "",
        source=data.get("source") or "Police FIR Registry",
        url=data.get("url") or "",
        latitude=lat,
        longitude=lng,
        severity=severity,
        risk_level=severity,
        severity_score=0.9 if severity in ["CRITICAL", "HIGH"] else (0.5 if severity == "MEDIUM" else 0.2)
    )
    db.session.add(new_crime)
    db.session.commit()

    AuditLog.record(
        action="CREATE_INCIDENT",
        admin=g.current_user,
        target_entity=f"Incident #{new_crime.id} ({article_id})",
        details=f"Created {crime_type} at {locality} with severity {severity}",
        ip_address=get_client_ip()
    )

    return jsonify({
        "success": True,
        "message": "Crime incident created successfully.",
        "crime": new_crime.to_dict()
    }), 201


@admin_bp.route("/crimes/<int:crime_id>", methods=["PUT"])
@admin_required
def update_crime(crime_id):
    """
    PUT /api/admin/crimes/<id>
    Update incident fields.
    """
    crime = db.session.get(Crime, crime_id)
    if not crime:
        return jsonify({"success": False, "error": "Crime incident not found"}), 404

    data = request.get_json() or {}
    if "title" in data:
        crime.title = data["title"]
    if "crime_type" in data and data["crime_type"]:
        crime.crime_type = data["crime_type"].strip()
    if "published_date" in data:
        crime.published_date = data["published_date"]
    if "district" in data:
        crime.district = data["district"]
    if "locality" in data:
        crime.locality = data["locality"]
        crime.location_name = data["locality"]
    if "description" in data:
        crime.description = data["description"]
    if "latitude" in data:
        try:
            crime.latitude = float(data["latitude"]) if data["latitude"] is not None else None
        except (ValueError, TypeError):
            pass
    if "longitude" in data:
        try:
            crime.longitude = float(data["longitude"]) if data["longitude"] is not None else None
        except (ValueError, TypeError):
            pass
    if "severity" in data:
        crime.severity = str(data["severity"]).upper()
        crime.risk_level = crime.severity

    db.session.commit()

    AuditLog.record(
        action="UPDATE_INCIDENT",
        admin=g.current_user,
        target_entity=f"Incident #{crime.id} ({crime.article_id})",
        details=f"Updated details of {crime.crime_type}",
        ip_address=get_client_ip()
    )

    return jsonify({
        "success": True,
        "message": "Incident updated successfully.",
        "crime": crime.to_dict()
    }), 200


@admin_bp.route("/crimes/<int:crime_id>", methods=["DELETE"])
@admin_required
def delete_crime(crime_id):
    """
    DELETE /api/admin/crimes/<id>
    Delete crime record.
    """
    crime = db.session.get(Crime, crime_id)
    if not crime:
        return jsonify({"success": False, "error": "Crime incident not found"}), 404

    article_id = crime.article_id
    crime_type = crime.crime_type

    db.session.delete(crime)
    db.session.commit()

    AuditLog.record(
        action="DELETE_INCIDENT",
        admin=g.current_user,
        target_entity=f"Incident #{crime_id} ({article_id})",
        details=f"Deleted {crime_type} record",
        ip_address=get_client_ip()
    )

    return jsonify({
        "success": True,
        "message": "Incident deleted successfully."
    }), 200


@admin_bp.route("/crimes/export", methods=["GET"])
@admin_required
def export_crimes_csv():
    """
    GET /api/admin/crimes/export
    Generate CSV file of all or filtered crime records.
    """
    q = (request.args.get("q") or "").strip()
    crime_type = (request.args.get("crime_type") or "").strip()
    severity = (request.args.get("severity") or "").strip()

    query = Crime.query
    if q:
        query = query.filter(or_(Crime.title.ilike(f"%{q}%"), Crime.locality.ilike(f"%{q}%"), Crime.crime_type.ilike(f"%{q}%")))
    if crime_type and crime_type.lower() != "all":
        query = query.filter(Crime.crime_type.ilike(crime_type))
    if severity and severity.lower() != "all":
        query = query.filter(or_(Crime.severity.ilike(severity), Crime.risk_level.ilike(severity)))

    crimes = query.order_by(desc(Crime.published_date)).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "article_id", "title", "published_date", "crime_type", "district",
        "locality", "latitude", "longitude", "severity", "description", "source", "url"
    ])

    for c in crimes:
        writer.writerow([
            c.id, c.article_id, c.title, c.published_date, c.crime_type, c.district,
            c.locality, c.latitude, c.longitude, c.severity or c.risk_level, c.description, c.source, c.url
        ])

    output.seek(0)

    AuditLog.record(
        action="EXPORT_CSV",
        admin=g.current_user,
        target_entity="Crime Dataset",
        details=f"Exported {len(crimes)} records to CSV",
        ip_address=get_client_ip()
    )

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=crimesense_export_{datetime.utcnow().strftime('%Y%m%d')}.csv"}
    )


@admin_bp.route("/crimes/import", methods=["POST"])
@admin_required
def import_crimes_csv():
    """
    POST /api/admin/crimes/import
    Bulk import crime records from uploaded CSV.
    """
    if "file" not in request.files:
        return jsonify({"success": False, "error": "CSV file is required"}), 400

    file = request.files["file"]
    if not file.filename.endswith(".csv"):
        return jsonify({"success": False, "error": "Only CSV files are supported"}), 400

    import uuid
    imported_count = 0
    updated_count = 0

    try:
        stream = io.StringIO(file.stream.read().decode("utf-8", errors="ignore"))
        reader = csv.DictReader(stream)

        for row in reader:
            art_id = row.get("article_id") or row.get("id") or f"IMP_{datetime.utcnow().strftime('%Y%m%d')}_{uuid.uuid4().hex[:6]}"
            crime_type = row.get("crime_type") or row.get("type") or "General Crime"
            date_str = row.get("published_date") or row.get("crime_date") or row.get("date") or datetime.utcnow().strftime("%Y-%m-%d")
            locality = row.get("locality") or row.get("location_name") or row.get("location") or "Vellore"
            district = row.get("district") or "Vellore"
            title = row.get("title") or f"{crime_type} at {locality}"
            desc_text = row.get("description") or ""

            lat = row.get("latitude") or row.get("lat")
            lng = row.get("longitude") or row.get("lng")
            try:
                lat = float(lat) if lat else None
                lng = float(lng) if lng else None
            except ValueError:
                lat, lng = None, None

            sev = (row.get("severity") or row.get("risk_level") or "Medium").upper()

            existing = Crime.query.filter_by(article_id=str(art_id)).first()
            if existing:
                existing.title = title
                existing.crime_type = crime_type
                existing.published_date = date_str
                existing.locality = locality
                existing.district = district
                existing.latitude = lat
                existing.longitude = lng
                existing.severity = sev
                existing.risk_level = sev
                updated_count += 1
            else:
                new_c = Crime(
                    article_id=str(art_id),
                    title=title,
                    published_date=date_str,
                    crime_type=crime_type,
                    district=district,
                    locality=locality,
                    description=desc_text,
                    source=row.get("source") or "CSV Import",
                    url=row.get("url") or "",
                    latitude=lat,
                    longitude=lng,
                    severity=sev,
                    risk_level=sev,
                    severity_score=0.8 if sev in ["CRITICAL", "HIGH"] else 0.4
                )
                db.session.add(new_c)
                imported_count += 1

        db.session.commit()

        AuditLog.record(
            action="IMPORT_CSV",
            admin=g.current_user,
            target_entity="Crime Dataset",
            details=f"Imported {imported_count} new records, updated {updated_count} existing records from {file.filename}",
            ip_address=get_client_ip()
        )

        return jsonify({
            "success": True,
            "message": f"Successfully imported {imported_count} new incidents and updated {updated_count} records.",
            "imported_count": imported_count,
            "updated_count": updated_count
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to parse CSV: {str(e)}"}), 400


# =========================================================================== #
# 3. HISTORY & TRENDS ANALYTICS
# =========================================================================== #

@admin_bp.route("/analytics/trends", methods=["GET"])
@admin_required
def get_historical_trends():
    """
    GET /api/admin/analytics/trends
    Crimes by year/month, YoY comparisons, district/locality breakdowns, crime type trends.
    """
    year_filter = request.args.get("year", "all")

    # 1. Available years
    all_dates = db.session.query(Crime.published_date).filter(Crime.published_date.isnot(None)).all()
    years_set = set()
    for (d,) in all_dates:
        if d and len(d) >= 4 and d[:4].isdigit():
            years_set.add(d[:4])

    available_years = sorted(list(years_set))

    # 2. Crimes by Year
    crimes_by_year = {}
    for (d,) in all_dates:
        if d and len(d) >= 4 and d[:4].isdigit():
            y = d[:4]
            crimes_by_year[y] = crimes_by_year.get(y, 0) + 1

    year_chart_data = [{"year": y, "count": crimes_by_year[y]} for y in sorted(crimes_by_year.keys())]

    # 3. Monthly Breakdown for selected year (or all)
    query = Crime.query.filter(Crime.published_date.isnot(None))
    if year_filter != "all":
        query = query.filter(Crime.published_date.startswith(year_filter))

    month_counts = {}
    for c in query.all():
        d = c.published_date
        if d and len(d) >= 7:
            m = d[:7]  # YYYY-MM
            month_counts[m] = month_counts.get(m, 0) + 1

    monthly_breakdown = [{"month": k, "count": v} for k, v in sorted(month_counts.items())]

    # 4. Per District Breakdown
    district_query = db.session.query(
        func.coalesce(Crime.district, "Vellore"), func.count(Crime.id)
    ).group_by(func.coalesce(Crime.district, "Vellore")).order_by(desc(func.count(Crime.id))).all()
    district_breakdown = [{"district": d[0], "count": d[1]} for d in district_query]

    # 5. Top Localities Breakdown
    locality_query = db.session.query(
        func.coalesce(Crime.locality, "Vellore"), func.count(Crime.id)
    ).group_by(func.coalesce(Crime.locality, "Vellore")).order_by(desc(func.count(Crime.id))).limit(10).all()
    locality_breakdown = [{"locality": l[0], "count": l[1]} for l in locality_query]

    # 6. Per Crime Type Multi-Year Trend
    type_year_query = db.session.query(
        Crime.crime_type, func.substr(Crime.published_date, 1, 4), func.count(Crime.id)
    ).filter(Crime.published_date.isnot(None)).group_by(
        Crime.crime_type, func.substr(Crime.published_date, 1, 4)
    ).all()

    type_trends = {}
    for ctype, y, cnt in type_year_query:
        if y and y.isdigit():
            if ctype not in type_trends:
                type_trends[ctype] = {}
            type_trends[ctype][y] = cnt

    return jsonify({
        "success": True,
        "available_years": available_years,
        "selected_year": year_filter,
        "year_chart": year_chart_data,
        "monthly_breakdown": monthly_breakdown,
        "district_breakdown": district_breakdown,
        "locality_breakdown": locality_breakdown,
        "type_trends": type_trends
    }), 200


# =========================================================================== #
# 4. USER MANAGEMENT & DETAILED PROFILE
# =========================================================================== #

@admin_bp.route("/users", methods=["GET"])
@admin_required
def list_users():
    """
    GET /api/admin/users
    Paginated user list with role, location status, contact counts, and last zone.
    """
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    q = (request.args.get("q") or "").strip()
    role_filter = request.args.get("role", "all")

    query = User.query
    if q:
        query = query.filter(or_(User.name.ilike(f"%{q}%"), User.email.ilike(f"%{q}%")))
    if role_filter != "all":
        query = query.filter_by(role=role_filter)

    paginated = query.order_by(desc(User.created_at)).paginate(page=page, per_page=per_page, error_out=False)

    users_data = []
    for u in paginated.items:
        settings = UserSettings.query.filter_by(user_id=u.id).first()
        contact_count = SOSContact.query.filter_by(user_id=u.id).count()
        rz_state = UserRedZoneState.query.filter_by(user_id=u.id).first()

        users_data.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
            "location_sharing_enabled": settings.location_sharing_enabled if settings else False,
            "share_live_location_with_admin": settings.share_live_location_with_admin if settings else False,
            "last_known_zone": rz_state.zone if rz_state else "green",
            "last_state": rz_state.state if rz_state else "SAFE",
            "sos_contact_count": contact_count
        })

    return jsonify({
        "success": True,
        "total": paginated.total,
        "page": paginated.page,
        "per_page": paginated.per_page,
        "pages": paginated.pages,
        "users": users_data
    }), 200


@admin_bp.route("/users/<int:user_id>", methods=["GET"])
@admin_required
def get_user_detail(user_id):
    """
    GET /api/admin/users/<id>
    Deep user inspection: profile, SOS contacts, saved destinations, SOS events,
    and consented location history trail.
    """
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    settings = UserSettings.query.filter_by(user_id=user.id).first()
    contacts = SOSContact.query.filter_by(user_id=user.id).order_by(SOSContact.is_primary.desc()).all()
    saved = SavedLocation.query.filter_by(user_id=user.id).all()
    sos_events = SOSEvent.query.filter_by(user_id=user.id).order_by(desc(SOSEvent.created_at)).all()
    rz_state = UserRedZoneState.query.filter_by(user_id=user.id).first()

    # Privacy filter: only return location history if user enabled location sharing or has active SOS
    locations = []
    has_location_consent = bool(settings and settings.location_sharing_enabled and settings.share_live_location_with_admin)
    has_active_sos = any(e.status == "active" for e in sos_events)

    if has_location_consent or has_active_sos:
        loc_records = UserLocation.query.filter_by(user_id=user.id).order_by(desc(UserLocation.recorded_at)).limit(50).all()
        locations = [l.to_dict() for l in loc_records]

    AuditLog.record(
        action="VIEW_USER_DETAILS",
        admin=g.current_user,
        target_entity=f"User #{user.id} ({user.email})",
        details="Admin viewed complete user safety profile and history",
        ip_address=get_client_ip()
    )

    return jsonify({
        "success": True,
        "user": user.to_dict(),
        "settings": settings.to_dict() if settings else None,
        "contacts": [c.to_dict() for c in contacts],
        "saved_locations": [s.to_dict() for s in saved],
        "sos_events": [e.to_dict() for e in sos_events],
        "location_history": locations,
        "location_sharing_consented": has_location_consent,
        "red_zone_state": rz_state.to_dict() if rz_state else None,
    }), 200


@admin_bp.route("/users/<int:user_id>/role", methods=["PUT"])
@admin_required
def change_user_role(user_id):
    """
    PUT /api/admin/users/<id>/role
    Update user role between 'user' and 'admin'.
    """
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    data = request.get_json() or {}
    new_role = (data.get("role") or "").strip().lower()

    if new_role not in ["user", "admin"]:
        return jsonify({"success": False, "error": "Role must be 'user' or 'admin'"}), 400

    old_role = user.role
    user.role = new_role
    db.session.commit()

    AuditLog.record(
        action="CHANGE_USER_ROLE",
        admin=g.current_user,
        target_entity=f"User #{user.id} ({user.email})",
        details=f"Changed role from {old_role} to {new_role}",
        ip_address=get_client_ip()
    )

    return jsonify({
        "success": True,
        "message": f"User role updated to '{new_role}'.",
        "user": user.to_dict()
    }), 200


@admin_bp.route("/users/<int:user_id>/status", methods=["PUT"])
@admin_required
def toggle_user_active(user_id):
    """
    PUT /api/admin/users/<id>/status
    Activate or deactivate user account.
    """
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    if user.id == g.current_user.id:
        return jsonify({"success": False, "error": "You cannot deactivate your own admin account."}), 400

    data = request.get_json() or {}
    is_active = bool(data.get("is_active", not user.is_active))
    user.is_active = is_active
    db.session.commit()

    AuditLog.record(
        action="TOGGLE_USER_ACTIVE",
        admin=g.current_user,
        target_entity=f"User #{user.id} ({user.email})",
        details=f"Set account is_active to {is_active}",
        ip_address=get_client_ip()
    )

    return jsonify({
        "success": True,
        "message": f"User account {'activated' if is_active else 'deactivated'}.",
        "user": user.to_dict()
    }), 200


@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user_admin(user_id):
    """
    DELETE /api/admin/users/<id>
    Permanently delete user and cascade data.
    """
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    if user.id == g.current_user.id:
        return jsonify({"success": False, "error": "You cannot delete your own admin account."}), 400

    from models.shared_link import SharedLink

    email = user.email
    # Cascade clean
    UserLocation.query.filter_by(user_id=user_id).delete()
    UserSettings.query.filter_by(user_id=user_id).delete()
    SOSContact.query.filter_by(user_id=user_id).delete()
    SOSEvent.query.filter_by(user_id=user_id).delete()
    SavedLocation.query.filter_by(user_id=user_id).delete()
    SharedLink.query.filter_by(user_id=user_id).delete()
    UserRedZoneState.query.filter_by(user_id=user_id).delete()

    db.session.delete(user)
    db.session.commit()

    AuditLog.record(
        action="DELETE_USER",
        admin=g.current_user,
        target_entity=f"User #{user_id} ({email})",
        details="Admin permanently deleted user account and personal records",
        ip_address=get_client_ip()
    )

    return jsonify({
        "success": True,
        "message": f"User '{email}' and all associated records permanently removed."
    }), 200


# =========================================================================== #
# 5. LIVE MAP (STRICT PRIVACY GUARDED)
# =========================================================================== #

@admin_bp.route("/live-map/users", methods=["GET"])
@admin_required
def get_live_map_users():
    """
    GET /api/admin/live-map/users
    Returns users currently broadcasting live location who have consented
    (location_sharing_enabled=True AND share_live_location_with_admin=True, OR active SOS).
    Filters out any users who disabled location sharing.
    """
    now = datetime.utcnow()
    fifteen_min_ago = now - timedelta(minutes=15)

    # Active states
    states = UserRedZoneState.query.filter(
        UserRedZoneState.latitude.isnot(None),
        UserRedZoneState.longitude.isnot(None),
        UserRedZoneState.last_heartbeat_at >= fifteen_min_ago
    ).all()

    active_live_users = []

    for s in states:
        u = db.session.get(User, s.user_id)
        if not u or not u.is_active:
            continue

        settings = UserSettings.query.filter_by(user_id=u.id).first()
        active_sos = SOSEvent.query.filter_by(user_id=u.id, status="active").first()

        # Strict privacy check
        is_consented = bool(settings and settings.location_sharing_enabled and settings.share_live_location_with_admin)
        if not is_consented and not active_sos:
            continue  # Skip users who did not consent

        time_ago = int((now - s.last_heartbeat_at).total_seconds()) if s.last_heartbeat_at else 0

        active_live_users.append({
            "user_id": u.id,
            "name": u.name,
            "email": u.email,
            "latitude": s.latitude,
            "longitude": s.longitude,
            "accuracy": s.accuracy,
            "zone": (s.zone or "green").lower(),
            "state": s.state,
            "last_heartbeat_at": s.last_heartbeat_at.isoformat() if s.last_heartbeat_at else None,
            "time_ago_seconds": time_ago,
            "is_emergency": active_sos is not None,
            "sos_event_id": active_sos.id if active_sos else None
        })

    # Log live map access
    AuditLog.record(
        action="VIEW_LIVE_MAP",
        admin=g.current_user,
        target_entity="Live Map Stream",
        details=f"Admin monitored {len(active_live_users)} active consented users on live map",
        ip_address=get_client_ip()
    )

    return jsonify({
        "success": True,
        "count": len(active_live_users),
        "timestamp": now.isoformat(),
        "users": active_live_users
    }), 200


# =========================================================================== #
# 6. ALERTS & SOS FEED, RESOLUTION & NOTES
# =========================================================================== #

@admin_bp.route("/sos-feed", methods=["GET"])
@admin_required
def get_admin_sos_feed():
    """
    GET /api/admin/sos-feed
    Live stream of SOS events with filters for status, type, and date range.
    """
    status_filter = request.args.get("status", "all")
    type_filter = request.args.get("type", "all")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    query = SOSEvent.query

    if status_filter != "all":
        query = query.filter_by(status=status_filter)
    if type_filter != "all":
        query = query.filter_by(type=type_filter)
    if start_date:
        query = query.filter(SOSEvent.created_at >= start_date)
    if end_date:
        query = query.filter(SOSEvent.created_at <= end_date)

    events = query.order_by(desc(SOSEvent.created_at)).limit(100).all()
    active_count = SOSEvent.query.filter_by(status="active").count()

    results = []
    for e in events:
        u = db.session.get(User, e.user_id)
        e_dict = e.to_dict()
        e_dict["user_name"] = u.name if u else "Unknown User"
        e_dict["user_email"] = u.email if u else "N/A"
        results.append(e_dict)

    return jsonify({
        "success": True,
        "count": len(results),
        "active_count": active_count,
        "events": results
    }), 200


@admin_bp.route("/sos-events/<int:event_id>/resolve", methods=["POST"])
@admin_required
def admin_resolve_sos_event(event_id):
    """
    POST /api/admin/sos-events/<id>/resolve
    Admin manually resolves an active SOS distress event and adds resolution notes.
    """
    event = db.session.get(SOSEvent, event_id)
    if not event:
        return jsonify({"success": False, "error": "SOS event not found"}), 404

    data = request.get_json() or {}
    notes = (data.get("notes") or "").strip()

    now = datetime.utcnow()
    event.status = "resolved"
    event.resolved_at = now
    if notes:
        existing_notes = getattr(event, "admin_notes", None) or ""
        admin_tag = f"[{g.current_user.name} @ {now.strftime('%d %b %H:%M')}]: {notes}"
        event.admin_notes = f"{existing_notes}\n{admin_tag}".strip()

    db.session.commit()

    AuditLog.record(
        action="RESOLVE_SOS_EVENT",
        admin=g.current_user,
        target_entity=f"SOSEvent #{event.id}",
        details=f"Admin marked event as resolved. Notes: {notes or 'None'}",
        ip_address=get_client_ip()
    )

    return jsonify({
        "success": True,
        "message": "SOS distress event resolved successfully.",
        "event": event.to_dict()
    }), 200


@admin_bp.route("/sos-events/<int:event_id>/notes", methods=["PUT"])
@admin_required
def admin_update_sos_notes(event_id):
    """
    PUT /api/admin/sos-events/<id>/notes
    Attach admin observation/police dispatch notes to an SOS incident.
    """
    event = db.session.get(SOSEvent, event_id)
    if not event:
        return jsonify({"success": False, "error": "SOS event not found"}), 404

    data = request.get_json() or {}
    notes = (data.get("notes") or "").strip()

    now = datetime.utcnow()
    admin_tag = f"[{g.current_user.name} @ {now.strftime('%d %b %H:%M')}]: {notes}"
    existing_notes = getattr(event, "admin_notes", None) or ""
    event.admin_notes = f"{existing_notes}\n{admin_tag}".strip()

    db.session.commit()

    AuditLog.record(
        action="ADD_SOS_NOTES",
        admin=g.current_user,
        target_entity=f"SOSEvent #{event.id}",
        details=f"Added admin note: {notes}",
        ip_address=get_client_ip()
    )

    return jsonify({
        "success": True,
        "message": "Notes attached to SOS event.",
        "event": event.to_dict()
    }), 200


# =========================================================================== #
# 7. AUDIT LOGS
# =========================================================================== #

@admin_bp.route("/audit-logs", methods=["GET"])
@admin_required
def list_audit_logs():
    """
    GET /api/admin/audit-logs
    Paginated audit log of admin operations and sensitive data accesses.
    """
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 30))
    action_filter = (request.args.get("action") or "").strip()
    admin_filter = (request.args.get("admin") or "").strip()

    query = AuditLog.query

    if action_filter and action_filter != "all":
        query = query.filter(AuditLog.action.ilike(f"%{action_filter}%"))

    if admin_filter:
        query = query.filter(or_(AuditLog.admin_email.ilike(f"%{admin_filter}%"), AuditLog.admin_name.ilike(f"%{admin_filter}%")))

    paginated = query.order_by(desc(AuditLog.created_at)).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "success": True,
        "total": paginated.total,
        "page": paginated.page,
        "per_page": paginated.per_page,
        "pages": paginated.pages,
        "logs": [l.to_dict() for l in paginated.items]
    }), 200
