---
paths:
  - "tests/**"
---

# Backend tests

- Two layers, two folders (ADR-011):
  - `tests/unit/test_<name>_api.py`: the HTTP layer with the service mocked (`create_autospec(I<Name>Service, instance=True)` registered with `add_to_di_container`, removed with `remove_from_di_container`); routing, validation, auth, status codes and the error shape, no database
  - `tests/integration/test_<name>.py`: the whole stack against a real temporary SQLite database (or `DATABASE_URL` from the environment); records are created through the API
- Shared fixtures only in `conftest.py` files: `client` (`tests/conftest.py`), `session_factory` + `auth_service` + `listing_service` (`tests/unit/conftest.py`), `tables` + `clean_tables` + `auth_headers` + `other_auth_headers` + `listing_id` (`tests/integration/conftest.py`)
- Every endpoint has at least: the happy path, unauthenticated (`401`) for writes, forbidden (`403`) where there is an owner, not found (`404`) where there is an id, validation (`422`) where there is input (`/test-endpoint` writes the set)
- Assert on the status code and on the error shape: `response.json() == {"detail": ..., "code": ...}`, or the exact `fieldErrors` keys for `422` (ADR-005)
- Assert that responses use camelCase keys (`imageUrl`, `createdAt`), not snake_case (ADR-010)
- A unit test asserts what the endpoint passed to the service (`listing_service.create.call_args.kwargs["current_user"].id == 1`), not what the service would have done
- In integration tests, create records through the API, not by inserting rows directly; every test starts from empty tables (`clean_tables`) and does not depend on another test or on `data/app.db`
- No `time.sleep`, no network, no real files: a test runs in milliseconds and offline
- Test names say what is expected: `test_patch_by_other_user_is_403`, not `test_patch_2`
- Every test function is typed (`-> None`, fixtures annotated); mypy checks `tests/` too
- A test is never deleted or skipped to make the suite green; a failing test is a finding
