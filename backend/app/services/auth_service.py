from datetime import timedelta

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.core.security import create_access_token, get_password_hash, verify_password

settings = get_settings()

# Demo user store (to be replaced by real persistence)
_FAKE_USER_DB = {
    "admin@example.org": {
        "username": "admin@example.org",
        "full_name": "Demo Admin",
        "hashed_password": get_password_hash("admin123"),
        "roles": ["admin"],
        "is_active": True,
    }
}


def authenticate_user(username: str, password: str) -> dict:
    user = _FAKE_USER_DB.get(username.lower())
    if not user or not user["is_active"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return user


def create_user_token(username: str) -> str:
    token_lifetime = timedelta(minutes=settings.jwt_access_token_expires_minutes)
    return create_access_token(subject=username, expires_delta=token_lifetime)
