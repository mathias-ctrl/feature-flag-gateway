from app.core.config import Settings
from app.core.security import create_access_token, decode_access_token


def test_access_token_round_trip() -> None:
    # Arrange
    settings = Settings(
        jwt_secret="test-secret-with-more-than-32-characters",
        database_url="sqlite+aiosqlite:///:memory:",
    )

    # Act
    token = create_access_token("user-1", "tenant-a", settings)
    payload = decode_access_token(token, settings)

    # Assert
    assert payload.sub == "user-1"
    assert payload.tenant_id == "tenant-a"
