from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FlagCreate(BaseModel):
    key: str = Field(min_length=1, max_length=128, pattern=r"^[a-z0-9._-]+$")
    environment: str = Field(default="production", min_length=1, max_length=32)
    enabled: bool = False
    description: str | None = Field(default=None, max_length=500)


class FlagUpdate(BaseModel):
    enabled: bool
    description: str | None = Field(default=None, max_length=500)


class FlagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    environment: str
    key: str
    enabled: bool
    description: str | None
    created_at: datetime
    updated_at: datetime


class FlagEvaluationResponse(BaseModel):
    tenant_id: str
    environment: str
    key: str
    enabled: bool
    source: str


class PageResponse(BaseModel):
    items: list[FlagResponse]
    next_cursor: UUID | None
