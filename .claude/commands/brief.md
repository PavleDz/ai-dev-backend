---
description: Interview me about a feature until we agree, then write the spec to docs/specs/<feature>.md
argument-hint: <feature description>
---

Brief me before anything is built: $ARGUMENTS

No code and no plan until we share the same picture of the feature. Interview me, one question at a time.

## 1. Explore first, ask second
Before the first question, read `docs/entities.md`, `.claude/decisions.md`, the existing domains in
`app/`, and `docs/specs/` if it exists. Anything the codebase
already answers (which entities exist, how auth works, what the error shape is) is not a question for me.

## 2. Interview
One question per message, with your best guess as the default so I can just say "yes". Walk down each branch until it is
resolved before opening the next one:
- **Goal:** who uses this and what do they get; what is the smallest version that is useful
- **Entities and fields:** new table or new columns on an existing one; for each field the type, required or optional, limits, default; which invariants are database constraints (ADR-007)
- **Relations:** foreign keys, `ondelete` behaviour, what happens to children when the parent goes
- **Routes:** method, path, body, response, status codes; which fields are set by the backend (`id`, `createdAt`, `ownerId`) (ADR-006, ADR-010)
- **Access rules:** who may read, create, change, delete; public, signed-in, owner, nobody
- **Error cases:** `401`, `403`, `404`, `409`, `422` and the message for each (ADR-005)
- **Tests:** the test list for every route (happy path plus the error cases above) (ADR-011)
- **Out of scope:** what we deliberately leave out

Stop asking when every row of the spec below can be filled in without guessing. Do not pad the interview.

## 3. Write the spec
Write `docs/specs/<feature>.md` (kebab-case name) with exactly these sections:
```
# <Feature>
## Goal
## Entities & fields        (table per entity: field | type | required | limits | notes; relations below it)
## Routes                   (method | path | auth | body | responses with status codes)
## Access rules
## Error cases              (status | when | detail | code)
## Done when                (checklist: tests, migration, docs/entities.md updated, poetry checks green)
```
Keep it under 80 lines. Show it to me and ask for confirmation; change it until I confirm.

## 4. Hand over
When confirmed, say which command comes next: `/new-entity <name>: <description>` to build it,
`/review-changes` before the commit, and remind me that the frontend repo needs the same `docs/entities.md` change (ADR-001).
Do not start building inside this command.
