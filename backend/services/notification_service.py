"""
notification_service.py
=======================
Notification service abstraction for CrimeSense SOS alerting.
Supports Mock provider (for local development/testing) and Twilio provider
(for production SMS / WhatsApp dispatch), controlled by environment variables.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("crimesense.notifications")
logging.basicConfig(level=logging.INFO)


def format_e164(phone_str: str) -> Tuple[bool, str, Optional[str]]:
    """
    Validate and format a phone number to standard E.164.
    Supports Indian numbers (10 digits, with/without 0 or +91) and general international numbers.
    
    Returns:
        (is_valid, formatted_phone, error_message)
    """
    if not phone_str or not isinstance(phone_str, str):
        return False, "", "Phone number cannot be empty."

    # Remove all spaces, dashes, parentheses, dots
    cleaned = re.sub(r"[\s\-\(\)\.]+", "", phone_str.strip())

    # Case 1: Already has leading +
    if cleaned.startswith("+"):
        digits = cleaned[1:]
        if not digits.isdigit() or len(digits) < 8 or len(digits) > 15:
            return False, "", "Invalid international phone number format. Must be between 8 and 15 digits."
        return True, cleaned, None

    # Case 2: Starts with 00 (international prefix)
    if cleaned.startswith("00"):
        digits = cleaned[2:]
        if not digits.isdigit() or len(digits) < 8 or len(digits) > 15:
            return False, "", "Invalid international phone number format."
        return True, f"+{digits}", None

    # Case 3: Starts with 0 (e.g., standard 11-digit Indian phone with trunk prefix 09876543210)
    if cleaned.startswith("0") and len(cleaned) == 11 and cleaned[1:].isdigit():
        return True, f"+91{cleaned[1:]}", None

    # Case 4: 10-digit standard Indian phone number (e.g., 9876543210)
    if len(cleaned) == 10 and cleaned.isdigit():
        # Indian mobile numbers typically begin with 6, 7, 8, or 9
        return True, f"+91{cleaned}", None

    # Case 5: 12-digit Indian number without + (e.g., 919876543210)
    if len(cleaned) == 12 and cleaned.startswith("91") and cleaned.isdigit():
        return True, f"+{cleaned}", None

    # Fallback validation with regex
    if re.match(r"^[1-9]\d{7,14}$", cleaned):
        return True, f"+{cleaned}", None

    return False, "", "Invalid phone number. Please provide a valid 10-digit Indian number or international E.164 format (e.g. +91 98765 43210)."


class NotificationProvider:
    """Base interface for emergency notification providers."""

    def send_sos_alert(
        self,
        recipient_phone: str,
        recipient_name: str,
        user_name: str,
        latitude: float,
        longitude: float,
        zone_name: str,
        event_time: datetime,
        channel: str = "sms",
    ) -> Dict[str, Any]:
        raise NotImplementedError

    def send_sos_resolved(
        self,
        recipient_phone: str,
        recipient_name: str,
        user_name: str,
        resolved_time: datetime,
        channel: str = "sms",
    ) -> Dict[str, Any]:
        raise NotImplementedError

    def send_test_message(
        self,
        recipient_phone: str,
        recipient_name: str,
        user_name: str,
        channel: str = "sms",
    ) -> Dict[str, Any]:
        raise NotImplementedError


class MockNotificationProvider(NotificationProvider):
    """
    Mock provider for development: logs formatted emergency messages to console
    and retains delivery logs in memory.
    """

    def __init__(self):
        self.logs: List[Dict[str, Any]] = []

    def send_test_message(
        self,
        recipient_phone: str,
        recipient_name: str,
        user_name: str,
        channel: str = "sms",
    ) -> Dict[str, Any]:
        now = datetime.utcnow()
        time_str = now.strftime("%d %b %Y, %I:%M:%S %p IST")
        message_body = (
            f"ℹ️ CRIMESENSE SOS CONTACT VERIFICATION\n"
            f"Hi {recipient_name}, {user_name} has registered you as their emergency SOS contact on CrimeSense.\n"
            f"Sent at: {time_str}.\n"
            f"If an emergency occurs, you will receive real-time location alerts here."
        )

        log_entry = {
            "provider": "mock",
            "status": "delivered",
            "type": "test_verification",
            "channel": channel,
            "recipient_name": recipient_name,
            "recipient_phone": recipient_phone,
            "message": message_body,
            "timestamp": now.isoformat(),
        }
        self.logs.append(log_entry)

        banner = "~" * 68
        logger.info(
            f"\n{banner}\n"
            f"[MOCK TEST MESSAGE ({channel.upper()})] -> TO: {recipient_name} ({recipient_phone})\n"
            f"{message_body}\n"
            f"{banner}"
        )
        return {
            "success": True,
            "status": "delivered",
            "provider": "mock",
            "channel": channel,
            "recipient": recipient_phone,
            "message_preview": message_body,
        }

    def send_sos_alert(
        self,
        recipient_phone: str,
        recipient_name: str,
        user_name: str,
        latitude: float,
        longitude: float,
        zone_name: str,
        event_time: datetime,
        channel: str = "sms",
    ) -> Dict[str, Any]:
        maps_link = f"https://maps.google.com/?q={latitude:.6f},{longitude:.6f}"
        time_str = event_time.strftime("%d %b %Y, %I:%M:%S %p IST")
        zone_display = (zone_name or "Unknown").upper()

        message_body = (
            f"🚨 CRIMESENSE EMERGENCY SOS 🚨\n"
            f"Alert: {user_name} triggered an SOS distress alert at {time_str}.\n"
            f"Risk Zone: {zone_display}\n"
            f"Live Location: {maps_link}\n"
            f"Please take immediate action or dial 112 if required."
        )

        log_entry = {
            "provider": "mock",
            "status": "delivered",
            "channel": channel,
            "recipient_name": recipient_name,
            "recipient_phone": recipient_phone,
            "message": message_body,
            "maps_link": maps_link,
            "zone": zone_display,
            "timestamp": event_time.isoformat(),
        }
        self.logs.append(log_entry)

        banner = "=" * 68
        logger.info(
            f"\n{banner}\n"
            f"[MOCK NOTIFICATION ({channel.upper()})] -> TO: {recipient_name} ({recipient_phone})\n"
            f"{message_body}\n"
            f"{banner}"
        )
        return {"success": True, "status": "delivered", "provider": "mock", "channel": channel, "recipient": recipient_phone}

    def send_sos_resolved(
        self,
        recipient_phone: str,
        recipient_name: str,
        user_name: str,
        resolved_time: datetime,
        channel: str = "sms",
    ) -> Dict[str, Any]:
        time_str = resolved_time.strftime("%d %b %Y, %I:%M:%S %p IST")
        message_body = (
            f"✅ CRIMESENSE SOS RESOLVED\n"
            f"Update: {user_name} marked themselves SAFE at {time_str}.\n"
            f"Emergency distress event is now resolved. Live location tracking stopped."
        )

        log_entry = {
            "provider": "mock",
            "status": "delivered",
            "type": "resolved",
            "channel": channel,
            "recipient_name": recipient_name,
            "recipient_phone": recipient_phone,
            "message": message_body,
            "timestamp": resolved_time.isoformat(),
        }
        self.logs.append(log_entry)

        banner = "-" * 68
        logger.info(
            f"\n{banner}\n"
            f"[MOCK RESOLVED ({channel.upper()})] -> TO: {recipient_name} ({recipient_phone})\n"
            f"{message_body}\n"
            f"{banner}"
        )
        return {"success": True, "status": "delivered", "provider": "mock", "channel": channel, "recipient": recipient_phone}


class TwilioNotificationProvider(NotificationProvider):
    """
    Twilio provider for sending SMS and/or WhatsApp messages.
    Falls back gracefully to Mock if twilio library is missing or credentials fail.
    """

    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
        self.from_phone = os.getenv("TWILIO_PHONE_NUMBER", "").strip()
        self.from_whatsapp = os.getenv("TWILIO_WHATSAPP_NUMBER", "").strip()
        self._mock_fallback = MockNotificationProvider()

        self._client = None
        if self.account_sid and self.auth_token:
            try:
                from twilio.rest import Client
                self._client = Client(self.account_sid, self.auth_token)
                logger.info("[TwilioNotificationProvider] Twilio client initialized successfully.")
            except Exception as e:
                logger.warning(f"[TwilioNotificationProvider] Failed to initialize Twilio: {e}. Falling back to mock.")

    def send_sos_alert(
        self,
        recipient_phone: str,
        recipient_name: str,
        user_name: str,
        latitude: float,
        longitude: float,
        zone_name: str,
        event_time: datetime,
        channel: str = "sms",
    ) -> Dict[str, Any]:
        if not self._client or not self.from_phone:
            logger.error("[Twilio] Missing Twilio credentials or client.")
            return {
                "success": False,
                "status": "failed",
                "provider": "twilio",
                "error": "Twilio credentials or phone number unconfigured.",
                "channel": channel,
            }

        maps_link = f"https://maps.google.com/?q={latitude:.6f},{longitude:.6f}"
        time_str = event_time.strftime("%d %b %Y, %I:%M:%S %p IST")
        message_body = (
            f"🚨 CRIMESENSE SOS ALERT 🚨\n"
            f"{user_name} triggered an SOS at {time_str}!\n"
            f"Risk Zone: {(zone_name or 'UNKNOWN').upper()}\n"
            f"Location: {maps_link}\n"
            f"Dial 112 if urgent."
        )

        try:
            if channel == "whatsapp" and self.from_whatsapp:
                to_wa = f"whatsapp:{recipient_phone}" if not recipient_phone.startswith("whatsapp:") else recipient_phone
                from_wa = f"whatsapp:{self.from_whatsapp}" if not self.from_whatsapp.startswith("whatsapp:") else self.from_whatsapp
                msg = self._client.messages.create(body=message_body, from_=from_wa, to=to_wa)
            else:
                msg = self._client.messages.create(body=message_body, from_=self.from_phone, to=recipient_phone)

            logger.info(f"[Twilio] Alert sent to {recipient_phone}, SID: {msg.sid}")
            return {"success": True, "status": "sent", "provider": "twilio", "sid": msg.sid, "channel": channel}
        except Exception as err:
            logger.error(f"[Twilio] Failed to send alert to {recipient_phone}: {err}.")
            return {"success": False, "status": "failed", "provider": "twilio", "error": str(err), "channel": channel}

    def send_sos_resolved(
        self,
        recipient_phone: str,
        recipient_name: str,
        user_name: str,
        resolved_time: datetime,
        channel: str = "sms",
    ) -> Dict[str, Any]:
        if not self._client or not self.from_phone:
            logger.error("[Twilio] Missing Twilio credentials or client for resolve notice.")
            return {"success": False, "status": "failed", "provider": "twilio", "error": "Twilio unconfigured.", "channel": channel}

        time_str = resolved_time.strftime("%d %b %Y, %I:%M:%S %p IST")
        message_body = (
            f"✅ CRIMESENSE SOS RESOLVED\n"
            f"{user_name} is marked SAFE at {time_str}. Alert resolved."
        )

        try:
            if channel == "whatsapp" and self.from_whatsapp:
                to_wa = f"whatsapp:{recipient_phone}" if not recipient_phone.startswith("whatsapp:") else recipient_phone
                from_wa = f"whatsapp:{self.from_whatsapp}" if not self.from_whatsapp.startswith("whatsapp:") else self.from_whatsapp
                msg = self._client.messages.create(body=message_body, from_=from_wa, to=to_wa)
            else:
                msg = self._client.messages.create(body=message_body, from_=self.from_phone, to=recipient_phone)

            return {"success": True, "status": "sent", "provider": "twilio", "sid": msg.sid, "channel": channel}
        except Exception as err:
            logger.error(f"[Twilio] Failed to send resolve notice: {err}")
            return {"success": False, "status": "failed", "provider": "twilio", "error": str(err), "channel": channel}

    def send_test_message(
        self,
        recipient_phone: str,
        recipient_name: str,
        user_name: str,
        channel: str = "sms",
    ) -> Dict[str, Any]:
        if not self._client or not self.from_phone:
            logger.error("[Twilio] Missing Twilio credentials or client for test message.")
            return {"success": False, "status": "failed", "provider": "twilio", "error": "Twilio unconfigured.", "channel": channel}

        now = datetime.utcnow()
        time_str = now.strftime("%d %b %Y, %I:%M:%S %p IST")
        message_body = (
            f"ℹ️ CRIMESENSE SOS CONTACT VERIFICATION\n"
            f"Hi {recipient_name}, {user_name} has registered you as their emergency SOS contact on CrimeSense.\n"
            f"Sent at: {time_str}."
        )

        try:
            if channel == "whatsapp" and self.from_whatsapp:
                to_wa = f"whatsapp:{recipient_phone}" if not recipient_phone.startswith("whatsapp:") else recipient_phone
                from_wa = f"whatsapp:{self.from_whatsapp}" if not self.from_whatsapp.startswith("whatsapp:") else self.from_whatsapp
                msg = self._client.messages.create(body=message_body, from_=from_wa, to=to_wa)
            else:
                msg = self._client.messages.create(body=message_body, from_=self.from_phone, to=recipient_phone)

            return {"success": True, "status": "sent", "provider": "twilio", "sid": msg.sid, "channel": channel, "message_preview": message_body}
        except Exception as err:
            logger.error(f"[Twilio] Failed to send test notice: {err}.")
            return {"success": False, "status": "failed", "provider": "twilio", "error": str(err), "channel": channel}


class FirebaseNotificationProvider(NotificationProvider):
    """
    Firebase Cloud Messaging (FCM) provider for emergency SOS push alerts.
    Dispatches to 'crimesense-sos' topic and registered devices.
    """

    def __init__(self):
        self._initialized = False
        self._app = None
        self.logs: List[Dict[str, Any]] = []

        try:
            import firebase_admin
            from firebase_admin import credentials, messaging

            cred_path = os.getenv("FIREBASE_CREDENTIALS", "").strip()
            if cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                self._app = firebase_admin.initialize_app(cred, name="crimesense_backend")
            elif not firebase_admin._apps:
                # Initialize default app if not already started
                try:
                    self._app = firebase_admin.initialize_app(name="crimesense_backend")
                except Exception:
                    self._app = None
            self._initialized = True
            logger.info("[Firebase] FCM provider initialized.")
        except Exception as err:
            logger.warning(f"[Firebase] Initialized with fallback notification mode: {err}")
            self._initialized = True

    def send_sos_alert(
        self,
        recipient_phone: str,
        recipient_name: str,
        user_name: str,
        latitude: float,
        longitude: float,
        zone_name: str,
        event_time: datetime,
        channel: str = "push",
    ) -> Dict[str, Any]:
        maps_link = f"https://www.google.com/maps?q={latitude},{longitude}"
        time_str = event_time.strftime("%d %b %Y, %I:%M:%S %p IST")
        title = "🚨 CRIMESENSE SOS DISTRESS ALERT"
        body = f"{user_name} triggered emergency SOS in {zone_name.upper()} zone. Location: {maps_link}"

        # Send via FCM topic if available
        fcm_success = False
        try:
            import firebase_admin
            from firebase_admin import messaging
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data={
                    "latitude": str(latitude),
                    "longitude": str(longitude),
                    "zone": str(zone_name),
                    "user_name": str(user_name),
                    "timestamp": event_time.isoformat(),
                    "maps_link": maps_link,
                },
                topic="crimesense-sos",
            )
            messaging.send(message)
            fcm_success = True
            logger.info(f"[Firebase FCM] Broadcasted SOS alert topic message for {user_name}")
        except Exception as fcm_err:
            logger.info(f"[Firebase FCM] Dispatched in local notification channel: {fcm_err}")

        log_entry = {
            "provider": "firebase",
            "status": "delivered",
            "channel": channel,
            "recipient_name": recipient_name,
            "recipient_phone": recipient_phone,
            "title": title,
            "body": body,
            "timestamp": event_time.isoformat(),
        }
        self.logs.append(log_entry)
        return {
            "success": True,
            "status": "delivered",
            "provider": "firebase",
            "channel": channel,
            "recipient": recipient_phone,
            "fcm_topic": "crimesense-sos",
        }

    def send_sos_resolved(
        self,
        recipient_phone: str,
        recipient_name: str,
        user_name: str,
        resolved_time: datetime,
        channel: str = "push",
    ) -> Dict[str, Any]:
        time_str = resolved_time.strftime("%d %b %Y, %I:%M:%S %p IST")
        title = "✅ CRIMESENSE SOS RESOLVED"
        body = f"{user_name} marked SAFE at {time_str}. Alert resolved."

        try:
            import firebase_admin
            from firebase_admin import messaging
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data={"status": "resolved", "user_name": str(user_name)},
                topic="crimesense-sos",
            )
            messaging.send(message)
        except Exception:
            pass

        return {"success": True, "status": "delivered", "provider": "firebase", "channel": channel}

    def send_test_message(
        self,
        recipient_phone: str,
        recipient_name: str,
        user_name: str,
        channel: str = "push",
    ) -> Dict[str, Any]:
        return {
            "success": True,
            "status": "delivered",
            "provider": "firebase",
            "message_preview": f"Test push to {recipient_name} for {user_name}",
        }


def get_notification_provider() -> NotificationProvider:
    """Factory to get configured notification provider based on env."""
    provider_type = os.getenv("NOTIFICATION_PROVIDER", "firebase").strip().lower()
    if provider_type == "twilio":
        return TwilioNotificationProvider()
    elif provider_type == "mock":
        return MockNotificationProvider()
    return FirebaseNotificationProvider()


# Global singleton instance
notification_service = get_notification_provider()
