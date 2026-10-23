"""API layer only: the auth service is a mock."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.auth.exceptions.auth import EmailAlreadyRegisteredException, InvalidCredentialsException
from app.auth.schemas.auth import AuthenticationResponseSchema
from app.users.schemas.user import UserResponseSchema
from tests.utils import create_current_user

pytestmark = pytest.mark.unit

REGISTER_BODY = {"email": "ana@example.com", "password": "secret123", "displayName": "Ana"}


def _auth_response() -> AuthenticationResponseSchema:
    user = create_current_user(1, "ana@example.com")
    return AuthenticationResponseSchema(
        token="jwt", user=UserResponseSchema.model_validate(user, from_attributes=True)
    )


def test_register_returns_201_with_token_and_user(client: TestClient, auth_service: Mock) -> None:
    auth_service.register.return_value = _auth_response()

    response = client.post("/api/auth/register", json=REGISTER_BODY)

    assert response.status_code == 201
    assert response.json() == {
        "token": "jwt",
        "user": {
            "id": 1,
            "email": "ana@example.com",
            "displayName": "Test User",
            "createdAt": "2026-01-01T00:00:00Z",
        },
    }


def test_register_duplicate_email_is_409_with_field_error(
    client: TestClient, auth_service: Mock
) -> None:
    auth_service.register.side_effect = EmailAlreadyRegisteredException()

    response = client.post("/api/auth/register", json=REGISTER_BODY)

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Email is already registered",
        "code": "email_already_registered",
        "fieldErrors": {"email": "Email is already registered"},
    }


def test_register_short_password_is_422(client: TestClient, auth_service: Mock) -> None:
    response = client.post("/api/auth/register", json={**REGISTER_BODY, "password": "short"})

    assert response.status_code == 422
    assert "password" in response.json()["fieldErrors"]
    auth_service.register.assert_not_called()


def test_login_wrong_password_is_401(client: TestClient, auth_service: Mock) -> None:
    auth_service.login.side_effect = InvalidCredentialsException()

    response = client.post(
        "/api/auth/login", json={"email": "ana@example.com", "password": "wrong"}
    )

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_credentials"


def test_me_returns_the_user_behind_the_token(client: TestClient) -> None:
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer token"})

    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
