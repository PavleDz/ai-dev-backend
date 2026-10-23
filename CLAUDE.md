# Backend

Python 3.13 · FastAPI · SQLAlchemy 2 (typed `Mapped[]`) · Pydantic 2 · Alembic · PyJWT + bcrypt · kink (DI) ·
pytest · ruff + black + mypy (strict) · Poetry. SQLite by default, Postgres via `DATABASE_URL`.
Entities and the API contract are in @docs/entities.md (the frontend lives in its own repository and carries a copy
of the same file; a contract change is made in both). All code, identifiers, comments, commit messages and docs are
in English; you may talk to me in any language.

## Read before writing code

| Task | Read first |
|------|-----------|
| A whole feature, before anything else | `/brief` → `docs/specs/<feature>.md`, then `docs/entities.md` |
| New entity (model + schemas + repository + service + api + tests) | `/new-entity`; `app/listings/` is the reference; `.claude/skills/backend-patterns` |
| Model or migration | `.claude/rules/backend-db.md` · ADR-003, ADR-004, ADR-007, ADR-008 in `.claude/decisions.md` |
| Endpoint or schema | `.claude/rules/backend-api.md` · ADR-005, ADR-006, ADR-010, ADR-014, ADR-016 |
| Service, repository, query, ownership | `.claude/rules/backend-db.md`, `.claude/rules/anti-patterns.md` · ADR-006, ADR-009, ADR-012, ADR-015 |
| Auth, tokens, settings | `app/auth/services/auth.py`, `app/deps.py`, `app/config/settings.py` · `.claude/rules/safety.md` |
| Tests | `.claude/rules/backend-tests.md`, `/test-endpoint` · ADR-011 |
| A slow list endpoint | `/check-n1` |
| Something that went wrong before | `.claude/frequent-mistakes.md` |
| Why we do it this way | `.claude/decisions.md` |
| Before a commit | `/api-check`, then `/review-changes` |

## One package per domain
Every domain lives in `app/<domain>/` with one folder per role, each holding one module per entity:
`api/` (endpoints on a `DBAPIRouter`), `services/` (`I<Name>Service` Protocol + `@inject` class: rules,
ownership, domain exceptions, returns response schemas), `repositories/` (`I<Name>Repository` + class:
queries on the session, `flush()`, never `commit()`), `models/` (tables), `schemas/` (request/response),
`exceptions/` (subclasses of `app/utils/exceptions.py` with a `code`), and `routes.py` (the domain's
`APIRouter` with tags) registered in `app/routes.py`. No `__init__.py` below `app/` (ADR-014).
Dependency direction: utils/database/config -> domain -> app, never the other way around.

## Structure
- `manage.py`: `poetry run start | test | lint | typecheck | makemigrations "<what>" | migrate | seed`
- `app/main.py`: settings into the DI container, logging, `app = setup_app()`
- `app/app.py`: `setup_app()`, exception handlers (one error shape), CORS, `/live`, `/ready`
- `app/routes.py`: `api_router` with prefix `/api`; every domain's `routes.py` is included here
- `app/deps.py`: `get_di_entity(IService)`, `get_current_user` (401 without a token), `get_optional_user`
- `app/config/settings.py`: `Settings` / `DBSettings` from the environment and `.env`
- `app/database/`: `Base`, `SessionFactory` (`ISessionFactory`), `DBAPIRouter` + `db_session_handler`, `load_all_models()`
- `app/utils/`: `di.py`, `exceptions.py`, `schemas.py` (`CamelCaseModel`, `CamelCaseResponseModel`, `UtcDatetime`), `pagination.py` (`Page[T]`, `paginate`), `logging.py`
- `app/auth/`: register/login/me, `password.py` (bcrypt), `services/auth.py` (JWT HS256), `schemas/auth.py` (`CurrentUser`)
- `app/users/models/user.py`, `app/listings/` (reference domain), `app/seed.py`
- `alembic/versions/`: one migration per schema change, generated with `poetry run makemigrations`
- `tests/unit/` (API layer with mocked services, `MockSessionFactory`), `tests/integration/` (real temp SQLite; fixtures `client`, `auth_headers`, `other_auth_headers`, `listing_id`)

## Rules
- Every file starts with `from __future__ import annotations`; ruff, black and mypy strict must pass (ADR-017)
- Endpoints stay thin: `Depends(get_di_entity(IFooService))`, one service call, return the response schema; no queries, no `if` on ownership, no status codes in a service; plain `def`, not `async def` (ADR-014, ADR-009)
- A service has a Protocol and `@inject(alias=IFooService)`; a repository takes `ISessionFactory` and only flushes; the endpoint's `DBAPIRouter` commits or rolls back (ADR-009, ADR-015)
- Schemas extend `CamelCaseModel` / `CamelCaseResponseModel` (camelCase JSON); endpoints return schemas, never models; lists return `Page[...]` (ADR-010, ADR-016)
- Every write endpoint takes `current_user: Annotated[CurrentUser, Depends(get_current_user)]`; the owner is always `current_user.id`, never an id from the body (ADR-006)
- Errors are domain exceptions (`NotFoundException`, `ForbiddenException`, `ConflictException`, ...) with a `code`; the client receives `{"detail", "code", "fieldErrors"?}` (ADR-005)
- Models use `Mapped[]` + `mapped_column`, `TIMESTAMP(timezone=True)` with `server_default=func.now()` (never `DateTime`), `ForeignKey(..., ondelete=...)`, relationships by string name with `TYPE_CHECKING` imports (ADR-008, ADR-009)
- What must hold for every row (unique, non-negative, allowed values) is a database constraint, not only a Pydantic check (ADR-007)
- Queries are `select()` on the models; no SQL strings, no `text()` (ADR-012)
- A schema change is a migration: `poetry run makemigrations "<what>"`, read the file, `poetry run migrate`; a committed migration is never edited; no `create_all` in app code (ADR-004)
- Settings come from `app.config.settings` through the container, never `os.environ` in a domain, never hard-coded secrets
- A dependency is proposed (name, why, alternative) and I run `poetry add <package>`; `poetry.lock` is never edited (ADR-013)
- If you are not sure how a library API works (FastAPI, SQLAlchemy 2, Pydantic 2, Alembic, kink), check the docs via Context7, do not guess
- The same mistake twice goes into `.claude/frequent-mistakes.md`

## How the agent is kept honest
Rules in markdown are requests. These are guarantees, wired in `.claude/settings.json` (Node hooks, so they run on every OS):
`guard-bash` blocks `git push --force`, `git reset --hard`, `rm -rf` on source trees, `alembic downgrade`, `docker compose down -v`, destructive SQL, reading `.env` and `poetry add` (a dependency needs my approval; I run it); `guard-edits` blocks editing a committed migration, `.env` and `poetry.lock`; `format` runs ruff + black after every edit; `verify-changes` runs ruff + black + mypy + pytest when you stop and sends you back once if red; `/review-changes` runs `api-reviewer`, `security-reviewer` and `migration-reviewer` in parallel for one verdict.

## Done when
- `poetry run lint && poetry run typecheck && poetry run test` pass (the Stop hook runs them too)
- Every endpoint has tests: unit (routing, auth, validation with the service mocked) and integration (happy path and 401/403/404/422 where they apply) (ADR-011)
- `poetry run alembic check` reports no missing migration
- `docs/entities.md` describes every field and route exactly as the code does (ADR-002)
- No secrets in code or in git (`.env` stays local; `.env.example` has placeholders only)
- `/review-changes` says APPROVED
