from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.models import FeatureFlag


class FeatureFlagRepository(ABC):
    @abstractmethod
    async def add(self, flag: FeatureFlag) -> FeatureFlag: ...

    @abstractmethod
    async def get_by_key(
        self,
        tenant_id: str,
        environment: str,
        key: str,
    ) -> FeatureFlag | None: ...

    @abstractmethod
    async def list_page(
        self,
        tenant_id: str,
        environment: str,
        limit: int,
        cursor: UUID | None,
    ) -> list[FeatureFlag]: ...
