"""Unit tests for security utilities."""
from app.core.security import hash_password, verify_password, create_access_token, decode_token


def test_password_hashing():
    hashed = hash_password("mysecretpassword")
    assert hashed != "mysecretpassword"
    assert verify_password("mysecretpassword", hashed)
    assert not verify_password("wrongpassword", hashed)


def test_token_creation_and_decode():
    token = create_access_token(subject=42)
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "42"


def test_invalid_token():
    result = decode_token("this.is.not.valid")
    assert result is None


def test_tampered_token():
    token = create_access_token(subject=1)
    tampered = token[:-5] + "XXXXX"
    assert decode_token(tampered) is None
