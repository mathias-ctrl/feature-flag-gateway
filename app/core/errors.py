from typing import Any

from fastapi import HTTPException, status


class ApplicationError(Exception):
    """Base exception for expected application failures."""


class EntityNotFoundError(ApplicationError):
    pass


class ConflictError(ApplicationError):
    pass


class UnauthorizedError(ApplicationError):
    pass


class AppHTTPException(HTTPException):
    def __init__(
        self,
        status_code: int,
        code: str,
        detail: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            detail={"code": code, "message": detail},
            headers=headers,
        )


ERROR_MAPPING: dict[type[ApplicationError], tuple[int, str]] = {
    EntityNotFoundError: (status.HTTP_404_NOT_FOUND, "not_found"),
    ConflictError: (status.HTTP_409_CONFLICT, "conflict"),
    UnauthorizedError: (status.HTTP_401_UNAUTHORIZED, "unauthorized"),
}


def to_http_exception(error: ApplicationError) -> AppHTTPException:
    status_code, code = ERROR_MAPPING.get(
        type(error),
        (status.HTTP_400_BAD_REQUEST, "application_error"),
    )
    headers: dict[str, str] | None = None
    if status_code == status.HTTP_401_UNAUTHORIZED:
        headers = {"WWW-Authenticate": "Bearer"}
    return AppHTTPException(status_code, code, str(error), headers)


def validation_error_payload(errors: list[dict[str, Any]]) -> dict[str, Any]:
    return {"code": "validation_error", "message": "Invalid request", "errors": errors}
