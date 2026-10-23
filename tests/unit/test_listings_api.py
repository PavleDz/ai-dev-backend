"""API layer only: routing, validation, auth and the error shape. The service is a mock."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.auth.exceptions.auth import InvalidTokenException
from app.listings.exceptions.listing import ListingNotFoundException, NotListingOwnerException
from app.listings.models.listing import ListingCategory
from app.listings.schemas.listing import ListingResponseSchema
from app.utils.pagination import Page

pytestmark = pytest.mark.unit

AUTH = {"Authorization": "Bearer token"}

LISTING = ListingResponseSchema(
    id=7,
    title="PlayStation 5",
    description="",
    price=380,
    category=ListingCategory.CONSOLES,
    city="Podgorica",
    image_url=None,
    created_at=datetime(2026, 1, 1, tzinfo=UTC),
    owner_id=1,
)

VALID_BODY = {"title": "PlayStation 5", "price": 380, "category": "consoles", "city": "Podgorica"}


def test_list_is_paginated_and_camel_case(client: TestClient, listing_service: Mock) -> None:
    listing_service.list.return_value = Page(total=1, items=[LISTING], pages=1)

    response = client.get("/api/listings?search=play&page=1&size=10")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["imageUrl"] is None
    assert body["items"][0]["createdAt"] == "2026-01-01T00:00:00Z"
    call = listing_service.list.call_args.kwargs
    assert call["search"] == "play"
    assert (call["pagination_params"].page, call["pagination_params"].size) == (1, 10)


def test_get_unknown_listing_is_404_with_error_shape(
    client: TestClient, listing_service: Mock
) -> None:
    listing_service.get.side_effect = ListingNotFoundException()

    response = client.get("/api/listings/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Listing not found", "code": "listing_not_found"}


def test_create_without_token_is_401(client: TestClient, listing_service: Mock) -> None:
    response = client.post("/api/listings", json=VALID_BODY)

    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"
    assert response.headers["WWW-Authenticate"] == "Bearer"
    listing_service.create.assert_not_called()


def test_create_with_invalid_token_is_401(
    client: TestClient, listing_service: Mock, auth_service: Mock
) -> None:
    auth_service.get_current_user.side_effect = InvalidTokenException()

    response = client.post("/api/listings", json=VALID_BODY, headers=AUTH)

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_token"
    listing_service.create.assert_not_called()


def test_create_passes_the_signed_in_user_to_the_service(
    client: TestClient, listing_service: Mock
) -> None:
    listing_service.create.return_value = LISTING

    response = client.post("/api/listings", json={**VALID_BODY, "ownerId": 42}, headers=AUTH)

    assert response.status_code == 201
    assert response.json()["ownerId"] == 1
    # the owner comes from the token (user 1), the "ownerId" in the body is ignored
    assert listing_service.create.call_args.kwargs["current_user"].id == 1


def test_create_with_invalid_body_is_422_with_field_errors(
    client: TestClient, listing_service: Mock
) -> None:
    response = client.post(
        "/api/listings", json={"title": "ab", "price": -1, "category": "cars"}, headers=AUTH
    )

    assert response.status_code == 422
    body = response.json()
    assert body["detail"] == "Validation failed"
    assert body["code"] == "validation_error"
    assert set(body["fieldErrors"]) == {"title", "price", "category", "city"}
    listing_service.create.assert_not_called()


def test_patch_by_other_user_is_403(client: TestClient, listing_service: Mock) -> None:
    listing_service.update.side_effect = NotListingOwnerException()

    response = client.patch("/api/listings/7", json={"price": 1}, headers=AUTH)

    assert response.status_code == 403
    assert response.json()["code"] == "not_listing_owner"


def test_delete_is_204_without_body(client: TestClient, listing_service: Mock) -> None:
    response = client.delete("/api/listings/7", headers=AUTH)

    assert response.status_code == 204
    assert response.content == b""
    listing_service.delete.assert_called_once()
