import os 
from dotenv import load_dotenv

from database import SessionLocal
from models import Role, User
from sqlalchemy import select
from security import hash_password

load_dotenv()

db = SessionLocal()

try:
    role_names = ["L2", "SYSTEM_ADMIN", "ADMIN"]

    for role_name in role_names:
        existing_role = db.scalar(
            select(Role).where(Role.name == role_name)
        )

        if existing_role is None:
            db.add(Role(name=role_name))

    admin_role = db.scalar(
        select(Role).where(Role.name == "ADMIN")
    )

    existing_admin = db.scalar(
        select(User).where(User.username == "admin")
    )

    admin_password = os.getenv("INITIAL_ADMIN_PASSWORD")

    if admin_password is None:
        raise RuntimeError("INITIAL_ADMIN_PASSWORD is not set")

    if admin_role is None:
        raise RuntimeError("ADMIN role does not exist")

    if existing_admin is None:
        admin_user = User(
            username="admin",
            email="admin@doomsday-pager.local",
            password_hash = hash_password(admin_password),
            role=admin_role
        )

        db.add(admin_user)

    db.commit()

except Exception:
    db.rollback()
    raise

finally:
    db.close()

