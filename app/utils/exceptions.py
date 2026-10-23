from __future__ import annotations

from typing import Any

from fastapi import HTTPException


class AppBaseException(Exception):
    """Base of every error a service raises. `app.app` maps each subclass to an HTTP status.

    The client always receives `{"detail": message, "code": code}`; `field_errors` adds
    `"fieldErrors": {"email": "..."}` when one input field is at fault (ADR-005).
    """

    def __init__(self, message: str, code: str, field_errors: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.field_errors = field_errors

    def response_content(self) -> dict[str, Any]:
        content: dict[str, Any] = {"detail": self.message, "code": self.code}
        if self.field_errors:
            content["fieldErrors"] = self.field_errors
        return content


class NotFoundException(AppBaseException):
    pass


class InvalidRequestException(AppBaseException):
    pass


class UnauthenticatedException(AppBaseException):
    pass


class ForbiddenException(AppBaseException):
    pass


class ConflictException(AppBaseException):
    pass


class ServerException(AppBaseException):
    pass


class HTTPExceptionWithCode(HTTPException):
    # override the default HTTPException to include a custom error code
    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: dict[str, str] | None = None,
        code: str = "",
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.code = code
