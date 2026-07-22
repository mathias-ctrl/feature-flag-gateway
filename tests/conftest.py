from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.dependencies import (
    get_current_token,
    get_flag_service,
    get_idempotency_store,
)
from app.core.config import Settings
from app.core.security import TokenPayload
from app.domain.models import Base
from app.infrastructure.cache import CachedFlag
from app.infrastructure.unit_of_work import UnitOfWork
from app.main import create_app
from app.services.flags import FeatureFlagService


class FakeCache:
    def __init__(self) -> None:
        self.values: dict[str, CachedFlag] = {}

    @staticmethod
    def _key(tenant_id: str, environment: str, key: str) -> str:
        return f"{tenant_id}:{environment}:{key}"

    async def get(self, tenant_id: str, environment: str, key: str) -> CachedFlag | None:
        return self.values.get(self._key(tenant_id, environment, key))

    async def set(self, tenant_id: str, environment: str, key: str, value: CachedFlag) -> None:
        self.values[self._key(tenant_id, environment, key)] = value

    async def delete(self, tenant_id: str, environment: str, key: str) -> None:
        self.values.pop(self._key(tenant_id, environment, key), None)


class FakeBroker:
    def __init__(self) -> None:
        self.messages: list[str] = []

    async def publish(self, tenant_id: str, payload: str) -> None:
        self.messages.append(payload)

    async def subscribe(self, tenant_id: str):  # type: ignore[no-untyped-def]
        if False:
            yield tenant_id


class FakeIdempotency:
    async def acquire(self, tenant_id: str, token: str, ttl_seconds: int = 300) -> None:
        return None


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/15",
        jwt_secret="test-secret-with-more-than-32-characters",
    )
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    service = FeatureFlagService(UnitOfWork, session_factory, FakeCache(), FakeBroker())
    app = create_app(settings)
    app.dependency_overrides[get_flag_service] = lambda: service
    app.dependency_overrides[get_idempotency_store] = lambda: FakeIdempotency()
    app.dependency_overrides[get_current_token] = lambda: TokenPayload(
        sub="user-1",
        tenant_id="tenant-a",
        exp=4_102_444_800,
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as test_client:
        yield test_client
    await engine.dispose()
