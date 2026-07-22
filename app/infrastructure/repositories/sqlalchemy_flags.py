from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import FeatureFlag
from app.domain.repositories import FeatureFlagRepository


class SqlAlchemyFeatureFlagRepository(FeatureFlagRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, flag: FeatureFlag) -> FeatureFlag:
        self._session.add(flag)
        await self._session.flush()
        await self._session.refresh(flag)
        return flag

    async def get_by_key(
        self,
        tenant_id: str,
        environment: str,
        key: str,
    ) -> FeatureFlag | None:
        statement = select(FeatureFlag).where(
            FeatureFlag.tenant_id == tenant_id,
            FeatureFlag.environment == environment,
            FeatureFlag.key == key,
        )
        return await self._session.scalar(statement)

    async def list_page(
        self,
        tenant_id: str,
        environment: str,
        limit: int,
        cursor: UUID | None,
    ) -> list[FeatureFlag]:
        statement = (
            select(FeatureFlag)
            .where(
                FeatureFlag.tenant_id == tenant_id,
                FeatureFlag.environment == environment,
            )
            .order_by(FeatureFlag.id)
            .limit(limit + 1)
        )
        if cursor is not None:
            statement = statement.where(FeatureFlag.id > cursor)
        result = await self._session.scalars(statement)
        return list(result.all())
