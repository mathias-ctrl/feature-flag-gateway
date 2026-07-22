from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from app.api.dependencies import get_flag_service, get_idempotency_store
from app.api.routes.flags import router as flags_router
from app.core.config import Settings, get_settings
from app.core.errors import ApplicationError, to_http_exception
from app.core.logging import configure_logging
from app.infrastructure.cache import RedisEventBroker, RedisFlagCache
from app.infrastructure.database import Database
from app.infrastructure.unit_of_work import UnitOfWork
from app.services.flags import FeatureFlagService
from app.services.idempotency import RedisIdempotencyStore

logger = structlog.get_logger()


def create_app(settings: Settings | None = None) -> FastAPI:
    configure_logging()
    resolved_settings = settings or get_settings()
    database = Database(resolved_settings)
    redis = Redis.from_url(resolved_settings.redis_url, decode_responses=False)
    cache = RedisFlagCache(redis, resolved_settings.cache_ttl_seconds)
    broker = RedisEventBroker(redis)
    flag_service = FeatureFlagService(
        UnitOfWork,
        database.session_factory,
        cache,
        broker,
    )
    idempotency_store = RedisIdempotencyStore(redis)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        await redis.aclose()
        await database.dispose()

    app = FastAPI(title=resolved_settings.app_name, lifespan=lifespan)
    app.include_router(flags_router)
    app.dependency_overrides[get_flag_service] = lambda: flag_service
    app.dependency_overrides[get_idempotency_store] = lambda: idempotency_store

    @app.middleware("http")
    async def security_headers(request: Request, call_next: Any):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(ApplicationError)
    async def application_error_handler(
        _: Request,
        error: ApplicationError,
    ) -> JSONResponse:
        http_error = to_http_exception(error)
        logger.warning("application_error", detail=str(error), status=http_error.status_code)
        return JSONResponse(
            status_code=http_error.status_code,
            content=http_error.detail,
            headers=http_error.headers,
        )

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
