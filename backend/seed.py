"""Initialize database roles and the default administrator"""

import os

from dotenv import load_dotenv
from sqlalchemy import select

from constants import UserRole
from database import SessionLocal
from models import Role, User
from security import hash_password


def seed_database() -> None:
    load_dotenv()

    db = SessionLocal()

    try:
        for role_name in UserRole:
            existing_role = db.scalar(
                select(Role).where(Role.name == role_name)
            )

            if existing_role is None:
                db.add(Role(name=role_name))

        db.flush()

        admin_role = db.scalar(
            select(Role).where(Role.name == UserRole.ADMIN)
        )

        if admin_role is None:
            raise RuntimeError("ADMIN role does not exist")

        existing_admin = db.scalar(
            select(User).where(User.username == "admin")
        )

        admin_password = os.getenv("INITIAL_ADMIN_PASSWORD")

        if admin_password is None:
            raise RuntimeError("INITIAL_ADMIN_PASSWORD is not set")

        if existing_admin is None:
            admin_user = User(
                username="admin",
                email="admin@doomsday-pager.local",
                password_hash=hash_password(admin_password),
                role=admin_role,
            )

            db.add(admin_user)

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
