from __future__ import annotations

import argparse
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.auth import hash_password  # noqa: E402
from app.database import SessionLocal, init_db  # noqa: E402
from app.models import User  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create or update an instructor/TA account.")
    parser.add_argument("--email", required=True, help="Account email address.")
    parser.add_argument("--password", required=True, help="Initial password.")
    parser.add_argument("--full-name", default="Course Instructor", help="Display name.")
    parser.add_argument("--role", choices=["instructor", "ta"], default="instructor", help="Staff role.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    email = args.email.strip().lower()
    if "@" not in email:
        raise SystemExit("Email must contain '@'.")
    if len(args.password) < 10:
        raise SystemExit("Password must be at least 10 characters.")

    init_db()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.full_name = args.full_name
            user.role = args.role
            user.hashed_password = hash_password(args.password)
            user.is_active = True
            user.must_change_password = False
            action = "Updated"
        else:
            user = User(
                email=email,
                full_name=args.full_name,
                role=args.role,
                hashed_password=hash_password(args.password),
                is_active=True,
                must_change_password=False,
            )
            db.add(user)
            action = "Created"
        db.commit()
    finally:
        db.close()

    print(f"{action} {args.role} account: {email}")


if __name__ == "__main__":
    main()
