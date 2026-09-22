"""
Create or promote the CrimeSense administrator account.

Usage (from the backend/ directory):

    python seed_admin.py
    python seed_admin.py --email ops@example.com --password Secret123
"""

import argparse
import os
import sys


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app  # noqa: E402

from config.config import (  # noqa: E402
    DEFAULT_ADMIN_EMAIL,
    DEFAULT_ADMIN_NAME,
    DEFAULT_ADMIN_PASSWORD,
)

from services import auth_service, user_service  # noqa: E402


def seed_admin(name, email, password):
    """Create the ADMIN account, or promote an existing one."""

    with app.app_context():

        existing = user_service.get_user_by_email(
            email
        )

        if existing is not None:

            user = user_service.update_user_role(
                existing.id,
                "ADMIN"
            )

            print(
                f"Promoted existing account "
                f"{user.email} to ADMIN"
            )

            return user

        user = auth_service.create_account(
            name=name,
            email=email,
            password=password,
            role="ADMIN"
        )

        print(f"Created ADMIN account {user.email}")

        return user


def main():

    parser = argparse.ArgumentParser(
        description="Create a CrimeSense ADMIN account."
    )

    parser.add_argument(
        "--name",
        default=DEFAULT_ADMIN_NAME
    )

    parser.add_argument(
        "--email",
        default=DEFAULT_ADMIN_EMAIL
    )

    parser.add_argument(
        "--password",
        default=DEFAULT_ADMIN_PASSWORD
    )

    arguments = parser.parse_args()

    user = seed_admin(
        arguments.name,
        arguments.email,
        arguments.password
    )

    print(f"Role: {user.role}")
    print("Sign in with the email and password above.")


if __name__ == "__main__":
    main()
