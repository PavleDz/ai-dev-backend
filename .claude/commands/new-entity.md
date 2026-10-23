---
description: New backend domain with a model, schemas, repository, service, exceptions, endpoints, migration and tests
argument-hint: <name>: <description>
---

Add a backend domain: $ARGUMENTS

The format is `<name>: <description>`, e.g. `messages: messages between a buyer and a seller`. The name is plural and snake_case.
If `docs/specs/<name>.md` exists (written by `/brief`), it is the agreed spec: follow it and skip the questions it already answers.

1. Read CLAUDE.md, docs/entities.md, `.claude/decisions.md` and `app/listings/` as the reference (`models/listing.py`, `schemas/listing.py`, `exceptions/listing.py`, `repositories/listing.py`, `services/listing.py`, `api/listing.py`, `routes.py`) plus `tests/unit/test_listings_api.py` and `tests/integration/test_listings.py`
2. Propose the table (columns with types, limits and constraints), relations to existing tables (foreign keys with `ondelete`), access rules (who may read, create, change, delete) and the routes, and wait for my confirmation
3. Create `app/<name>/` with no `__init__.py` anywhere in it (ADR-014) and these files, one entity per file name (singular):
   - `models/<entity>.py`: the table (`Mapped[]`, `TIMESTAMP(timezone=True)`, `CheckConstraint`, `ForeignKey(ondelete=...)`), enums as `StrEnum`
   - `schemas/<entity>.py`: `<Entity>CreateRequestSchema`, `<Entity>UpdateRequestSchema` (all optional), `<Entity>ResponseSchema` (on `CamelCaseResponseModel`)
   - `exceptions/<entity>.py`: `<Entity>NotFoundException(NotFoundException)`, `Not<Entity>OwnerException(ForbiddenException)`, each with `message` and `code`
   - `repositories/<entity>.py`: `I<Entity>Repository(Protocol)` + `@inject(alias=I<Entity>Repository)` class taking `ISessionFactory`; `select()` queries, `paginate` for lists, `flush()` never `commit()`
   - `services/<entity>.py`: `I<Entity>Service(Protocol)` + `@inject(alias=I<Entity>Service)` class taking the repository; ownership checks, domain exceptions, returns response schemas
   - `api/<entity>.py`: `router = DBAPIRouter(prefix="/<name>")`, one endpoint per route, services via `Depends(get_di_entity(...))`, writes with `Depends(get_current_user)`
   - `routes.py`: `APIRouter(tags=["<Name>"])` that includes the api router
4. Register the domain router in `app/routes.py` on `api_router`; models are picked up by `load_all_models()`, nothing else to register
5. Generate the migration with `poetry run makemigrations "create <name>"`, read the generated file in `alembic/versions/`, fix anything autogenerate got wrong, then `poetry run migrate`
6. Write the tests (the `/test-endpoint` skill has the template):
   - `tests/unit/test_<name>_api.py`: a `<entity>_service` mock fixture in `tests/unit/conftest.py`, then per route: status code, validation `422` with `fieldErrors`, `401` without a token, what was passed to the service
   - `tests/integration/test_<name>.py`: happy path per route through the API, `403` with `other_auth_headers`, `404`, a `<entity>_id` fixture in `tests/integration/conftest.py` (built through `POST`) and the new table in `clean_tables`
7. Update docs/entities.md: field table, relations, access rules and the route table with status codes and error codes
8. Tell the user which frontend file (`src/features/<name>/api/<name>-api.ts` in the frontend repo) now needs real `fetch` calls, and that `list()` must read the `items` field of the paginated response; the frontend repo also gets the same docs/entities.md change (ADR-001)
9. Run `poetry run lint --fix && poetry run typecheck && poetry run test && poetry run alembic check` in the repo root and fix what fails; `alembic check` must say that no new upgrade operations were detected
