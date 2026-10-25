"""
email_service.py
================
Email delivery service for CrimeSense account verification and password recovery.
Supports standard SMTP providers (Gmail, SendGrid, Mailgun, AWS SES, Mailtrap)
and graceful development fallback when SMTP credentials are not configured.
"""

from __future__ import annotations

import os
import smtplib
import secrets
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Tuple

logger = logging.getLogger("crimesense.email")


def generate_secure_token() -> Tuple[str, str]:
    """
    Generate a high-entropy URL-safe token and its SHA-256 hash.
    The raw token is emailed to the user; only the hash is stored in the database.
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    return raw_token, token_hash


def hash_token(raw_token: str) -> str:
    """Compute the SHA-256 hash of a provided raw token."""
    if not raw_token:
        return ""
    return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()


class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "").strip()
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "").strip()
        self.smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").strip().lower() in ("true", "1", "yes")
        self.from_email = os.getenv("SMTP_FROM_EMAIL", "no-reply@crimesense.org").strip()
        self.from_name = os.getenv("SMTP_FROM_NAME", "CrimeSense Security").strip()
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")

    def is_smtp_configured(self) -> bool:
        """Check whether live SMTP credentials have been provided."""
        return bool(self.smtp_host and self.smtp_user and self.smtp_password)

    def _send_smtp_message(self, recipient_email: str, subject: str, text_content: str, html_content: str) -> bool:
        """Dispatch an email via smtplib to the configured SMTP host."""
        if not self.is_smtp_configured():
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = recipient_email

        msg.attach(MIMEText(text_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=15) as server:
                if self.smtp_use_tls:
                    server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, [recipient_email], msg.as_string())
            logger.info(f"[EmailService] Email successfully dispatched to {recipient_email} via SMTP")
            return True
        except Exception as e:
            logger.error(f"[EmailService] Failed to send email via SMTP to {recipient_email}: {e}")
            return False

    def send_verification_email(self, user_email: str, user_name: str, raw_token: str) -> Dict[str, Any]:
        """
        Send an email verification link to a user.
        If SMTP is not configured, logs the verification link for local development.
        """
        verify_url = f"{self.frontend_url}/verify-email?token={raw_token}"
        subject = "CrimeSense — Verify your email address"

        text_content = (
            f"Hello {user_name or 'Citizen'},\n\n"
            f"Thank you for registering with CrimeSense — Real-Time Crime Analysis & Personal Safety Platform.\n\n"
            f"Please verify your email address by opening the following link:\n"
            f"{verify_url}\n\n"
            f"This link will expire in 24 hours. If you did not create this account, please ignore this email.\n\n"
            f"Stay safe,\n"
            f"The CrimeSense Team"
        )

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #020617; color: #f8fafc; padding: 24px; }}
            .container {{ max-width: 540px; margin: 0 auto; background: #0f172a; border: 1px solid #1e293b; border-radius: 16px; padding: 32px; }}
            .header {{ text-align: center; margin-bottom: 24px; }}
            .logo {{ font-size: 24px; font-weight: bold; color: #38bdf8; }}
            .btn {{ display: inline-block; background: #0284c7; color: #ffffff !important; padding: 12px 28px; border-radius: 8px; font-weight: 600; text-decoration: none; margin: 20px 0; }}
            .footer {{ font-size: 12px; color: #64748b; margin-top: 24px; border-top: 1px solid #1e293b; padding-top: 16px; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <div class="logo">🛡️ CrimeSense</div>
              <p style="color: #94a3b8; font-size: 14px; margin-top: 4px;">Real-Time Crime Analysis & Personal Safety</p>
            </div>
            <p>Hello <strong>{user_name or 'Citizen'}</strong>,</p>
            <p>Thank you for registering with CrimeSense. Please verify your email address to confirm your account and activate automated safety alerts.</p>
            <div style="text-align: center;">
              <a href="{verify_url}" class="btn">Verify Email Address</a>
            </div>
            <p style="font-size: 13px; color: #94a3b8;">Or copy and paste this link into your browser:<br>
              <a href="{verify_url}" style="color: #38bdf8; word-break: break-all;">{verify_url}</a>
            </p>
            <div class="footer">
              <p>This verification link expires in 24 hours. If you did not create a CrimeSense account, you can safely ignore this message.</p>
            </div>
          </div>
        </body>
        </html>
        """

        if self.is_smtp_configured():
            sent = self._send_smtp_message(user_email, subject, text_content, html_content)
            return {
                "success": sent,
                "provider": "smtp",
                "sent": sent,
                "message": "Verification email sent successfully." if sent else "Failed to dispatch email via SMTP."
            }
        else:
            logger.warning(
                f"[EmailService] [DEV FALLBACK] Verification email for {user_email}:\n"
                f"Verify URL: {verify_url}"
            )
            return {
                "success": True,
                "provider": "mock_development",
                "sent": False,
                "link": verify_url,
                "message": "Email logged in development mode. Configure SMTP credentials for live delivery."
            }

    def send_password_reset_email(self, user_email: str, user_name: str, raw_token: str) -> Dict[str, Any]:
        """
        Send a password reset link to a user.
        If SMTP is not configured, logs the reset link for local development.
        """
        reset_url = f"{self.frontend_url}/reset-password?token={raw_token}"
        subject = "CrimeSense — Password Reset Request"

        text_content = (
            f"Hello {user_name or 'Citizen'},\n\n"
            f"We received a request to reset your CrimeSense account password.\n\n"
            f"Please click the following link to set a new password:\n"
            f"{reset_url}\n\n"
            f"This link is valid for 1 hour. If you did not request a password reset, please ignore this email.\n\n"
            f"The CrimeSense Team"
        )

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #020617; color: #f8fafc; padding: 24px; }}
            .container {{ max-width: 540px; margin: 0 auto; background: #0f172a; border: 1px solid #1e293b; border-radius: 16px; padding: 32px; }}
            .header {{ text-align: center; margin-bottom: 24px; }}
            .logo {{ font-size: 24px; font-weight: bold; color: #38bdf8; }}
            .btn {{ display: inline-block; background: #e11d48; color: #ffffff !important; padding: 12px 28px; border-radius: 8px; font-weight: 600; text-decoration: none; margin: 20px 0; }}
            .footer {{ font-size: 12px; color: #64748b; margin-top: 24px; border-top: 1px solid #1e293b; padding-top: 16px; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <div class="logo">🛡️ CrimeSense</div>
              <p style="color: #94a3b8; font-size: 14px; margin-top: 4px;">Password Reset Assistance</p>
            </div>
            <p>Hello <strong>{user_name or 'Citizen'}</strong>,</p>
            <p>We received a request to reset your CrimeSense password. Click the button below to choose a new password:</p>
            <div style="text-align: center;">
              <a href="{reset_url}" class="btn">Reset My Password</a>
            </div>
            <p style="font-size: 13px; color: #94a3b8;">Or copy and paste this link into your browser:<br>
              <a href="{reset_url}" style="color: #38bdf8; word-break: break-all;">{reset_url}</a>
            </p>
            <div class="footer">
              <p>This password reset link expires in 1 hour. If you did not request a password reset, no action is needed; your password remains unchanged.</p>
            </div>
          </div>
        </body>
        </html>
        """

        if self.is_smtp_configured():
            sent = self._send_smtp_message(user_email, subject, text_content, html_content)
            return {
                "success": sent,
                "provider": "smtp",
                "sent": sent,
                "message": "Password reset email sent successfully." if sent else "Failed to dispatch email via SMTP."
            }
        else:
            logger.warning(
                f"[EmailService] [DEV FALLBACK] Password reset email for {user_email}:\n"
                f"Reset URL: {reset_url}"
            )
            return {
                "success": True,
                "provider": "mock_development",
                "sent": False,
                "link": reset_url,
                "message": "Email logged in development mode. Configure SMTP credentials for live delivery."
            }


email_service = EmailService()
