from __future__ import annotations

from fastapi.testclient import TestClient


def test_create_and_get(client: TestClient, auth_headers: dict[str, str]) -> None:
    created = client.post(
        "/api/listings",
        json={
            "title": "Elden Ring",
            "price": 35,
            "category": "games",
            "city": "Nikšić",
            "imageUrl": "https://example.com/er.jpg",
        },
        headers=auth_headers,
    )

    assert created.status_code == 201
    body = created.json()
    assert body["description"] == ""
    assert body["imageUrl"] == "https://example.com/er.jpg"
    assert body["createdAt"].endswith("Z")

    fetched = client.get(f"/api/listings/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == body


def test_list_newest_first_with_search(client: TestClient, auth_headers: dict[str, str]) -> None:
    for title in ["PlayStation 5", "Xbox Series X", "PlayStation 4"]:
        client.post(
            "/api/listings",
            json={"title": title, "price": 100, "category": "consoles", "city": "Bar"},
            headers=auth_headers,
        )

    response = client.get("/api/listings?search=playstation")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert [item["title"] for item in body["items"]] == ["PlayStation 4", "PlayStation 5"]


def test_list_pagination(client: TestClient, auth_headers: dict[str, str]) -> None:
    for i in range(3):
        client.post(
            "/api/listings",
            json={"title": f"Game {i}", "price": 10, "category": "games", "city": "Bar"},
            headers=auth_headers,
        )

    response = client.get("/api/listings?page=2&size=2")

    body = response.json()
    assert (body["total"], body["pages"], len(body["items"])) == (3, 2, 1)


def test_owner_can_patch(client: TestClient, auth_headers: dict[str, str], listing_id: int) -> None:
    response = client.patch(
        f"/api/listings/{listing_id}", json={"price": 350}, headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json()["price"] == 350
    assert response.json()["title"] == "PlayStation 5"  # untouched fields stay


def test_other_user_cannot_patch_or_delete(
    client: TestClient, other_auth_headers: dict[str, str], listing_id: int
) -> None:
    patched = client.patch(
        f"/api/listings/{listing_id}", json={"price": 1}, headers=other_auth_headers
    )
    assert patched.status_code == 403

    deleted = client.delete(f"/api/listings/{listing_id}", headers=other_auth_headers)
    assert deleted.status_code == 403
    assert client.get(f"/api/listings/{listing_id}").status_code == 200


def test_owner_can_delete(
    client: TestClient, auth_headers: dict[str, str], listing_id: int
) -> None:
    deleted = client.delete(f"/api/listings/{listing_id}", headers=auth_headers)

    assert deleted.status_code == 204
    assert client.get(f"/api/listings/{listing_id}").status_code == 404


def test_patch_unknown_listing_is_404(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.patch("/api/listings/999", json={"price": 1}, headers=auth_headers)

    assert response.status_code == 404


def test_negative_price_is_rejected_by_the_database_too(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    # Pydantic answers 422 before the database is reached...
    response = client.post(
        "/api/listings",
        json={"title": "Free", "price": -5, "category": "games", "city": "Bar"},
        headers=auth_headers,
    )
    assert response.status_code == 422
    assert "price" in response.json()["fieldErrors"]
