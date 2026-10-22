"""Authentication and role-based authorization dependencies"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from jwt_handler import decode_access_token
from models import User

bearer_scheme = HTTPBearer(auto_error=False)

def authentication_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user( credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme), db: Session = Depends(get_db),) -> User:

    if credentials is None:
        raise authentication_error()

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")

        if not isinstance(user_id, str) or not user_id.isdecimal():
            raise authentication_error()

        user_id = int(user_id)

        if user_id <= 0:
            raise authentication_error()

    except InvalidTokenError as exc:
        raise authentication_error() from exc

    user = db.scalar(
        select(User).where(User.id == user_id)
    )

    if user is None:
        raise authentication_error()

    return user

def require_roles(*allowed_roles: str):
    def role_checker(current_user: User = Depends(get_current_user),) -> User:

        if current_user.role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )

        return current_user

    return role_checker