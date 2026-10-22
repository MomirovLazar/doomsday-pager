from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import ExpiredSignatureError, InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from jwt_handler import decode_access_token
from models import User

bearer_scheme = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)) -> User:

    token = credentials.credentials

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )

        user_id = int(user_id)

    except (ExpiredSignatureError, InvalidTokenError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user = db.scalar(
        select(User).where(User.id == user_id)
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    return user

def require_roles(*allowed_roles: str):

    def role_checker(current_user: User = Depends(get_current_user)) -> User:

        if current_user.role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action"
            )

        return current_user

    return role_checker
