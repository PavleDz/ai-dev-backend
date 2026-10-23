---
description: All backend checks before a commit
---

1. Run `poetry run lint`, `poetry run typecheck` and `poetry run test` in the repo root and fix the errors
2. Run `poetry run alembic check` in the repo root; if it reports changes, a model changed without a migration: generate one with `poetry run makemigrations "<what changed>"` and read the file (ADR-004)
3. Start the API (`poetry run start`) and call every route in docs/entities.md with `curl`, including the error cases: without a token (`401`), as another user (`403`), an unknown id (`404`), invalid input (`422`). Check that status codes, camelCase keys and the error shape match the tables in docs/entities.md (ADR-005, ADR-010)
4. Compare docs/entities.md with `app/*/api/*.py` and `app/*/schemas/*.py`: every route, field, limit and status code must be in both places; fix the one that is wrong (code is the source of truth for what it does, the doc for what was agreed) (ADR-002)
5. Give me a short report: what passes, what you fixed, what I should look at myself
6. Then run `/review-changes`: it launches the reviewer agents on the diff and gives one verdict
