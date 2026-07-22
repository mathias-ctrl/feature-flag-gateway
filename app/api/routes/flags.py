from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sse_starlette.sse import EventSourceResponse

from app.api.dependencies import (
    get_flag_service,
    get_idempotency_store,
    get_tenant_id,
)
from app.domain.schemas import (
    FlagCreate,
    FlagEvaluationResponse,
    FlagResponse,
    FlagUpdate,
    PageResponse,
)
from app.services.flags import FeatureFlagService
from app.services.idempotency import IdempotencyStore

router = APIRouter(prefix="/v1/flags", tags=["feature-flags"])


@router.post("", response_model=FlagResponse, status_code=status.HTTP_201_CREATED)
async def create_flag(
    body: FlagCreate,
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    service: Annotated[FeatureFlagService, Depends(get_flag_service)],
    idempotency: Annotated[IdempotencyStore, Depends(get_idempotency_store)],
    request_token: Annotated[str, Header(alias="Idempotency-Key")],
) -> FlagResponse:
    await idempotency.acquire(tenant_id, request_token)
    flag = await service.create(tenant_id, body)
    return FlagResponse.model_validate(flag)


@router.put("/{environment}/{key}", response_model=FlagResponse)
async def update_flag(
    environment: str,
    key: str,
    body: FlagUpdate,
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    service: Annotated[FeatureFlagService, Depends(get_flag_service)],
    idempotency: Annotated[IdempotencyStore, Depends(get_idempotency_store)],
    request_token: Annotated[str, Header(alias="Idempotency-Key")],
) -> FlagResponse:
    await idempotency.acquire(tenant_id, request_token)
    flag = await service.update(tenant_id, environment, key, body)
    return FlagResponse.model_validate(flag)


@router.get("/{environment}/{key}/evaluate", response_model=FlagEvaluationResponse)
async def evaluate_flag(
    environment: str,
    key: str,
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    service: Annotated[FeatureFlagService, Depends(get_flag_service)],
) -> FlagEvaluationResponse:
    evaluation = await service.evaluate(tenant_id, environment, key)
    return FlagEvaluationResponse(
        tenant_id=tenant_id,
        environment=environment,
        key=key,
        enabled=evaluation.enabled,
        source=evaluation.source,
    )


@router.get("", response_model=PageResponse)
async def list_flags(
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    service: Annotated[FeatureFlagService, Depends(get_flag_service)],
    environment: Annotated[str, Query(max_length=32)] = "production",
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: UUID | None = None,
) -> PageResponse:
    items, next_cursor = await service.list_page(
        tenant_id,
        environment,
        limit,
        cursor,
    )
    return PageResponse(
        items=[FlagResponse.model_validate(item) for item in items],
        next_cursor=next_cursor,
    )


@router.get("/events/stream")
async def stream_events(
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    service: Annotated[FeatureFlagService, Depends(get_flag_service)],
) -> EventSourceResponse:
    async def events():  # type: ignore[no-untyped-def]
        async for payload in service.stream(tenant_id):
            yield {"event": "flag.updated", "data": payload}

    return EventSourceResponse(events(), ping=15)
