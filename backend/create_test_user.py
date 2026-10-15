
from sqlalchemy import select

from database import SessionLocal
from models import Role, User
from security import hash_password


def create_test_user():
    db = SessionLocal()

    try:
        role = db.scalar(
            select(Role).where(Role.name == "SYSTEM_ADMIN")
        )

        if role is None:
            print("SYSTEM_ADMIN role not found")
            return

        existing_user = db.scalar(
            select(User).where(User.username == "sysadmin_test")
        )

        if existing_user is not None:
            print("Test user already exists")
            return

        password = input("Enter test user password: ")

        if not password:
            print("Password cannot be empty")
            return

        user = User(
            username="sysadmin_test",
            email="sysadmin_test@doomsday-pager.local",
            password_hash=hash_password(password),
            role_id=role.id
        )

        db.add(user)
        db.commit()

        print("Test SYSTEM_ADMIN created successfully")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    create_test_user()
