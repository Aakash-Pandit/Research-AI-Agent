import os
import uuid

# Must be set before any app imports
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_EXPIRE_MINUTES", "60")
os.environ.setdefault("COHERE_API_KEY", "test-cohere-key")
os.environ.setdefault("TAILVY_API_KEY", "test-tavily-key")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test_db")

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from starlette.middleware.authentication import AuthenticationMiddleware

from auth.jwt import create_access_token
from auth.backend import JWTAuthBackend
from database.db import get_db
from users.choices import UserType

TEST_ADMIN_ID = "00000000-0000-0000-0000-000000000001"
TEST_USER_ID = "00000000-0000-0000-0000-000000000002"


def make_db_user(user_id: str, user_type: UserType) -> MagicMock:
    user = MagicMock()
    user.id = uuid.UUID(user_id)
    user.user_type = user_type
    user.email = f"{user_type.value.lower()}@test.com"
    user.first_name = "Test"
    user.last_name = "User"
    user.username = f"{user_type.value.lower()}_user"
    user.phone = "1234567890"
    user.gender = "M"
    user.date_of_birth = "1990-01-01"
    user.password_hash = "$2b$12$placeholder"
    return user


def make_session_cls(user: MagicMock) -> MagicMock:
    """Return a mock SessionLocal that yields `user` from DB queries."""
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)
    mock_session.query.return_value.filter.return_value.first.return_value = user
    return MagicMock(return_value=mock_session)


@pytest.fixture(scope="session")
def fastapi_app():
    from application.app import app
    import auth.apis  # noqa — registers /login
    import users.apis  # noqa — registers /users routes
    app.add_middleware(AuthenticationMiddleware, backend=JWTAuthBackend())
    return app


@pytest.fixture
def admin_token():
    return create_access_token({
        "sub": TEST_ADMIN_ID,
        "user_type": "ADMIN",
        "username": "admin_user",
        "email": "admin@test.com",
    })


@pytest.fixture
def user_token():
    return create_access_token({
        "sub": TEST_USER_ID,
        "user_type": "REGULAR",
        "username": "regular_user",
        "email": "regular@test.com",
    })


@pytest.fixture
def admin_db_user():
    return make_db_user(TEST_ADMIN_ID, UserType.ADMIN)


@pytest.fixture
def regular_db_user():
    return make_db_user(TEST_USER_ID, UserType.REGULAR)


@pytest.fixture
def mock_db():
    """A mock SQLAlchemy session for overriding get_db."""
    return MagicMock()


@pytest.fixture
def client_admin(fastapi_app, admin_db_user, admin_token, mock_db):
    fastapi_app.dependency_overrides[get_db] = lambda: mock_db
    with patch("auth.backend.SessionLocal", make_session_cls(admin_db_user)):
        with TestClient(fastapi_app) as c:
            c.headers.update({"Authorization": f"Bearer {admin_token}"})
            yield c
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def client_user(fastapi_app, regular_db_user, user_token, mock_db):
    fastapi_app.dependency_overrides[get_db] = lambda: mock_db
    with patch("auth.backend.SessionLocal", make_session_cls(regular_db_user)):
        with TestClient(fastapi_app) as c:
            c.headers.update({"Authorization": f"Bearer {user_token}"})
            yield c
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def client_anon(fastapi_app, mock_db):
    fastapi_app.dependency_overrides[get_db] = lambda: mock_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()
