import pytest
from auth.passwords import hash_password, verify_password


def test_hash_returns_string():
    result = hash_password("mysecret")
    assert isinstance(result, str)


def test_hash_starts_with_bcrypt_prefix():
    result = hash_password("mysecret")
    assert result.startswith("$2b$")


def test_verify_correct_password():
    hashed = hash_password("correct_password")
    assert verify_password("correct_password", hashed) is True


def test_verify_wrong_password():
    hashed = hash_password("correct_password")
    assert verify_password("wrong_password", hashed) is False


def test_same_password_produces_different_hashes():
    h1 = hash_password("same_password")
    h2 = hash_password("same_password")
    assert h1 != h2


def test_password_truncated_at_72_bytes():
    long_password = "a" * 100
    hashed = hash_password(long_password)
    # Both are truncated to 72 bytes so they should match
    assert verify_password("a" * 72, hashed) is True


def test_empty_password_hashes_and_verifies():
    hashed = hash_password("")
    assert verify_password("", hashed) is True
    assert verify_password("notempty", hashed) is False
