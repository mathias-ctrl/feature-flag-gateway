from fastapi import status

from app.core.errors import (
    ApplicationError,
    ConflictError,
    EntityNotFoundError,
    UnauthorizedError,
    to_http_exception,
    validation_error_payload,
)


def test_not_found_error_mapping() -> None:
    # Arrange
    error = EntityNotFoundError("Flag not found")

    # Act
    result = to_http_exception(error)

    # Assert
    assert result.status_code == status.HTTP_404_NOT_FOUND
    assert result.detail == {
        "code": "not_found",
        "message": "Flag not found",
    }


def test_conflict_error_mapping() -> None:
    # Arrange
    error = ConflictError("Flag already exists")

    # Act
    result = to_http_exception(error)

    # Assert
    assert result.status_code == status.HTTP_409_CONFLICT
    assert result.detail["code"] == "conflict"


def test_unauthorized_error_mapping_adds_bearer_header() -> None:
    # Arrange
    error = UnauthorizedError("Invalid token")

    # Act
    result = to_http_exception(error)

    # Assert
    assert result.status_code == status.HTTP_401_UNAUTHORIZED
    assert result.headers == {"WWW-Authenticate": "Bearer"}


def test_unknown_application_error_uses_bad_request() -> None:
    # Arrange
    error = ApplicationError("Unexpected application error")

    # Act
    result = to_http_exception(error)

    # Assert
    assert result.status_code == status.HTTP_400_BAD_REQUEST
    assert result.detail["code"] == "application_error"


def test_validation_error_payload() -> None:
    # Arrange
    errors = [{"loc": ["body", "key"], "msg": "Required"}]

    # Act
    result = validation_error_payload(errors)

    # Assert
    assert result == {
        "code": "validation_error",
        "message": "Invalid request",
        "errors": errors,
    }
