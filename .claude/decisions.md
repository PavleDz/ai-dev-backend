# Decisions

Why this repo does things the way it does. Each entry is an ADR (architecture decision record):
context, the decision, and what it costs or buys. Rules in `.claude/rules/` and the reviewer agents
cite these numbers, so the rule and the reason stay linked. Add a new ADR when you make a choice the
team would otherwise re-discuss; never renumber an old one, mark it "superseded by ADR-0XX" instead.

### ADR-001 · The backend is its own repository; the contract travels with every change
**Context:** a feature almost always touches the backend, the frontend and `docs/entities.md` in between, but the two sides live in separate repositories.
**Decision:** this repository holds only the backend; `docs/entities.md` is the shared contract and a copy of it lives in the frontend repo. A change to the contract is made in both repositories in the same round of pull requests, and the backend PR names the frontend change it requires.
**Consequence:** nothing is "merged on one side only" by accident: `contract-keeper` reports "Contract changed: yes" and the frontend repo gets the same edit before the feature is called done.

### ADR-002 · `docs/entities.md` is the contract
**Context:** frontend and backend are built in different workshops, in different repositories, sometimes by different people.
**Decision:** fields, types, routes, status codes, error codes and the error shape are agreed in `docs/entities.md` before code; code and doc change in the same commit.
**Consequence:** code is the source of truth for what the system *does*, the doc for what was *agreed*; `contract-keeper` reports where they differ.

### ADR-003 · SQLite by default, Postgres through `DATABASE_URL`
**Context:** students must run the API in minutes on any laptop; some teams deploy to Postgres.
**Decision:** `sqlite:///./data/app.db` is the default; `DATABASE_URL` switches to Postgres with no code change; `SessionFactory` picks the engine options per backend; migrations use `render_as_batch=True` so they run on both.
**Consequence:** every column type and constraint must work on both engines; no engine-specific SQL.

### ADR-004 · Schema changes are migrations; committed migrations are history
**Context:** a table that exists only on the agent's laptop breaks every teammate and CI.
**Decision:** no `Base.metadata.create_all` outside `tests/integration/conftest.py`; every model change gets an Alembic revision through `poetry run makemigrations "<what>"`; a revision that is committed is never edited (`guard-edits` enforces it), a new one is added instead.
**Consequence:** `poetry run alembic check` is part of "done"; autogenerate output is read and fixed before `poetry run migrate`.

### ADR-005 · One error shape: `{"detail", "code", "fieldErrors"?}`
**Context:** clients (the frontend repo) show errors next to fields, switch on a stable code, and need one predictable format; the author's production backends answer `{"detail", "code"}`.
**Decision:** services raise a domain exception from `app/<domain>/exceptions/` that extends one of `NotFoundException`, `InvalidRequestException`, `UnauthenticatedException`, `ForbiddenException`, `ConflictException`, `ServerException` (`app/utils/exceptions.py`) with a human `message` and a snake_case `code`; the handlers in `app/app.py` map the base class to the status and answer `{"detail": message, "code": code}`, plus `"fieldErrors"` when a field is at fault; Pydantic's `422` is rewritten to the same shape with `code: "validation_error"`. No bare `HTTPException`, no status codes in services, no swallowed exceptions.
**Consequence:** clients (the frontend repo's `ApiError`) read `message` (from `detail`), `code` and `fieldErrors`; tests assert on the body, not just the status.

### ADR-006 · The owner comes from the token, never from the body
**Context:** `ownerId` in a request body lets any signed-in user create or claim records as someone else.
**Decision:** write endpoints depend on `get_current_user` (`CurrentUser`); the service sets `owner_id=current_user.id`; request schemas have no `id` or `ownerId`; ownership is checked in the service and raises the domain's `Not...OwnerException` (`403`).
**Consequence:** IDOR is a review item for `security-reviewer`; tests include a `403` for every owned record.

### ADR-007 · Invariants are database constraints, not `if` statements
**Context:** "one email per user" checked with a `SELECT` then `INSERT` fails under two concurrent requests, and does not hold for rows written by a script.
**Decision:** `unique=True`, `CheckConstraint`, `nullable` and `ForeignKey(ondelete=...)` carry the rules; Pydantic validates input for a good message, the database guarantees the data; the service turns `IntegrityError` into a `ConflictException` subclass (`409` with `fieldErrors`).
**Consequence:** every constraint is a migration, and the same limits appear in `schemas/`, the `StrEnum` in `models/` and `docs/entities.md`.

### ADR-008 · Timestamps are `TIMESTAMP(timezone=True)` with `server_default=func.now()`
**Context:** naive datetimes take the server's local timezone, which differs between laptops, CI and a server; a Python-side default is skipped by anything that writes rows without the ORM.
**Decision:** every timestamp column is `TIMESTAMP(timezone=True)` (`sqlalchemy.DateTime` is banned by ruff) with `server_default=func.now()`; `UtcDatetime` in `app/utils/schemas.py` serializes as `...Z` whatever the engine returned.
**Consequence:** clients (the frontend repo) receive one format; `DateTime`, `datetime.now()` and `datetime.utcnow()` are review findings.

### ADR-009 · SQLAlchemy 2 typed style, one transaction per endpoint, synchronous `def`
**Context:** `async def` endpoints with a sync session block the event loop and hide the bug until load; commits scattered through services make rollback on error impossible.
**Decision:** `Mapped[]` + `mapped_column`, `select()` queries; every endpoint is registered on a `DBAPIRouter`, whose `db_session_handler` opens the thread-scoped session, commits when the endpoint returns and rolls back when it raises; repositories call `flush()` and never `commit()`; route functions are plain `def` (FastAPI runs them in a thread pool).
**Consequence:** no `async def` in `api/` or `services/` unless the code awaits something that is truly async; no `Column()`, no `session.query()`, no `commit()` outside `app/database/`.

### ADR-010 · camelCase JSON through `CamelCaseModel`; endpoints return schemas, not models
**Context:** Python is snake_case, TypeScript is camelCase; converting by hand drifts; a model returned from an endpoint lazy-loads after the session is closed.
**Decision:** every request schema extends `CamelCaseModel`, every response schema `CamelCaseResponseModel` (`alias_generator=camelize` from pyhumps, `populate_by_name`, `from_attributes`); services build `...ResponseSchema.model_validate(model)` and the endpoint's return annotation is that schema (FastAPI derives `response_model` from it).
**Consequence:** `imageUrl` in JSON is `image_url` in Python; a schema that does not extend one of the two bases, or an endpoint annotated with a model, is a bug.

### ADR-011 · Tests are part of the endpoint, in two layers
**Context:** an endpoint that "works in the browser" is not verified for the cases that matter: no token, wrong user, unknown id, bad input; a suite that needs a database for every assertion is slow and hides which layer broke.
**Decision:** `tests/unit/test_<name>_api.py` tests the HTTP layer with the service replaced by `create_autospec(I...Service)` in the DI container (routing, validation, auth, error shape, what reached the service); `tests/integration/test_<name>.py` runs the whole stack against a temporary SQLite database through the API with the fixtures `auth_headers`, `other_auth_headers`, `<entity>_id`; every route has the happy path plus `401`, `403`, `404`, `422` with `fieldErrors` where they apply.
**Consequence:** `verify-changes` runs the suite when the agent stops; a new endpoint without tests is BLOCKED in `/review-changes`.

### ADR-012 · No SQL strings
**Context:** f-strings and `.format()` in SQL are injection; `text()` bypasses the typed models.
**Decision:** queries are built with `select()`, `update()`, `delete()` on the models inside repositories; filters are column expressions; `ilike(f"%{search}%")` is a parameter, not SQL.
**Consequence:** `text(` and `f"SELECT` are review findings; a query that cannot be expressed with the ORM is a design question, not a `text()`.

### ADR-013 · Poetry manages Python, `manage.py` is the command line, dependencies need approval
**Context:** mixed `pip`/`venv`/`uv` setups produce "works on my machine"; an unreviewed dependency is a supply-chain and licensing risk; the author's production backends use Poetry and a `manage.py` with `poetry run <command>` shortcuts, so the starter should feel the same.
**Decision:** Poetry only (`poetry install`, `poetry run`, `poetry add`), virtualenv in-project; `manage.py` defines the commands and `pyproject.toml` exposes them as `poetry run start | test | lint | typecheck | makemigrations | migrate | seed`; `poetry.lock` is generated, never edited; the agent proposes a dependency with name, reason and alternative and the user runs `poetry add` (`guard-bash` enforces it).
**Consequence:** `pyproject.toml` + `poetry.lock` are the single source of the environment; `pip install` and `uv` never appear in docs or commands; a new command is a `BaseCommand` subclass in `manage.py`, not an ad-hoc script.

### ADR-014 · Domain packages with `api/`, `models/`, `repositories/`, `schemas/`, `services/`, `exceptions/`; thin endpoints
**Context:** a global `routers/`, `models/`, `schemas/` split spreads one entity over distant folders; logic in endpoints cannot be tested or reused; the author's production backends group everything about one domain under `app/<domain>/` with one subfolder per role, and that is the layout students will meet at work.
**Decision:** `app/<domain>/{api,models,repositories,schemas,services,exceptions}/<entity>.py` plus `routes.py`; no `__init__.py` below `app/` (namespace packages; mypy runs with `explicit_package_bases`, `load_all_models()` walks `app/*/models/`); an endpoint parses input, calls one service method and returns; rules and ownership live in the service, the session and the queries in the repository; shared code lives in `app/database/`, `app/utils/`, `app/config/`, `app/deps.py`; dependency direction is `utils/database/config -> domains -> app.routes -> app.app`, and domains import each other only through models under `TYPE_CHECKING` or through another domain's Protocols.
**Consequence:** a new entity is one folder plus one migration, two test files and one section in `docs/entities.md` (`/new-entity`); a `__init__.py` under `app/<domain>/` is a review finding.

### ADR-015 · Dependency injection with kink: a Protocol per service and repository
**Context:** services that build their own repositories (and repositories that build their own engine) cannot be replaced in a test, so every test needs a database; FastAPI's `Depends` alone wires HTTP, not the layers below it.
**Decision:** every service and repository declares a `Protocol` (`IListingService`) and registers its implementation with `@inject(alias=IListingService)` from `app/utils/di.py`; constructors take Protocols and `ISessionFactory` and are resolved by the container; endpoints get a service with `Depends(get_di_entity(IListingService))`; `SessionFactory` and `Settings` are singletons; tests override with `add_to_di_container(IFoo, mock)` and restore with `remove_from_di_container(IFoo)`.
**Consequence:** a service or repository must be imported somewhere reachable from `app/routes.py` (the `api/` module imports it) so the decorator runs before the first request; a class without a Protocol and `@inject` is a review finding.

### ADR-016 · Lists are paginated with `Page[T]`
**Context:** a `GET` that returns every row works with 3 seeded records and times out with 30 000; adding pagination later changes the contract for every client.
**Decision:** list endpoints take `PaginationParams` (`?page=`, `?size=` capped at 500, from `get_pagination_params`), repositories return `Page[Model]` through `paginate()` in `app/utils/pagination.py`, services map it to `Page[...ResponseSchema]`, and the JSON is `{"total", "items", "pages"}`.
**Consequence:** clients (the frontend repo) read `items`; a list endpoint without `pagination_params` is a review finding.

### ADR-017 · Strict typing: mypy strict, ruff's full rule set, black, `from __future__ import annotations`
**Context:** an untyped backend lets the agent return a model where a schema was expected, pass a string where an enum was agreed, or forget a `-> None`; the author's production backends run the same strict configuration, so a project that passes here passes there.
**Decision:** `pyproject.toml` enables mypy strict options (`disallow_untyped_defs`, `warn_return_any`, pydantic plugin, ...) for `app/` and `tests/`, the ruff rule groups from production (E, F, B, I, UP, RUF, TID, FAST, TRY, DTZ, PT, SIM, ARG, N, ...), black at 100 columns, and `from __future__ import annotations` as a required import in every file; `poetry run lint` and `poetry run typecheck` must pass before "done", and `verify-changes` runs them when the agent stops.
**Consequence:** `sqlalchemy.DateTime` and `kink.inject` are banned imports (use `TIMESTAMP` and `app.utils.di.inject`); a `# type: ignore` needs a code and a reason.
