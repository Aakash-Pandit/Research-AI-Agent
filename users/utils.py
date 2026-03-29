from fastapi import HTTPException, Request

from users.choices import UserType


def coerce_user_type(value: str) -> UserType:
    """Convert a string value to UserType enum."""
    normalized = value.strip().upper()
    try:
        return UserType[normalized]
    except KeyError:
        raise HTTPException(status_code=403, detail="Admin access required")


def require_admin(user_type: str) -> None:
    """Raise 403 if user is not an admin."""
    if coerce_user_type(user_type) != UserType.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")


def require_authenticated_user(request: Request):
    """Raise 401 if user is not authenticated."""
    if not request.user or not request.user.is_authenticated:
        raise HTTPException(status_code=401, detail="Authentication required")
    return request.user
