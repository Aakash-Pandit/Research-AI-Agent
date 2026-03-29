import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException

from users.choices import UserType
from users.utils import coerce_user_type, require_admin, require_authenticated_user


class TestCoerceUserType:
    def test_admin_string(self):
        assert coerce_user_type("ADMIN") == UserType.ADMIN

    def test_regular_string(self):
        assert coerce_user_type("REGULAR") == UserType.REGULAR

    def test_lowercase_input(self):
        assert coerce_user_type("admin") == UserType.ADMIN

    def test_mixed_case_input(self):
        assert coerce_user_type("Admin") == UserType.ADMIN

    def test_invalid_value_raises_403(self):
        with pytest.raises(HTTPException) as exc:
            coerce_user_type("SUPERUSER")
        assert exc.value.status_code == 403


class TestRequireAdmin:
    def test_admin_passes(self):
        require_admin("ADMIN")  # should not raise

    def test_regular_raises_403(self):
        with pytest.raises(HTTPException) as exc:
            require_admin("REGULAR")
        assert exc.value.status_code == 403

    def test_invalid_type_raises_403(self):
        with pytest.raises(HTTPException) as exc:
            require_admin("UNKNOWN")
        assert exc.value.status_code == 403


class TestRequireAuthenticatedUser:
    def test_authenticated_user_returns_user(self):
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_request = MagicMock()
        mock_request.user = mock_user

        result = require_authenticated_user(mock_request)
        assert result is mock_user

    def test_unauthenticated_raises_401(self):
        mock_user = MagicMock()
        mock_user.is_authenticated = False
        mock_request = MagicMock()
        mock_request.user = mock_user

        with pytest.raises(HTTPException) as exc:
            require_authenticated_user(mock_request)
        assert exc.value.status_code == 401

    def test_no_user_raises_401(self):
        mock_request = MagicMock()
        mock_request.user = None

        with pytest.raises(HTTPException) as exc:
            require_authenticated_user(mock_request)
        assert exc.value.status_code == 401
