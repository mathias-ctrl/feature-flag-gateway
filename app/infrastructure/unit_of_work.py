from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.repositories import FeatureFlagRepository
from app.infrastructure.repositories.sqlalchemy_flags import (
    SqlAlchemyFeatureFlagRepository,
)


class UnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self.session: AsyncSession
        self.flags: FeatureFlagRepository

    async def __aenter__(self) -> Self:
        self.session = self._session_factory()
        self.flags = SqlAlchemyFeatureFlagRepository(self.session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            await self.session.rollback()
        await self.session.close()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
