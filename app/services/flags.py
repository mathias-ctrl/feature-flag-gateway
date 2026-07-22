import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.errors import ConflictError, EntityNotFoundError
from app.domain.models import FeatureFlag
from app.domain.schemas import FlagCreate, FlagUpdate
from app.infrastructure.cache import CachedFlag, EventBroker, FlagCache
from app.infrastructure.unit_of_work import UnitOfWork


@dataclass(frozen=True, slots=True)
class Evaluation:
    enabled: bool
    source: str


class FeatureFlagService:
    def __init__(
        self,
        uow_factory: type[UnitOfWork],
        session_factory: object,
        cache: FlagCache,
        broker: EventBroker,
    ) -> None:
        self._uow_factory = uow_factory
        self._session_factory = session_factory
        self._cache = cache
        self._broker = broker

    def _uow(self) -> UnitOfWork:
        return self._uow_factory(self._session_factory)  # type: ignore[arg-type]

    async def create(self, tenant_id: str, data: FlagCreate) -> FeatureFlag:
        flag = FeatureFlag(tenant_id=tenant_id, **data.model_dump())
        try:
            async with self._uow() as uow:
                created = await uow.flags.add(flag)
                await uow.commit()
        except IntegrityError as error:
            raise ConflictError("Feature flag already exists") from error
        await self._synchronize(created)
        return created

    async def update(
        self,
        tenant_id: str,
        environment: str,
        key: str,
        data: FlagUpdate,
    ) -> FeatureFlag:
        async with self._uow() as uow:
            flag = await uow.flags.get_by_key(tenant_id, environment, key)
            if flag is None:
                raise EntityNotFoundError("Feature flag not found")
            flag.enabled = data.enabled
            flag.description = data.description
            await uow.commit()
            await uow.session.refresh(flag)
        await self._synchronize(flag)
        return flag

    async def evaluate(
        self,
        tenant_id: str,
        environment: str,
        key: str,
    ) -> Evaluation:
        cached = await self._cache.get(tenant_id, environment, key)
        if cached is not None:
            return Evaluation(enabled=cached.enabled, source="cache")

        async with self._uow() as uow:
            flag = await uow.flags.get_by_key(tenant_id, environment, key)
        if flag is None:
            raise EntityNotFoundError("Feature flag not found")

        await self._cache.set(
            tenant_id,
            environment,
            key,
            CachedFlag(enabled=flag.enabled),
        )
        return Evaluation(enabled=flag.enabled, source="database")

    async def list_page(
        self,
        tenant_id: str,
        environment: str,
        limit: int,
        cursor: UUID | None,
    ) -> tuple[list[FeatureFlag], UUID | None]:
        async with self._uow() as uow:
            rows = await uow.flags.list_page(tenant_id, environment, limit, cursor)
        has_next = len(rows) > limit
        items = rows[:limit]
        next_cursor = items[-1].id if has_next and items else None
        return items, next_cursor

    def stream(self, tenant_id: str) -> AsyncIterator[str]:
        return self._broker.subscribe(tenant_id)

    async def _synchronize(self, flag: FeatureFlag) -> None:
        await self._cache.set(
            flag.tenant_id,
            flag.environment,
            flag.key,
            CachedFlag(enabled=flag.enabled),
        )
        payload = json.dumps(
            {
                "type": "flag.updated",
                "tenant_id": flag.tenant_id,
                "environment": flag.environment,
                "key": flag.key,
                "enabled": flag.enabled,
            }
        )
        await self._broker.publish(flag.tenant_id, payload)
