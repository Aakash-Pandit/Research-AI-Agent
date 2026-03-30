from fastapi import HTTPException

from users.choices import UserType


def coerce_user_type(value: str) -> UserType:
    normalized = value.strip().upper()
    try:
        return UserType[normalized]
    except KeyError:
        raise HTTPException(status_code=403, detail="Admin access required")


def require_admin(user_type: str) -> None:
    if coerce_user_type(user_type) != UserType.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
