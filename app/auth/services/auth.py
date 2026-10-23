from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Protocol

import jwt
from sqlalchemy.exc import IntegrityError

from app.auth.exceptions.auth import (
    EmailAlreadyRegisteredException,
    InvalidCredentialsException,
    InvalidTokenException,
)
from app.auth.password import hash_password, verify_password
from app.auth.repositories.auth import IAuthRepository
from app.auth.schemas.auth import (
    AuthenticationResponseSchema,
    CurrentUser,
    LoginRequestSchema,
    RegisterRequestSchema,
    TokenPayload,
)
from app.config.settings import Settings
from app.users.models.user import User
from app.users.schemas.user import UserResponseSchema
from app.utils.di import inject


class IAuthService(Protocol):
    def register(self, data: RegisterRequestSchema) -> AuthenticationResponseSchema: ...

    def login(self, data: LoginRequestSchema) -> AuthenticationResponseSchema: ...

    def get_current_user(self, token: str) -> CurrentUser: ...


@inject(alias=IAuthService)
class AuthService(IAuthService):
    def __init__(self, auth_repository: IAuthRepository, settings: Settings) -> None:
        self._auth_repository = auth_repository
        self._settings = settings

    def register(self, data: RegisterRequestSchema) -> AuthenticationResponseSchema:
        user = User(
            email=data.email.lower(),
            password_hash=hash_password(data.password),
            display_name=data.display_name,
        )
        try:
            user = self._auth_repository.add_user(user)
        except IntegrityError as e:
            # The UNIQUE constraint on users.email decides, not an `if` before the insert (ADR-007).
            raise EmailAlreadyRegisteredException from e
        return self._authentication_response(user)

    def login(self, data: LoginRequestSchema) -> AuthenticationResponseSchema:
        user = self._auth_repository.get_user_by_email(data.email.lower())
        if user is None or not verify_password(data.password, user.password_hash):
            raise InvalidCredentialsException
        return self._authentication_response(user)

    def get_current_user(self, token: str) -> CurrentUser:
        payload = self._decode_token(token)
        user = self._auth_repository.get_user_by_id(int(payload.sub))
        if user is None:
            raise InvalidTokenException
        return CurrentUser(
            id=user.id, email=user.email, display_name=user.display_name, created_at=user.created_at
        )

    def _authentication_response(self, user: User) -> AuthenticationResponseSchema:
        return AuthenticationResponseSchema(
            token=self._create_access_token(user_id=user.id),
            user=UserResponseSchema.model_validate(user),
        )

    def _create_access_token(self, user_id: int) -> str:
        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=self._settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = TokenPayload(
            sub=str(user_id), exp=int(expires_at.timestamp()), iat=int(now.timestamp())
        )
        return jwt.encode(
            payload.model_dump(), self._settings.JWT_SECRET_KEY, algorithm=self._settings.ALGORITHM
        )

    def _decode_token(self, token: str) -> TokenPayload:
        try:
            payload = jwt.decode(
                token, self._settings.JWT_SECRET_KEY, algorithms=[self._settings.ALGORITHM]
            )
            return TokenPayload.model_validate(payload)
        except (jwt.PyJWTError, ValueError) as e:
            raise InvalidTokenException from e
