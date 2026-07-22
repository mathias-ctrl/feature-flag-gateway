import pytest

from app.core.config import Settings
from app.core.errors import UnauthorizedError
from app.core.security import (
    decode_access_token,
    hash_password,
    verify_password,
)


def make_settings() -> Settings:
    return Settings(
        jwt_secret="test-secret-with-more-than-32-characters",
        database_url="sqlite+aiosqlite:///:memory:",
    )


def test_password_hash_can_be_verified() -> None:
    # Arrange
    password = "strong-password-123"

    # Act
    password_hash = hash_password(password)

    # Assert
    assert password_hash != password
    assert verify_password(password, password_hash) is True


def test_wrong_password_is_rejected() -> None:
    # Arrange
    password_hash = hash_password("correct-password")

    # Act
    result = verify_password("wrong-password", password_hash)

    # Assert
    assert result is False


def test_invalid_access_token_raises_unauthorized() -> None:
    # Arrange
    settings = make_settings()

    # Act / Assert
    with pytest.raises(
        UnauthorizedError,
        match="Invalid or expired access token",
    ):
        decode_access_token("invalid-token", settings)
