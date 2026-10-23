from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.exceptions.auth import NotAuthenticatedException
from app.auth.schemas.auth import CurrentUser
from app.auth.services.auth import IAuthService
from app.utils.di import get_di_entity

__all__ = ["get_current_user", "get_di_entity", "get_optional_user"]

# auto_error=False: a missing header is handled below, as a 401 with our error shape (not a 403).
security = HTTPBearer(auto_error=False)


def get_optional_user(
    auth_service: Annotated[IAuthService, Depends(get_di_entity(IAuthService))],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> CurrentUser | None:
    """The signed-in user, or None when there is no token. For endpoints that work both ways."""
    if credentials is None:
        return None
    return auth_service.get_current_user(token=credentials.credentials)


def get_current_user(
    current_user: Annotated[CurrentUser | None, Depends(get_optional_user)],
) -> CurrentUser:
    """The signed-in user; 401 without a valid token. Every write endpoint depends on this (ADR-006)."""
    if current_user is None:
        raise NotAuthenticatedException
    return current_user
