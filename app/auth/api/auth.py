from __future__ import annotations

from typing import Annotated

from fastapi import Depends, status

from app.auth.schemas.auth import (
    AuthenticationResponseSchema,
    CurrentUser,
    LoginRequestSchema,
    RegisterRequestSchema,
)
from app.auth.services.auth import IAuthService
from app.database.session_handler import DBAPIRouter
from app.deps import get_current_user, get_di_entity
from app.users.schemas.user import UserResponseSchema

router = DBAPIRouter()


@router.post(
    path="/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register",
    description="Creates a user and returns a token for it.",
)
def register(
    data: RegisterRequestSchema,
    auth_service: Annotated[IAuthService, Depends(get_di_entity(IAuthService))],
) -> AuthenticationResponseSchema:
    return auth_service.register(data)


@router.post(path="/login", summary="Login", description="Returns a token for valid credentials.")
def login(
    data: LoginRequestSchema,
    auth_service: Annotated[IAuthService, Depends(get_di_entity(IAuthService))],
) -> AuthenticationResponseSchema:
    return auth_service.login(data)


@router.get(path="/me", summary="Get logged in user", description="The user behind the token.")
def get_logged_in_user(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> UserResponseSchema:
    return UserResponseSchema.model_validate(current_user, from_attributes=True)
