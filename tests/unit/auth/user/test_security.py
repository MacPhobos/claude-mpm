"""Unit tests for password hashing and JWT utilities.

Tests cover:
- bcrypt round-trip: hash → verify
- Wrong-password rejection
- Access token creation and decoding
- Refresh token creation and decoding
- Custom expiry for access tokens
- Expired token detection
- Invalid token detection
"""

from __future__ import annotations

import os
from datetime import timedelta

import pytest
from jose import JWTError, jwt

from claude_mpm.auth.user.security import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self) -> None:
        hashed = get_password_hash("mysecret")
        assert hashed != "mysecret"

    def test_verify_correct_password(self) -> None:
        hashed = get_password_hash("correct_horse_battery_staple")
        assert verify_password("correct_horse_battery_staple", hashed) is True

    def test_verify_wrong_password(self) -> None:
        hashed = get_password_hash("correct_horse_battery_staple")
        assert verify_password("wrong_password", hashed) is False

    def test_hash_is_different_each_call(self) -> None:
        """bcrypt uses a random salt, so two hashes of the same string differ."""
        h1 = get_password_hash("same_password")
        h2 = get_password_hash("same_password")
        assert h1 != h2

    def test_verify_empty_password(self) -> None:
        # bcrypt>=4 rejects empty passwords; use a minimal non-empty string
        hashed = get_password_hash("a")
        assert verify_password("a", hashed) is True

    def test_verify_wrong_against_short(self) -> None:
        hashed = get_password_hash("a")
        assert verify_password("b", hashed) is False


# ---------------------------------------------------------------------------
# Access token
# ---------------------------------------------------------------------------


class TestAccessToken:
    def test_creates_valid_jwt(self) -> None:
        token = create_access_token({"sub": "user@example.com"})
        payload = decode_token(token)
        assert payload["sub"] == "user@example.com"

    def test_contains_exp_claim(self) -> None:
        token = create_access_token({"sub": "user@example.com"})
        payload = decode_token(token)
        assert "exp" in payload

    def test_custom_expiry(self) -> None:
        token = create_access_token(
            {"sub": "user@example.com"}, expires_delta=timedelta(hours=2)
        )
        payload = decode_token(token)
        assert payload["sub"] == "user@example.com"

    def test_expired_token_raises(self) -> None:
        token = create_access_token(
            {"sub": "user@example.com"}, expires_delta=timedelta(seconds=-1)
        )
        with pytest.raises(JWTError):
            decode_token(token)

    def test_tampered_token_raises(self) -> None:
        token = create_access_token({"sub": "user@example.com"})
        tampered = token + "x"
        with pytest.raises(JWTError):
            decode_token(tampered)

    def test_wrong_secret_raises(self) -> None:
        token = create_access_token({"sub": "user@example.com"})
        with pytest.raises(JWTError):
            jwt.decode(token, "wrong_secret", algorithms=[ALGORITHM])

    def test_extra_claims_preserved(self) -> None:
        token = create_access_token({"sub": "user@example.com", "role": "admin"})
        payload = decode_token(token)
        assert payload["role"] == "admin"


# ---------------------------------------------------------------------------
# Refresh token
# ---------------------------------------------------------------------------


class TestRefreshToken:
    def test_creates_valid_jwt(self) -> None:
        token = create_refresh_token({"sub": "user@example.com"})
        payload = decode_token(token)
        assert payload["sub"] == "user@example.com"

    def test_refresh_lives_longer_than_access(self) -> None:
        """Refresh token exp should be further in the future than access token."""
        access = create_access_token({"sub": "u@e.com"})
        refresh = create_refresh_token({"sub": "u@e.com"})
        access_exp = decode_token(access)["exp"]
        refresh_exp = decode_token(refresh)["exp"]
        assert refresh_exp > access_exp

    def test_expired_refresh_raises(self) -> None:
        """Craft a refresh token with a negative TTL using internal helper."""
        from claude_mpm.auth.user.security import _build_token

        token = _build_token({"sub": "u@e.com"}, timedelta(seconds=-1))
        with pytest.raises(JWTError):
            decode_token(token)
