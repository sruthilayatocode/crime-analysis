"""
red_zone_scheduler.py
=====================
Background scheduler and state machine for Red Zone Inactivity Monitoring.
State Machine per user: SAFE -> IN_RED -> WARNING -> AUTO_ALERT_SENT

Rules enforced:
1. When a user's latest zone is RED and they remain stationary (>30m no movement, no interaction)
   for >= inactivity_minutes (default 10, configurable 5-30), triggers 'Are you safe?' prompt (60s window).
2. If no 'I'm safe' check-in within 60s, creates an auto_red_zone SOSEvent and notifies SOS contacts.
3. 30-minute cooldown between auto alerts per user to prevent notification spam.
4. Stale heartbeat detection (> 15 min without heartbeat in RED zone) treated as trigger candidate with 'last known location'.
5. Resets state when moving out of RED, tapping 'I'm safe', or disabling features.
"""

from __future__ import annotations

import logging
import math
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from database import db
from models.user import User
from models.user_settings import UserSettings
from models.user_red_zone_state import UserRedZoneState
from models.sos_contact import SOSContact
from models.sos_event import SOSEvent
from models.user_location import UserLocation
from services.notification_service import notification_service

logger = logging.getLogger("crimesense.scheduler")
logging.basicConfig(level=logging.INFO)

# Global stop event for daemon scheduler thread
_scheduler_stop_event = threading.Event()
_scheduler_thread = None


def calculate_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Haversine distance between two coordinates in meters."""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 0.0

    R = 6371000.0  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def evaluate_user_state(
    user_id: int,
    override_now: Optional[datetime] = None,
    threshold_override_minutes: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Evaluate the Red Zone Inactivity state machine for a specific user.
    """
    now = override_now or datetime.utcnow()
    user = db.session.get(User, user_id)
    if not user:
        return {"success": False, "error": "User not found"}

    # 1. Fetch user settings
    settings = UserSettings.query.filter_by(user_id=user_id).first()
    if not settings:
        settings = UserSettings(user_id=user_id, location_sharing_enabled=True, red_zone_alert_enabled=True)
        db.session.add(settings)
        db.session.commit()

    # 2. Fetch or initialize Red Zone state
    rz_state = UserRedZoneState.query.filter_by(user_id=user_id).first()
    if not rz_state:
        rz_state = UserRedZoneState(
            user_id=user_id,
            state="SAFE",
            zone="green",
            last_interaction_at=now,
            last_heartbeat_at=now
        )
        db.session.add(rz_state)
        db.session.commit()

    # If user disabled location sharing or red zone alerts, reset state to SAFE
    if not settings.location_sharing_enabled or not settings.red_zone_alert_enabled:
        if rz_state.state != "SAFE":
            rz_state.state = "SAFE"
            rz_state.entered_red_at = None
            rz_state.warning_prompt_sent_at = None
            rz_state.warning_expires_at = None
            rz_state.is_stale_heartbeat = False
            db.session.commit()
        return {"success": True, "state": "SAFE", "reason": "Feature disabled in user settings"}

    # 3. Check 30-minute cooldown
    in_cooldown = False
    if rz_state.last_auto_alert_at:
        cooldown_elapsed = (now - rz_state.last_auto_alert_at).total_seconds()
        if cooldown_elapsed < 1800:  # 30 minutes = 1800 seconds
            in_cooldown = True

    # 4. Check if current zone is NOT RED
    current_zone = (rz_state.zone or "green").lower()
    if current_zone != "red":
        if rz_state.state != "SAFE":
            logger.info(f"[Scheduler] User #{user_id} moved out of RED zone (zone={current_zone}). Resetting state to SAFE.")
            rz_state.state = "SAFE"
            rz_state.entered_red_at = None
            rz_state.warning_prompt_sent_at = None
            rz_state.warning_expires_at = None
            rz_state.is_stale_heartbeat = False
            db.session.commit()
        return {"success": True, "state": "SAFE", "zone": current_zone}

    # 5. User is in RED ZONE
    inactivity_limit_minutes = (
        threshold_override_minutes
        if threshold_override_minutes is not None
        else (settings.inactivity_minutes or 10)
    )

    # State: SAFE -> transition to IN_RED
    if rz_state.state == "SAFE":
        rz_state.state = "IN_RED"
        rz_state.entered_red_at = rz_state.entered_red_at or now
        rz_state.last_interaction_at = rz_state.last_interaction_at or now
        rz_state.is_stale_heartbeat = False
        db.session.commit()
        logger.info(f"[Scheduler] User #{user_id} transitioned SAFE -> IN_RED at {now.isoformat()}")
        return {"success": True, "state": "IN_RED", "entered_at": rz_state.entered_red_at.isoformat()}

    # State: IN_RED -> check inactivity & stale heartbeat
    if rz_state.state == "IN_RED":
        # Check stale heartbeat (> 15 minutes without heartbeat while in RED)
        is_stale = False
        if rz_state.last_heartbeat_at:
            hb_elapsed_minutes = (now - rz_state.last_heartbeat_at).total_seconds() / 60.0
            if hb_elapsed_minutes >= 15.0:
                is_stale = True
                rz_state.is_stale_heartbeat = True

        # Check inactivity duration since last movement/touch
        ref_time = rz_state.last_interaction_at or rz_state.entered_red_at or now
        inactive_minutes = (now - ref_time).total_seconds() / 60.0

        if (inactive_minutes >= inactivity_limit_minutes or is_stale) and not in_cooldown:
            # Transition to WARNING (prompt "Are you safe?" with 60s window)
            rz_state.state = "WARNING"
            rz_state.warning_prompt_sent_at = now
            rz_state.warning_expires_at = now + timedelta(seconds=60)
            db.session.commit()
            logger.warning(
                f"[Scheduler] User #{user_id} IN_RED -> WARNING (inactive for {inactive_minutes:.1f}m / stale={is_stale}). 60s prompt active."
            )
            return {
                "success": True,
                "state": "WARNING",
                "warning_expires_at": rz_state.warning_expires_at.isoformat(),
                "seconds_remaining": 60,
                "is_stale": is_stale,
            }

        return {
            "success": True,
            "state": "IN_RED",
            "inactive_minutes": round(inactive_minutes, 1),
            "threshold_minutes": inactivity_limit_minutes,
            "in_cooldown": in_cooldown,
        }

    # State: WARNING -> check if 60-second window expired
    if rz_state.state == "WARNING":
        if rz_state.warning_expires_at and now >= rz_state.warning_expires_at:
            if in_cooldown:
                logger.info(f"[Scheduler] User #{user_id} WARNING expired but in 30-min cooldown. Skipping duplicate alert.")
                rz_state.state = "IN_RED"
                rz_state.warning_prompt_sent_at = None
                rz_state.warning_expires_at = None
                db.session.commit()
                return {"success": True, "state": "IN_RED", "cooldown": True}

            # 60s expired without check-in -> Trigger AUTO SOS ALERT!
            logger.error(f"[Scheduler] 🚨 60s Safety prompt timed out for User #{user_id}! Triggering AUTO RED ZONE SOS EVENT!")
            rz_state.state = "AUTO_ALERT_SENT"
            rz_state.last_auto_alert_at = now
            rz_state.warning_prompt_sent_at = None
            rz_state.warning_expires_at = None
            db.session.commit()

            # Create SOSEvent record
            lat = rz_state.latitude if rz_state.latitude is not None else 12.9165
            lng = rz_state.longitude if rz_state.longitude is not None else 79.1325
            accuracy = rz_state.accuracy

            sos_event = SOSEvent(
                user_id=user_id,
                type="auto_red_zone",
                latitude=lat,
                longitude=lng,
                accuracy=accuracy,
                zone="red",
                status="active",
                created_at=now,
                live_tracking_until=now + timedelta(hours=1)
            )
            db.session.add(sos_event)
            db.session.commit()

            # Notify user's emergency contacts
            contacts = SOSContact.query.filter_by(user_id=user_id).all()
            user_name = user.name or "CrimeSense User"
            delivery_results = []

            for c in contacts:
                # Custom wording for auto red zone trigger
                res = notification_service.send_sos_alert(
                    recipient_phone=c.phone,
                    recipient_name=c.name,
                    user_name=f"{user_name} [AUTO RED ZONE INACTIVITY]",
                    latitude=lat,
                    longitude=lng,
                    zone_name="red",
                    event_time=now,
                    channel="sms"
                )
                delivery_results.append({
                    "contact_id": c.id,
                    "contact_name": c.name,
                    "contact_phone": c.phone,
                    "status": res.get("status", "sent"),
                    "provider": res.get("provider", "mock"),
                    "timestamp": now.isoformat()
                })

            sos_event.contacts_notified = delivery_results
            db.session.commit()

            return {
                "success": True,
                "state": "AUTO_ALERT_SENT",
                "sos_event_id": sos_event.id,
                "contacts_notified": delivery_results,
            }

        diff = (rz_state.warning_expires_at - now).total_seconds()
        return {
            "success": True,
            "state": "WARNING",
            "seconds_remaining": max(0, int(diff)),
        }

    return {"success": True, "state": rz_state.state}


def evaluate_all_users(app_instance) -> int:
    """
    Run evaluation loop over all active users with Red Zone monitoring enabled.
    """
    with app_instance.app_context():
        try:
            # Query all users with location sharing & red zone alert enabled
            active_settings = UserSettings.query.filter(
                UserSettings.location_sharing_enabled == True,
                UserSettings.red_zone_alert_enabled == True
            ).all()

            evaluated_count = 0
            for s in active_settings:
                evaluate_user_state(s.user_id)
                evaluated_count += 1

            return evaluated_count
        except Exception as err:
            logger.error(f"[Scheduler] Error during evaluate_all_users: {err}")
            return 0


def _scheduler_loop(app_instance, interval_seconds: int = 30):
    """Background worker thread running every interval_seconds."""
    logger.info(f"[Scheduler] Red Zone background worker started (evaluating every {interval_seconds}s).")
    while not _scheduler_stop_event.is_set():
        try:
            evaluate_all_users(app_instance)
        except Exception as e:
            logger.error(f"[Scheduler] Worker loop exception: {e}")
        _scheduler_stop_event.wait(interval_seconds)


def start_red_zone_scheduler(app_instance, interval_seconds: int = 30):
    """Start background daemon scheduler thread."""
    global _scheduler_thread
    if _scheduler_thread is None or not _scheduler_thread.is_alive():
        _scheduler_stop_event.clear()
        _scheduler_thread = threading.Thread(
            target=_scheduler_loop,
            args=(app_instance, interval_seconds),
            daemon=True,
            name="RedZoneInactivityScheduler"
        )
        _scheduler_thread.start()
        logger.info("[Scheduler] Background scheduler initialized and running.")


def stop_red_zone_scheduler():
    """Signal background worker to stop gracefully."""
    _scheduler_stop_event.set()
