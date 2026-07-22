from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.errors import ConflictError, EntityNotFoundError
from app.domain.models import FeatureFlag
from app.domain.schemas import FlagCreate, FlagUpdate
from app.infrastructure.cache import CachedFlag
from app.services.flags import FeatureFlagService


def make_flag(
    *,
    enabled: bool = True,
    key: str = "checkout.v2",
) -> FeatureFlag:
    now = datetime.now(UTC)
    return FeatureFlag(
        id=uuid4(),
        tenant_id="tenant-a",
        environment="production",
        key=key,
        enabled=enabled,
        description="Test flag",
        created_at=now,
        updated_at=now,
    )


class FakeCache:
    def __init__(self, cached: CachedFlag | None = None) -> None:
        self.cached = cached
        self.set_calls: list[tuple[str, str, str, CachedFlag]] = []

    async def get(
        self,
        tenant_id: str,
        environment: str,
        key: str,
    ) -> CachedFlag | None:
        return self.cached

    async def set(
        self,
        tenant_id: str,
        environment: str,
        key: str,
        value: CachedFlag,
    ) -> None:
        self.cached = value
        self.set_calls.append(
            (tenant_id, environment, key, value)
        )

    async def delete(
        self,
        tenant_id: str,
        environment: str,
        key: str,
    ) -> None:
        self.cached = None


class FakeBroker:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    async def publish(self, tenant_id: str, payload: str) -> None:
        self.messages.append((tenant_id, payload))

    async def subscribe(self, tenant_id: str):  # type: ignore[no-untyped-def]
        yield tenant_id


class FakeSession:
    def __init__(self) -> None:
        self.refreshed: list[FeatureFlag] = []

    async def refresh(self, flag: FeatureFlag) -> None:
        self.refreshed.append(flag)


class FakeRepository:
    def __init__(
        self,
        *,
        flag: FeatureFlag | None = None,
        rows: list[FeatureFlag] | None = None,
        add_error: Exception | None = None,
    ) -> None:
        self.flag = flag
        self.rows = rows or []
        self.add_error = add_error

    async def add(self, flag: FeatureFlag) -> FeatureFlag:
        if self.add_error is not None:
            raise self.add_error
        if flag.id is None:
            flag.id = uuid4()
        return flag

    async def get_by_key(
        self,
        tenant_id: str,
        environment: str,
        key: str,
    ) -> FeatureFlag | None:
        return self.flag

    async def list_page(
        self,
        tenant_id: str,
        environment: str,
        limit: int,
        cursor: Any,
    ) -> list[FeatureFlag]:
        return self.rows


class FakeUnitOfWork:
    repository = FakeRepository()
    commits = 0

    def __init__(self, session_factory: object) -> None:
        self.flags = self.repository
        self.session = FakeSession()

    async def __aenter__(self) -> "FakeUnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: object,
        exc_value: object,
        traceback: object,
    ) -> None:
        return None

    async def commit(self) -> None:
        type(self).commits += 1


def make_service(
    cache: FakeCache,
    broker: FakeBroker,
) -> FeatureFlagService:
    return FeatureFlagService(
        FakeUnitOfWork,  # type: ignore[arg-type]
        object(),
        cache,
        broker,
    )


async def test_evaluate_returns_cached_value() -> None:
    # Arrange
    cache = FakeCache(CachedFlag(enabled=True))
    service = make_service(cache, FakeBroker())

    # Act
    result = await service.evaluate(
        "tenant-a",
        "production",
        "checkout.v2",
    )

    # Assert
    assert result.enabled is True
    assert result.source == "cache"


async def test_evaluate_loads_database_and_populates_cache() -> None:
    # Arrange
    flag = make_flag(enabled=False)
    FakeUnitOfWork.repository = FakeRepository(flag=flag)
    cache = FakeCache()
    service = make_service(cache, FakeBroker())

    # Act
    result = await service.evaluate(
        "tenant-a",
        "production",
        "checkout.v2",
    )

    # Assert
    assert result.enabled is False
    assert result.source == "database"
    assert cache.cached == CachedFlag(enabled=False)


async def test_evaluate_missing_flag_raises_not_found() -> None:
    # Arrange
    FakeUnitOfWork.repository = FakeRepository(flag=None)
    service = make_service(FakeCache(), FakeBroker())

    # Act / Assert
    with pytest.raises(
        EntityNotFoundError,
        match="Feature flag not found",
    ):
        await service.evaluate(
            "tenant-a",
            "production",
            "missing",
        )


async def test_update_missing_flag_raises_not_found() -> None:
    # Arrange
    FakeUnitOfWork.repository = FakeRepository(flag=None)
    service = make_service(FakeCache(), FakeBroker())
    update = FlagUpdate(enabled=False, description=None)

    # Act / Assert
    with pytest.raises(
        EntityNotFoundError,
        match="Feature flag not found",
    ):
        await service.update(
            "tenant-a",
            "production",
            "missing",
            update,
        )


async def test_update_synchronizes_cache_and_broker() -> None:
    # Arrange
    flag = make_flag(enabled=False)
    FakeUnitOfWork.repository = FakeRepository(flag=flag)
    cache = FakeCache()
    broker = FakeBroker()
    service = make_service(cache, broker)
    update = FlagUpdate(
        enabled=True,
        description="Enabled during test",
    )

    # Act
    result = await service.update(
        "tenant-a",
        "production",
        "checkout.v2",
        update,
    )

    # Assert
    assert result.enabled is True
    assert result.description == "Enabled during test"
    assert cache.cached == CachedFlag(enabled=True)
    assert broker.messages
    assert '"type": "flag.updated"' in broker.messages[0][1]


async def test_list_page_returns_cursor_when_more_rows_exist() -> None:
    # Arrange
    first = make_flag(key="flag-1")
    second = make_flag(key="flag-2")
    third = make_flag(key="flag-3")
    FakeUnitOfWork.repository = FakeRepository(
        rows=[first, second, third]
    )
    service = make_service(FakeCache(), FakeBroker())

    # Act
    items, next_cursor = await service.list_page(
        "tenant-a",
        "production",
        limit=2,
        cursor=None,
    )

    # Assert
    assert items == [first, second]
    assert next_cursor == second.id


async def test_create_translates_integrity_error_to_conflict() -> None:
    # Arrange
    error = IntegrityError("insert", {}, Exception("duplicate"))
    FakeUnitOfWork.repository = FakeRepository(add_error=error)
    service = make_service(FakeCache(), FakeBroker())
    data = FlagCreate(
        key="checkout.v2",
        environment="production",
        enabled=True,
    )

    # Act / Assert
    with pytest.raises(
        ConflictError,
        match="Feature flag already exists",
    ):
        await service.create("tenant-a", data)


def test_stream_delegates_to_broker() -> None:
    # Arrange
    broker = FakeBroker()
    service = make_service(FakeCache(), broker)

    # Act
    stream = service.stream("tenant-a")

    # Assert
    assert stream is not None
