---
paths:
  - "app/**/models/**"
  - "app/**/repositories/**"
  - "app/**/services/**"
  - "alembic/**"
---

# Backend database

- Models live in `app/<domain>/models/<name>.py` and use SQLAlchemy 2.0 style: `class X(Base)`, `Mapped[type]` annotations and `mapped_column(...)`; no `Column(...)` and no untyped attributes (ADR-009)
- `Base` comes from `app.database.base` and carries the naming convention, so every index and constraint has a predictable name that a later migration can drop
- Every table has `id: Mapped[int] = mapped_column(primary_key=True)` and `created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())`; `sqlalchemy.DateTime` is banned by ruff, use `TIMESTAMP` (ADR-008)
- Every foreign key sets `ondelete` (`CASCADE` or `SET NULL`) and `index=True`; relationships use string targets (`relationship("User", back_populates=...)`) and the other model is imported under `if TYPE_CHECKING:` so modules never import each other at runtime
- Allowed values are a `StrEnum` in the models module (`ListingCategory`) and a `CheckConstraint` on the column; schemas reuse the enum
- What must hold for every row is enforced by the database: `unique=True`, `CheckConstraint`, `nullable`; Pydantic validates input, the constraint guarantees the data; the service turns an `IntegrityError` into a `ConflictException` subclass (`409`) (ADR-007)
- Repositories (`app/<domain>/repositories/<name>.py`) are the only place that touches the session: `db = self._session_factory()`, `select()` on the models, `db.flush()` after `add`/`delete`, never `db.commit()`; the endpoint's `DBAPIRouter` commits (ADR-009, ADR-015)
- Queries are built with `select()` on the models; never `text()`, f-strings or `.format()` with SQL, never `session.query()` (ADR-012)
- A list endpoint that reads a relationship on every row loads it with `selectinload` / `joinedload` in the same query; a query inside a loop is an N+1 (`/check-n1` finds them)
- Lists go through `paginate(query=..., pagination_params=..., db=db)` from `app.utils.pagination` and return `Page[Model]`; the service maps it to `Page[...ResponseSchema]` (ADR-016)
- Never call `Base.metadata.create_all` in app code; tables and columns come from migrations only (`tests/integration/conftest.py` may use it on its temporary database) (ADR-004)
- A model change is a migration: `poetry run makemigrations "<what changed>"`, then read the generated file in `alembic/versions/` and fix what autogenerate missed (renames, data moves, a `server_default` for a new `NOT NULL` column on a table with rows) before `poetry run migrate` (ADR-004)
- A new domain only needs a `models/` folder: `load_all_models()` imports every `app/*/models/*.py` for the app and for alembic, nothing is registered by hand
- Never edit a migration that has already been committed; add a new one (`guard-edits` blocks it) (ADR-004)
- Never run `alembic downgrade` on a database with real data without asking first (`guard-bash` blocks it)
- `poetry run alembic check` passes before a commit: no model change without a migration (ADR-004)
- Works on SQLite and Postgres alike: no engine-specific types or SQL; migrations use `render_as_batch=True` (ADR-003)
