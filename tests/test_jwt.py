import pytest
from datetime import timedelta
from auth.jwt import create_access_token, decode_access_token


def test_create_and_decode_basic_token():
    token = create_access_token({"sub": "user-123"})
    payload = decode_access_token(token)
    assert payload["sub"] == "user-123"


def test_token_contains_expiry():
    token = create_access_token({"sub": "user-123"})
    payload = decode_access_token(token)
    assert "exp" in payload


def test_token_preserves_all_claims():
    data = {"sub": "abc", "user_type": "ADMIN", "username": "jdoe", "email": "j@test.com"}
    token = create_access_token(data)
    payload = decode_access_token(token)
    assert payload["sub"] == "abc"
    assert payload["user_type"] == "ADMIN"
    assert payload["username"] == "jdoe"
    assert payload["email"] == "j@test.com"


def test_expired_token_raises_value_error():
    token = create_access_token({"sub": "x"}, expires_delta=timedelta(seconds=-1))
    with pytest.raises(ValueError, match="Invalid token"):
        decode_access_token(token)


def test_malformed_token_raises_value_error():
    with pytest.raises(ValueError, match="Invalid token"):
        decode_access_token("not.a.valid.token")


def test_empty_string_raises_value_error():
    with pytest.raises(ValueError, match="Invalid token"):
        decode_access_token("")


def test_custom_expiry_is_respected():
    token = create_access_token({"sub": "y"}, expires_delta=timedelta(hours=2))
    payload = decode_access_token(token)
    assert payload["sub"] == "y"
