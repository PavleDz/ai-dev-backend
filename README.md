# AI-DEV 2026 · Workshop 4 · Backend starter

FastAPI API with a SQLite/Postgres database and JWT auth, laid out the way a production service is:
one package per domain, services and repositories behind Protocols, dependency injection, one
transaction per request, strict typing. Set up for working with Claude Code (`.claude/`).

The frontend from Workshop 3 lives in its own repository. The contract between the two is
`docs/entities.md`: field names, types, routes, status codes and the error shape. A change to it is made
in both repositories in the same pull request.

## Run it

Prerequisites: Python 3.13 and [Poetry](https://python-poetry.org/docs/#installation)
(`pipx install poetry`, or `curl -sSL https://install.python-poetry.org | python3 -`).

```bash
poetry install            # creates .venv (in the project) and installs everything from poetry.lock
poetry run migrate        # creates data/app.db with all tables (alembic upgrade head)
poetry run seed           # demo user demo@example.com / demo1234 and 3 listings
poetry run start          # http://localhost:8000/docs
```

Configuration is read from `.env` (copy `.env.example`); every variable has a working default.
The frontend dev server proxies `/api` to port 8000, so run both at once.

## Switch to Postgres

```bash
docker compose up -d db                               # postgres:17 on localhost:5432
echo 'DATABASE_URL=postgresql+psycopg://app:app@localhost:5432/app' >> .env
poetry run migrate && poetry run seed
```

Nothing else changes: the same models, migrations and tests run against both databases.

## Layout

```
manage.py                  the command line: runserver, test, lint, typecheck, makemigrations, migrate, seed
app/main.py                settings into the DI container, logging, `app = setup_app()`
app/app.py                 setup_app(): routers, exception handlers (one error shape), CORS, /live and /ready
app/routes.py              api_router (/api): includes every domain's routes.py
app/deps.py                get_di_entity (resolve a service), get_current_user / get_optional_user
app/config/settings.py     Settings and DBSettings (pydantic-settings, .env)
app/database/              Base (naming convention), SessionFactory, DBAPIRouter + db_session_handler
                           (one transaction per endpoint), load_all_models()
app/utils/                 di.py (kink), exceptions.py (hierarchy + codes), schemas.py (CamelCaseModel),
                           pagination.py (Page, paginate), logging.py
app/auth/                  password.py, api/auth.py, services/auth.py (JWT), repositories/auth.py, ...
app/users/models/user.py   the user table
app/listings/              the reference domain, replace with yours:
  api/listing.py           endpoints (DBAPIRouter): HTTP in, HTTP out, nothing else
  services/listing.py      IListingService + ListingService: rules, ownership, domain exceptions
  repositories/listing.py  IListingRepository + ListingRepository: queries, flush, no commit
  models/listing.py        the table (Mapped[], constraints, relationships)
  schemas/listing.py       ListingCreateRequestSchema, ListingUpdateRequestSchema, ListingResponseSchema
  exceptions/listing.py    ListingNotFoundException, NotListingOwnerException
  routes.py                APIRouter(tags=["Listings"]) that includes api/listing.py
app/seed.py                demo data through the services, idempotent
alembic/                   env.py reads DATABASE_URL and imports every model; versions/ are history
tests/                     unit/ (API layer, services mocked) and integration/ (real temp SQLite)
docs/entities.md           the contract with the frontend
data/                      local SQLite file (gitignored)
```

There is no `__init__.py` below `app/`: domains are namespace packages, and `load_all_models()`
finds every `app/<domain>/models/*.py` on its own.

## Everyday commands

```bash
poetry run test                                   # pytest; `poetry run pytest tests/unit -q` for a subset
poetry run lint                                   # ruff check + black --check; `--fix` fixes and formats
poetry run typecheck                              # mypy, strict
poetry run makemigrations "add x to listings"     # after changing a model; read the generated file
poetry run migrate                                # apply migrations
poetry run alembic check                          # fails if a model changed without a migration
poetry add <package>                              # add a dependency (updates pyproject.toml and poetry.lock)
```

## First steps with Claude

1. `/brief <feature>` for anything bigger than a field: Claude interviews you, writes `docs/specs/<feature>.md`, you confirm.
2. `/new-entity <name>: <description>` for each entity in `docs/entities.md`; the `listings` example shows the shape, delete it when yours exist.
3. `/api-check`, then `/review-changes` before every commit: three reviewer agents read the diff in parallel and give one verdict.
4. `contract-keeper` when `docs/entities.md` and the code drift apart; `/check-n1` when a list is slow; `/test-endpoint` when a route lacks tests.
5. When Claude makes the same mistake twice, add one line to `.claude/frequent-mistakes.md`; the reviewers read it.

## What is in the .claude folder

| File | Purpose |
| --- | --- |
| `CLAUDE.md` | Stack, domain-package structure, rules, "done when", how the agent is kept honest |
| `.claude/rules/` | `backend-api`, `backend-db`, `backend-tests`, `anti-patterns` (WRONG/RIGHT pairs copied from the reference domain) load for matching files; `safety.md` always loads. Rules cite the ADR they come from |
| `.claude/decisions.md` | ADR-001…017: why the repo works this way (contract, migrations, error shape, owner from token, constraints, UTC, one transaction per endpoint, camelCase, tests, no SQL strings, Poetry, domain packages, DI, pagination, strict typing) |
| `.claude/frequent-mistakes.md` | Living log: one line per repeated mistake, read by every reviewer agent |
| `.claude/commands/` | `/brief` (interview → `docs/specs/<feature>.md`), `/new-entity`, `/api-check`, `/review-changes` (parallel reviewers → one verdict) |
| `.claude/skills/backend-patterns/` | Endpoint, service, repository, model, auth, error and migration patterns that load when working on the API |
| `.claude/skills/check-n1/` | Finds queries in loops and relationships read per row without `selectinload`/`joinedload` |
| `.claude/skills/test-endpoint/` | The standard test set for one route (unit with mocked service; integration happy, 401, 403, 404, 422) |
| `.claude/agents/api-reviewer.md` | Reviews correctness, layers, contract and tests; changes nothing |
| `.claude/agents/security-reviewer.md` | Reviews auth on writes, ownership (IDOR), secrets, SQL injection, tokens, CORS; changes nothing |
| `.claude/agents/migration-reviewer.md` | Reviews model vs migration, autogenerate pitfalls and the revision chain; changes nothing |
| `.claude/agents/contract-keeper.md` | Compares `docs/entities.md` with the code and may edit only the doc |
| `.claude/settings.json` | Permissions (poetry, curl, migrations allowed; force push, hard reset, downgrade and volume deletion denied), Explanatory output style, and the five hooks below |
| `.claude/hooks/session-start.mjs` | SessionStart: branch, last commits, where the rules live |
| `.claude/hooks/guard-bash.mjs` | PreToolUse (Bash): blocks destructive git, `rm -rf` on source trees, `alembic downgrade`, volume deletion, destructive SQL, reading `.env`, and unapproved `poetry add` |
| `.claude/hooks/guard-edits.mjs` | PreToolUse (Edit/Write): blocks editing a committed migration, `.env` and `poetry.lock` |
| `.claude/hooks/format.mjs` | PostToolUse: ruff + black on the edited file |
| `.claude/hooks/verify-changes.mjs` | Stop: ruff + black + mypy + pytest on changed files; a failure sends the agent back to work once |
| `.mcp.json` | Context7 (current library docs) |
| `.github/workflows/ci.yml` | lint, mypy and pytest on every push and pull request |

The hooks are Node scripts so they run on Windows, macOS and Linux without extra installs.
