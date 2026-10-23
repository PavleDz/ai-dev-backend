---
description: Review the current changes with the reviewer agents in parallel, run the checks, give one verdict
argument-hint: [file paths]
allowed-tools: Bash(git diff:*), Bash(git log:*), Bash(git status), Bash(git branch:*), Bash(poetry run lint:*), Bash(poetry run typecheck), Bash(poetry run test:*), Bash(poetry run alembic check), Agent
---

Review the changes before they are committed. Agents review; you consolidate and decide.

## 1. Find the changed files
1. If arguments were given (`$ARGUMENTS`), review exactly those files.
2. Otherwise, on a branch other than `main`: `git diff main...HEAD --name-only --diff-filter=ACMR`.
3. If that is empty (you are on `main`, or nothing is committed yet): `git diff --name-only --diff-filter=ACMR HEAD` plus `git status --short` for untracked files.
If there is nothing, say "No changes to review." and stop.

## 2. Get the diff
`git diff main...HEAD -- <files>` or `git diff HEAD -- <files>`; for untracked files read them whole. Keep the diff and the file list: every agent gets both.

## 3. Launch the reviewers in parallel
Use the Agent tool and launch all of them **in one message**, so they run at the same time. Pass each one the file list, the diff, and this sentence: "Read `.claude/rules/*`, `.claude/decisions.md` and `.claude/frequent-mistakes.md` first; cite the ADR for every finding."

| Agent | Always? | Focus |
|-------|---------|-------|
| `api-reviewer` | yes, when any `.py` file changed | thin routers, contract, error shape, tests |
| `security-reviewer` | yes, when any `.py` file changed | auth on writes, ownership/IDOR, secrets, SQL, tokens, CORS |
| `migration-reviewer` | yes, when any `.py` file changed (it answers "No schema changes." quickly if none) | model vs migration, autogenerate pitfalls, revision chain |
| `contract-keeper` | only when `docs/entities.md`, a file under `app/*/schemas/` or `app/*/api/` changed | doc and code agree |

## 4. Run the checks yourself (while the agents work)
- `poetry run lint && poetry run typecheck && poetry run test` and `poetry run alembic check`, from the repo root
Record PASS/FAIL and the last lines of any failure.

## 5. Consolidate
Merge the agents' tables into one. When two agents report the same problem (same file and line, or clearly the same cause), keep one row and raise its confidence.

**Confidence:** found by 3 agents = 3/3 (certain) · by 2 = 2/3 (very likely) · by 1 and it is a rule or ADR violation = 1/3 (worth fixing) · by 1 and subjective = note it under "Also mentioned", not in the table.

```
## Review: <branch or "uncommitted changes"> · <date>
**Files:** <n> · **Agents:** api, security, migration[, contract]
**Checks:** lint PASS/FAIL · mypy PASS/FAIL · pytest PASS/FAIL (<n> passed) · alembic check PASS/FAIL

| # | Severity | Confidence | File:Line | Problem | Fix | ADR / rule | Found by |
|---|----------|------------|-----------|---------|-----|------------|----------|

**Verdict: APPROVED | NEEDS CHANGES | BLOCKED**
**Done well:** <merged positives, two lines at most>
**Also mentioned:** <subjective single-agent remarks, one line each>
```

**Verdict rules:**
- **BLOCKED**: any HIGH from `security-reviewer`, a new or changed route without tests, a migration that fails or loses data, or a failing check
- **NEEDS CHANGES**: any other HIGH, or three or more MEDIUM
- **APPROVED**: everything else; list the LOW items so I can decide

## 6. Close the loop
End with two things:
1. The fixes in the order you would make them (do not make them in this command; I decide)
2. "Repeated mistake? Add a line to `.claude/frequent-mistakes.md`." and, if a finding matches an entry that is already there, say which one, because that means the log needs a sharper rule, not another line
