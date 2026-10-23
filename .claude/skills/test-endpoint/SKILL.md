---
name: test-endpoint
description: Write the standard test set for one backend route: a unit test with the service mocked plus integration tests for the happy path, 401, 403, 404, 422 with fieldErrors, using the fixtures from the conftest files. Use when adding or changing an endpoint, or when a route has only a happy-path test.
argument-hint: <METHOD /api/path> or <domain name>
---

# Test an endpoint

Every route gets the same questions answered by tests (ADR-011), in two layers. The templates are
`tests/unit/test_listings_api.py` and `tests/integration/test_listings.py`; copy the shape, rename
the entity. All paths are relative to the repo root.

## 1. Read
`tests/conftest.py`, `tests/unit/conftest.py`, `tests/integration/conftest.py` (the fixtures), the two template files,
the route's `api/<entity>.py`, `schemas/<entity>.py`, `services/<entity>.py`, `exceptions/<entity>.py`, and its row in
`docs/entities.md` (status codes, messages and codes are agreed there, ADR-002, ADR-005).

## 2. The fixtures you already have
| Fixture | Where | Gives you |
|---------|-------|-----------|
| `client` | `tests/conftest.py` | `TestClient` on the app |
| `auth_service` (autouse) | `tests/unit/conftest.py` | mock `IAuthService`; every request is user 1; set `.get_current_user.side_effect` for `401` |
| `listing_service` | `tests/unit/conftest.py` | mock `IListingService`; set `.return_value` / `.side_effect` |
| `auth_headers` | `tests/integration/conftest.py` | `{"Authorization": "Bearer ..."}` for user A, registered through the API |
| `other_auth_headers` | `tests/integration/conftest.py` | the same for user B, for `403` tests |
| `listing_id` | `tests/integration/conftest.py` | a record created by user A through `POST` |
For a new domain add a `<entity>_service` mock fixture to `tests/unit/conftest.py` (copy `listing_service`), a
`<entity>_id` fixture to `tests/integration/conftest.py` (built through `POST`, never by inserting rows) and the
new table to `clean_tables`. Add a module-level `VALID_BODY = {...}` dict with one valid body.

## 3. The set, per route
| Route kind | Unit (service mocked) | Integration (real database) |
|------------|-----------------------|-----------------------------|
| `GET` list | `Page` is serialized camelCase; query params reach the service | empty at start; order (newest first); `search`; `page`/`size` |
| `GET /{id}` | service exception → `404` with `{"detail", "code"}` | happy path returns the created record |
| `POST` | no token `401`; invalid token `401`; `422` with the exact `fieldErrors` keys; `current_user.id` passed to the service, `ownerId` in the body ignored | `201` and body (`createdAt` ends with `Z`, defaults applied) |
| `PATCH /{id}` | service `403` exception → `403` with its `code` | owner `200` and only the sent field changed; other user `403`; unknown id `404` |
| `DELETE /{id}` | `204` with empty body, service called once | owner `204`, then `GET` is `404`; other user `403` |

## 4. Templates
```python
# tests/unit/test_<name>_api.py  (from tests/unit/test_listings_api.py)
pytestmark = pytest.mark.unit
AUTH = {"Authorization": "Bearer token"}


def test_create_without_token_is_401(client: TestClient, listing_service: Mock) -> None:
    response = client.post("/api/listings", json=VALID_BODY)

    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"
    listing_service.create.assert_not_called()


def test_create_with_invalid_body_is_422_with_field_errors(client: TestClient, listing_service: Mock) -> None:
    response = client.post("/api/listings", json={"title": "ab", "price": -1, "category": "cars"}, headers=AUTH)

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
```

```python
# tests/integration/test_<name>.py  (from tests/integration/test_listings.py)
def test_other_user_cannot_patch_or_delete(
    client: TestClient, other_auth_headers: dict[str, str], listing_id: int
) -> None:
    patched = client.patch(f"/api/listings/{listing_id}", json={"price": 1}, headers=other_auth_headers)
    assert patched.status_code == 403

    deleted = client.delete(f"/api/listings/{listing_id}", headers=other_auth_headers)
    assert deleted.status_code == 403
    assert client.get(f"/api/listings/{listing_id}").status_code == 200


def test_owner_can_delete(client: TestClient, auth_headers: dict[str, str], listing_id: int) -> None:
    deleted = client.delete(f"/api/listings/{listing_id}", headers=auth_headers)

    assert deleted.status_code == 204
    assert client.get(f"/api/listings/{listing_id}").status_code == 404
```

## 5. Rules while writing
- Name says the expectation: `test_patch_by_other_user_is_403`, not `test_patch_2`
- Assert on the body, not only the status: `detail` and `code` are part of the contract (ADR-005), camelCase keys too (ADR-010)
- Unit tests assert what reached the service (`call_args.kwargs`), integration tests assert what is in the database through the API
- One behaviour per test; no `time.sleep`, no network, no `data/app.db`; every function typed (`-> None`)
- A `422` test sends several bad fields at once and asserts the exact set of `fieldErrors` keys
- If the route is public in `docs/entities.md`, there is no `401` test for it; say so in the report instead of inventing one

## 6. Run and report
`poetry run pytest -q tests/unit/test_<name>_api.py tests/integration/test_<name>.py` in the repo root, then
`poetry run typecheck`. Report the table from step 3 with PASS/FAIL per row and anything in `docs/entities.md`
that the code contradicted (a wrong message, a missing status code or error code).
