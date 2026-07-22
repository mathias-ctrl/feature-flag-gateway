import json
from collections.abc import AsyncIterator
from dataclasses import asdict, dataclass
from typing import Protocol

from redis.asyncio import Redis


@dataclass(frozen=True, slots=True)
class CachedFlag:
    enabled: bool


class FlagCache(Protocol):
    async def get(self, tenant_id: str, environment: str, key: str) -> CachedFlag | None: ...
    async def set(
        self,
        tenant_id: str,
        environment: str,
        key: str,
        value: CachedFlag,
    ) -> None: ...
    async def delete(self, tenant_id: str, environment: str, key: str) -> None: ...


class RedisFlagCache:
    def __init__(self, redis: Redis, ttl_seconds: int) -> None:
        self._redis = redis
        self._ttl_seconds = ttl_seconds

    @staticmethod
    def _key(tenant_id: str, environment: str, key: str) -> str:
        return f"flags:{tenant_id}:{environment}:{key}"

    async def get(
        self,
        tenant_id: str,
        environment: str,
        key: str,
    ) -> CachedFlag | None:
        raw = await self._redis.get(self._key(tenant_id, environment, key))
        if raw is None:
            return None
        return CachedFlag(**json.loads(raw))

    async def set(
        self,
        tenant_id: str,
        environment: str,
        key: str,
        value: CachedFlag,
    ) -> None:
        await self._redis.set(
            self._key(tenant_id, environment, key),
            json.dumps(asdict(value)),
            ex=self._ttl_seconds,
        )

    async def delete(self, tenant_id: str, environment: str, key: str) -> None:
        await self._redis.delete(self._key(tenant_id, environment, key))


class EventBroker(Protocol):
    async def publish(self, tenant_id: str, payload: str) -> None: ...
    def subscribe(self, tenant_id: str) -> AsyncIterator[str]: ...


class RedisEventBroker:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    @staticmethod
    def _channel(tenant_id: str) -> str:
        return f"flag-events:{tenant_id}"

    async def publish(self, tenant_id: str, payload: str) -> None:
        await self._redis.publish(self._channel(tenant_id), payload)

    async def subscribe(self, tenant_id: str) -> AsyncIterator[str]:
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(self._channel(tenant_id))
        try:
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                data = message["data"]
                yield data.decode() if isinstance(data, bytes) else str(data)
        finally:
            await pubsub.unsubscribe(self._channel(tenant_id))
            await pubsub.aclose()
