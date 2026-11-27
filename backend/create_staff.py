"""Create a support-agent account interactively: python -m backend.create_staff."""
from getpass import getpass

from sqlalchemy import select

from backend.app.auth import hash_password
from backend.app.db import Base, SessionLocal, engine
from backend.app.models import StaffUser


def main() -> None:
    Base.metadata.create_all(bind=engine)
    email = input("Staff email: ").strip().lower()
    if not email or "@" not in email:
        raise SystemExit("Enter a valid email address.")
    password = getpass("Password (at least 12 characters): ")
    confirmation = getpass("Confirm password: ")
    if len(password) < 12:
        raise SystemExit("Password must contain at least 12 characters.")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")

    with SessionLocal() as db:
        existing = db.execute(select(StaffUser).where(StaffUser.email == email)).scalar_one_or_none()
        if existing:
            raise SystemExit("A staff account with that email already exists.")
        staff = StaffUser(email=email, password_hash=hash_password(password), is_active=True)
        db.add(staff)
        db.commit()
        print(f"Created support staff account for {email}.")


if __name__ == "__main__":
    main()
