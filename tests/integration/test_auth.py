from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_register_then_me(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={"email": "Ana@Example.com", "password": "secret123", "displayName": "Ana"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == "ana@example.com"  # stored lowercase
    assert "password" not in body["user"]
    assert "passwordHash" not in body["user"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {body['token']}"})
    assert me.status_code == 200
    assert me.json()["displayName"] == "Ana"


@pytest.mark.usefixtures("auth_headers")
def test_register_twice_is_409(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={"email": "ana@example.com", "password": "secret123", "displayName": "Ana 2"},
    )

    assert response.status_code == 409
    assert response.json()["fieldErrors"] == {"email": "Email is already registered"}


@pytest.mark.usefixtures("auth_headers")
def test_login_ok_and_wrong_password(client: TestClient) -> None:
    ok = client.post("/api/auth/login", json={"email": "ana@example.com", "password": "secret123"})
    assert ok.status_code == 200
    assert ok.json()["token"]

    wrong = client.post("/api/auth/login", json={"email": "ana@example.com", "password": "nope"})
    assert wrong.status_code == 401
    assert wrong.json() == {"detail": "Invalid email or password", "code": "invalid_credentials"}


def test_login_unknown_email_gives_the_same_401(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login", json={"email": "nobody@example.com", "password": "secret123"}
    )

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_credentials"


def test_me_with_garbage_token_is_401(client: TestClient) -> None:
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-jwt"})

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_token"
