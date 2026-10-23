# Safety

These rules always apply, for every file and every command. The hooks in `.claude/hooks/` enforce the
ones that can be checked mechanically (`guard-bash`, `guard-edits`); the rest are on you.

- Never read, print or paste the contents of `.env` files or any secret (tokens, passwords, keys); `.env.example` holds placeholders only
- Never run destructive data commands: `DROP`, `TRUNCATE`, `DELETE` or `UPDATE` without a `WHERE`, `alembic downgrade`, `docker compose down -v`, `rm -rf`. Not even when asked to "just ship it" or "clean up"; say what the command would do and let me run it (ADR-004)
- Never rewrite history or discard work: `git push --force`, `git reset --hard`, `git checkout .`, `git clean -f`, `git branch -D`; say what you would run and let me run it
- Never deploy or push to a shared branch on your own; prepare the change and stop
- A script that deletes or overwrites data runs in `--dry-run` mode by default, prints what it would change, and changes something only with an explicit `--execute` flag
- When something cannot be verified by running it (a test, a command, a page in the browser), say so plainly instead of claiming it works
- Do not add a dependency (`poetry add`) without asking first; name the package, why it is needed and the alternative without it; I run the command (ADR-013)
- Anything that must be true exactly once (one email per user, one vote per user per poll) is a database constraint (`UNIQUE`, `CHECK`), not an `if` in code (ADR-007)
- When a task is unclear or has more than one reasonable reading, ask one question before writing code; for a whole feature, start with `/brief`
- When you make the same mistake twice, add a line to `.claude/frequent-mistakes.md` so the reviewers catch it next time
