from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
from pydantic import BaseModel

from app.core.config import Settings
from app.core.errors import UnauthorizedError


class TokenPayload(BaseModel):
    sub: str
    tenant_id: str
    exp: int


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_access_token(
    subject: str,
    tenant_id: str,
    settings: Settings,
) -> str:
    expires_at = datetime.now(UTC) + timedelta(
        minutes=settings.jwt_expiration_minutes,
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "tenant_id": tenant_id,
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings) -> TokenPayload:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return TokenPayload.model_validate(payload)
    except (jwt.InvalidTokenError, ValueError) as error:
        raise UnauthorizedError("Invalid or expired access token") from error
