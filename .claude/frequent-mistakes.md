# Frequent mistakes

A living log. When the agent makes the same mistake twice, add one line here: the mistake, the rule
that fixes it, the ADR behind the rule. The reviewer agents and `/review-changes` read this file first,
so a mistake logged here is caught in the next review instead of the one after. Keep entries short and
concrete; delete an entry when the mistake has not shown up for a while.

Format: `- **<what went wrong>** → <the rule> (ADR-0XX)`

## Backend

- **`ownerId` accepted from the request body** → the owner is `current_user.id` from `get_current_user`; request schemas have no `id` or `ownerId` field (ADR-006)
- **Query or ownership `if` written inside `app/<domain>/api/`** → an endpoint calls one service method; queries live in the repository, rules and exceptions in the service (ADR-014)
- **`db.commit()` called in a repository or service** → repositories `flush()`; the endpoint's `DBAPIRouter` commits on return and rolls back on raise (ADR-009)
- **Service or repository class without a `Protocol` and `@inject(alias=...)`, or a constructor that builds its own repository** → `I<Name>Service(Protocol)` + `@inject(alias=I<Name>Service)`; constructors take Protocols and the container resolves them; tests then mock the Protocol (ADR-015)
- **`__init__.py` files created in `app/<domain>/` and its subfolders** → only `app/__init__.py` exists under `app/`; domain packages are namespace packages (ADR-014)
- **`uv`, `pip install` or `python -m` used instead of the Poetry commands** → `poetry install`, `poetry run start | test | lint | typecheck | makemigrations | migrate | seed`; a dependency is proposed and the user runs `poetry add` (ADR-013)
- **Model changed, no migration generated: the table exists only on the agent's laptop** → every model change gets `poetry run makemigrations "<what>"`, read the file, `poetry run migrate`, then `poetry run alembic check` (ADR-004)
- **A committed file under `alembic/versions/` edited "to fix the migration"** → migrations are history; add a new revision (ADR-004)
- **`Base.metadata.create_all()` added to `app/app.py` "so the tables exist"** → tables come from migrations; `create_all` is allowed only in `tests/integration/conftest.py` (ADR-004)
- **Service returns the SQLAlchemy model (`-> Listing`) and the endpoint is annotated with it** → services return `...ResponseSchema.model_validate(model)`; the endpoint's return annotation is the schema (ADR-010)
- **`from __future__ import annotations` missing at the top of a new file** → ruff requires it in every file; `poetry run lint --fix` adds it (ADR-017)
- **`DateTime(timezone=True)` with `default=lambda: datetime.now(UTC)` for `created_at`** → `TIMESTAMP(timezone=True)` with `server_default=func.now()`; `sqlalchemy.DateTime` is a banned import (ADR-008)
- **Only the happy path tested, or only integration tests** → every route gets a unit test with the service mocked plus integration tests for `401` on writes, `403` where there is an owner, `404` where there is an id, `422` with `fieldErrors` where there is input (ADR-011)
- **`async def` endpoint on the sync session** → plain `def`; the sync engine must not run on the event loop (ADR-009)
- **`raise HTTPException(status_code=..., detail=...)` in a service, or `except Exception: pass` around a database call** → raise a domain exception from `app/<domain>/exceptions/` with `message` and `code`; catch `IntegrityError` and raise the `ConflictException` subclass; never swallow (ADR-005)
- **Secret pasted into `settings.py` or a test "because `.env` did not load"** → defaults stay dev-only placeholders; the real value goes in `.env`, which the agent never reads or writes (rules/safety.md)
- **Uniqueness checked with a `SELECT` before the `INSERT`** → `unique=True` on the column and `IntegrityError` → `409` (ADR-007)
- **List endpoint returns `list[...ResponseSchema]` with every row** → `PaginationParams` in, `Page[...ResponseSchema]` out, `paginate()` in the repository (ADR-016)

## Contract

- **Schema or route changed, `docs/entities.md` left as it was** → doc and code move together in one commit; run `contract-keeper` when unsure, and say that the frontend repo needs the same doc change (ADR-001, ADR-002)
- **Contract changed here, frontend repo never told** → the PR description names the frontend change (`src/features/<name>/api/<name>-api.ts` and `types.ts` in the frontend repo); a list client must read `items` (ADR-001, ADR-016)
