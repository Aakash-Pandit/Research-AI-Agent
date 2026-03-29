import uuid
import pytest
from unittest.mock import MagicMock

from users.choices import UserType
from tests.conftest import TEST_ADMIN_ID, TEST_USER_ID


def make_orm_user(user_id: str = None, user_type: UserType = UserType.REGULAR):
    user = MagicMock()
    user.id = uuid.UUID(user_id or str(uuid.uuid4()))
    user.first_name = "jane"
    user.last_name = "doe"
    user.username = "janedoe"
    user.email = "jane@test.com"
    user.phone = "5551234567"
    user.gender = "F"
    user.user_type = user_type
    user.date_of_birth = "1995-06-15"
    user.password_hash = "hashed"
    return user


NEW_USER_PAYLOAD = {
    "first_name": "John",
    "last_name": "Smith",
    "username": "johnsmith",
    "password": "strongpass123",
    "email": "john@test.com",
    "phone": "5559876543",
    "gender": "M",
    "user_type": "REGULAR",
    "date_of_birth": "1990-01-01T00:00:00",
}


class TestCreateUser:
    def test_create_user_success(self, client_anon, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        orm_user = make_orm_user(user_type=UserType.REGULAR)
        mock_db.refresh.side_effect = lambda u: None

        with pytest.MonkeyPatch().context() as mp:
            import users.apis as apis_module
            original_user_cls = None

            resp = client_anon.post("/users", json=NEW_USER_PAYLOAD)

        assert resp.status_code in (200, 201)

    def test_duplicate_username_returns_409(self, client_anon, mock_db):
        existing = make_orm_user()
        mock_db.query.return_value.filter.return_value.first.return_value = existing

        resp = client_anon.post("/users", json=NEW_USER_PAYLOAD)

        assert resp.status_code == 409
        assert "username" in resp.json()["detail"].lower()

    def test_missing_required_field_returns_422(self, client_anon):
        payload = {k: v for k, v in NEW_USER_PAYLOAD.items() if k != "email"}
        resp = client_anon.post("/users", json=payload)
        assert resp.status_code == 422


class TestGetUsers:
    def test_get_users_requires_auth(self, client_anon):
        resp = client_anon.get("/users")
        assert resp.status_code == 401

    def test_get_users_as_admin_returns_list(self, client_admin, mock_db):
        orm_users = [make_orm_user(user_type=UserType.REGULAR)]
        mock_db.query.return_value.order_by.return_value.all.return_value = orm_users

        resp = client_admin.get("/users")

        assert resp.status_code == 200
        body = resp.json()
        assert "users" in body
        assert "total" in body

    def test_get_users_as_regular_returns_403(self, client_user):
        resp = client_user.get("/users")
        assert resp.status_code == 403


class TestGetUser:
    def test_get_own_user_returns_200(self, client_user, mock_db):
        orm_user = make_orm_user(user_id=TEST_USER_ID)
        mock_db.query.return_value.filter.return_value.first.return_value = orm_user

        resp = client_user.get(f"/users/{TEST_USER_ID}")

        assert resp.status_code == 200
        assert resp.json()["id"] == TEST_USER_ID

    def test_get_other_user_returns_403(self, client_user):
        other_id = "00000000-0000-0000-0000-000000000099"
        resp = client_user.get(f"/users/{other_id}")
        assert resp.status_code == 403


class TestDeleteUser:
    def test_delete_existing_user(self, client_admin, mock_db):
        orm_user = make_orm_user(user_id=TEST_ADMIN_ID)
        mock_db.query.return_value.filter.return_value.first.return_value = orm_user

        resp = client_admin.delete(f"/users/{TEST_ADMIN_ID}")

        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_delete_nonexistent_user_returns_404(self, client_admin, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        resp = client_admin.delete(f"/users/{TEST_ADMIN_ID}")

        assert resp.status_code == 404
