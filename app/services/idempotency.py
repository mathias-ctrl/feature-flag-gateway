from typing import Protocol

from redis.asyncio import Redis

from app.core.errors import ConflictError


class IdempotencyStore(Protocol):
    async def acquire(self, tenant_id: str, token: str, ttl_seconds: int = 300) -> None: ...


class RedisIdempotencyStore:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def acquire(
        self,
        tenant_id: str,
        token: str,
        ttl_seconds: int = 300,
    ) -> None:
        key = f"idempotency:{tenant_id}:{token}"
        acquired = await self._redis.set(key, "1", ex=ttl_seconds, nx=True)
        if not acquired:
            raise ConflictError("Duplicated request token")
