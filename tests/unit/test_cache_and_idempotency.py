import json
from collections.abc import AsyncIterator
from typing import Any

import pytest

from app.core.errors import ConflictError
from app.infrastructure.cache import (
    CachedFlag,
    RedisEventBroker,
    RedisFlagCache,
)
from app.services.idempotency import RedisIdempotencyStore


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.published: list[tuple[str, str]] = []
        self.allow_set = True

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def set(
        self,
        key: str,
        value: str,
        *,
        ex: int,
        nx: bool = False,
    ) -> bool:
        if nx and not self.allow_set:
            return False
        self.values[key] = value
        return True

    async def delete(self, key: str) -> None:
        self.values.pop(key, None)

    async def publish(self, channel: str, payload: str) -> None:
        self.published.append((channel, payload))


async def test_cache_returns_none_on_miss() -> None:
    # Arrange
    redis = FakeRedis()
    cache = RedisFlagCache(redis, ttl_seconds=60)  # type: ignore[arg-type]

    # Act
    result = await cache.get("tenant-a", "production", "checkout")

    # Assert
    assert result is None


async def test_cache_set_get_and_delete() -> None:
    # Arrange
    redis = FakeRedis()
    cache = RedisFlagCache(redis, ttl_seconds=60)  # type: ignore[arg-type]
    value = CachedFlag(enabled=True)

    # Act
    await cache.set("tenant-a", "production", "checkout", value)
    cached = await cache.get("tenant-a", "production", "checkout")
    await cache.delete("tenant-a", "production", "checkout")
    deleted = await cache.get("tenant-a", "production", "checkout")

    # Assert
    assert cached == value
    assert deleted is None
    assert json.loads(
        redis.values.get(
            "flags:tenant-a:production:checkout",
            "{}",
        )
    ) == {}


async def test_event_broker_publishes_to_tenant_channel() -> None:
    # Arrange
    redis = FakeRedis()
    broker = RedisEventBroker(redis)  # type: ignore[arg-type]

    # Act
    await broker.publish("tenant-a", '{"enabled": true}')

    # Assert
    assert redis.published == [
        ("flag-events:tenant-a", '{"enabled": true}')
    ]


async def test_idempotency_accepts_new_token() -> None:
    # Arrange
    redis = FakeRedis()
    store = RedisIdempotencyStore(redis)  # type: ignore[arg-type]

    # Act
    await store.acquire("tenant-a", "request-1", ttl_seconds=120)

    # Assert
    assert redis.values["idempotency:tenant-a:request-1"] == "1"


async def test_idempotency_rejects_duplicate_token() -> None:
    # Arrange
    redis = FakeRedis()
    redis.allow_set = False
    store = RedisIdempotencyStore(redis)  # type: ignore[arg-type]

    # Act / Assert
    with pytest.raises(ConflictError, match="Duplicated request token"):
        await store.acquire("tenant-a", "request-1")
