"""Centralized application configuration"""

import os

from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    cors_origins: tuple[str, ...]

def load_settings() -> Settings:
    database_url = os.getenv("DATABASE_URL")
    jwt_secret_key = os.getenv("JWT_SECRET_KEY")
    jwt_algorithm = os.getenv("JWT_ALGORITHM")
    expire_minutes = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")

    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    if not jwt_secret_key:
        raise RuntimeError("JWT_SECRET_KEY is not set")

    if not jwt_algorithm:
        raise RuntimeError("JWT_ALGORITHM is not set")

    if not expire_minutes:
        raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES is not set")

    try:
        expire_minutes = int(expire_minutes)

    except ValueError as exc:
        raise RuntimeError(
            "ACCESS_TOKEN_EXPIRE_MINUTES must be an integer"
        ) from exc

    if expire_minutes <= 0:
        raise RuntimeError(
            "ACCESS_TOKEN_EXPIRE_MINUTES must be greater than zero"
        )

    cors_origins_list = []

    origins = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173"
    )

    for origin in origins.split(","):
        origin = origin.strip()

        if origin:
            cors_origins_list.append(origin)

    cors_origins = tuple(cors_origins_list)

    return Settings(
        database_url=database_url,
        jwt_secret_key=jwt_secret_key,
        jwt_algorithm=jwt_algorithm,
        access_token_expire_minutes=expire_minutes,
        cors_origins=cors_origins
    )

settings = load_settings()