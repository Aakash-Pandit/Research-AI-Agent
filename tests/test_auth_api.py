import pytest
from unittest.mock import MagicMock, patch

from auth.passwords import hash_password


def make_db_user_with_password(username: str, password: str) -> MagicMock:
    user = MagicMock()
    user.id = "00000000-0000-0000-0000-000000000001"
    user.username = username
    user.password_hash = hash_password(password)
    user.user_type = "REGULAR"
    user.email = f"{username}@test.com"
    return user


class TestLoginEndpoint:
    def test_valid_credentials_return_token(self, client_anon, mock_db):
        db_user = make_db_user_with_password("johndoe", "secret123")
        mock_db.query.return_value.filter.return_value.first.return_value = db_user

        resp = client_anon.post("/login", json={"username": "johndoe", "password": "secret123"})

        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_wrong_password_returns_401(self, client_anon, mock_db):
        db_user = make_db_user_with_password("johndoe", "correct_pass")
        mock_db.query.return_value.filter.return_value.first.return_value = db_user

        resp = client_anon.post("/login", json={"username": "johndoe", "password": "wrong_pass"})

        assert resp.status_code == 401

    def test_unknown_username_returns_401(self, client_anon, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        resp = client_anon.post("/login", json={"username": "nobody", "password": "pass"})

        assert resp.status_code == 401

    def test_missing_password_returns_422(self, client_anon):
        resp = client_anon.post("/login", json={"username": "user"})
        assert resp.status_code == 422

    def test_missing_username_returns_422(self, client_anon):
        resp = client_anon.post("/login", json={"password": "pass"})
        assert resp.status_code == 422

    def test_returned_token_is_decodable(self, client_anon, mock_db):
        from auth.jwt import decode_access_token

        db_user = make_db_user_with_password("alice", "pass123")
        mock_db.query.return_value.filter.return_value.first.return_value = db_user

        resp = client_anon.post("/login", json={"username": "alice", "password": "pass123"})
        token = resp.json()["access_token"]

        payload = decode_access_token(token)
        assert payload["username"] == "alice"
        assert payload["email"] == "alice@test.com"
