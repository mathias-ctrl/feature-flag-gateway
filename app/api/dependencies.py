from typing import Annotated

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings
from app.core.errors import UnauthorizedError
from app.core.security import TokenPayload, decode_access_token
from app.services.flags import FeatureFlagService
from app.services.idempotency import IdempotencyStore

bearer = HTTPBearer(auto_error=False)


def get_flag_service() -> FeatureFlagService:
    raise RuntimeError("Dependency must be overridden by application factory")


def get_idempotency_store() -> IdempotencyStore:
    raise RuntimeError("Dependency must be overridden by application factory")


def get_current_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenPayload:
    if credentials is None:
        raise UnauthorizedError("Missing bearer token")
    return decode_access_token(credentials.credentials, settings)


def get_tenant_id(
    token: Annotated[TokenPayload, Depends(get_current_token)],
    tenant_header: Annotated[str | None, Header(alias="X-Tenant-ID")] = None,
) -> str:
    if tenant_header is not None and tenant_header != token.tenant_id:
        raise UnauthorizedError("Token does not grant access to this tenant")
    return token.tenant_id
