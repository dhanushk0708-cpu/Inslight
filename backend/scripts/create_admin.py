"""
Secure Initial Administrator Setup Script for INSLIGHT.
Usage (from backend/):
  python scripts/create_admin.py --email admin@inslight.ai --name "System Admin"
Prompts interactively for a password (never hardcodes a default password).
"""
import argparse
import getpass
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, init_db
from app.core.security import hash_password
from app.models.user import User


def main():
    parser = argparse.ArgumentParser(description="Create or promote an INSLIGHT Admin user.")
    parser.add_argument("--email", required=True, help="Admin user email address")
    parser.add_argument("--name", default="Inslight Admin", help="Admin display name (for new users)")
    parser.add_argument("--password", default=None, help="Optional password (if omitted, prompts securely)")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        email = args.email.strip().lower()
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            existing.role = "admin"
            existing.is_active = True
            db.commit()
            print(f"[OK] Promoted existing user '{email}' to role='admin'.")
            return

        password = args.password or getpass.getpass("Enter strong admin password (min 8 chars): ")
        if len(password) < 8:
            print("[ERROR] Password must be at least 8 characters.")
            sys.exit(1)

        admin = User(
            name=args.name.strip(),
            email=email,
            hashed_password=hash_password(password),
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f"[OK] Created new admin account '{email}' (id={admin.id}).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
