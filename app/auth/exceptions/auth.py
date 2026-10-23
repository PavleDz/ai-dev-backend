from __future__ import annotations

from app.utils.exceptions import ConflictException, UnauthenticatedException


class InvalidCredentialsException(UnauthenticatedException):
    def __init__(self) -> None:
        # One message for a wrong email and a wrong password: the API must not reveal which emails exist.
        super().__init__(message="Invalid email or password", code="invalid_credentials")


class InvalidTokenException(UnauthenticatedException):
    def __init__(self) -> None:
        super().__init__(message="Invalid or expired token", code="invalid_token")


class NotAuthenticatedException(UnauthenticatedException):
    def __init__(self) -> None:
        super().__init__(message="Authentication required", code="not_authenticated")


class EmailAlreadyRegisteredException(ConflictException):
    def __init__(self) -> None:
        message = "Email is already registered"
        super().__init__(
            message=message, code="email_already_registered", field_errors={"email": message}
        )
