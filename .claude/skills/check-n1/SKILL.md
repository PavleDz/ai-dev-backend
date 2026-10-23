---
name: check-n1
description: Find N+1 queries in the backend: a query inside a loop, or a relationship read per row in a list endpoint without selectinload/joinedload. Use when a list endpoint is slow, after adding a relationship, or when asked to "check for N+1".
allowed-tools: Read, Grep, Glob
---

# Check N+1

An N+1 is one query for the list plus one more query for every row. With 3 seeded listings nobody
notices; with 300 the page takes seconds. The fix is almost always one `selectinload` or `joinedload`.

## 1. Find the relationships
Grep `app/*/models/*.py` for `relationship(`. Note the model, the attribute name and whether
it is to-one (`Mapped[User]`) or to-many (`Mapped[list[Message]]`).

## 2. Find where they are read
For every relationship attribute (`listing.owner`, `listing.messages`), grep:
- `app/*/services/*.py` and `app/*/api/*.py` for `.<attribute>` reads
- `app/*/schemas/*.py` for a `...ResponseSchema` field with that name (`model_validate` reads it, once per row)

## 3. Find the queries that return lists
In every `repositories/*.py`: `paginate(`, `db.scalars(select(...)).all()` and `.all()` calls; in every `services/*.py`: any
`for ... in` whose body calls a repository method (`get_by_id`, `get_all`, ...). A query inside the loop body is an N+1 by definition.

## 4. Decide
A list query is clean when either no relationship is read for its rows, or the query has
`.options(selectinload(Model.attr))` (to-many) or `.options(joinedload(Model.attr))` (to-one) for every attribute that is read.
Note: in the reference `ListingRepository.get_all` returns plain `Listing` rows and `ListingResponseSchema` exposes `owner_id`, not `owner`, so no load is needed; the moment `ListingResponseSchema` gains `owner: UserResponseSchema`, it does.

## 5. Report
```
### N+1 check
| # | Severity | File:Line | Query | Reads | Fix |
|---|----------|-----------|-------|-------|-----|
| 1 | HIGH | app/listings/repositories/listing.py:27 | get_all | ListingResponseSchema.owner | `.options(joinedload(Listing.owner))` |
| 2 | HIGH | app/messages/services/message.py:31 | loop: `self._user_repository.get_by_id(m.sender_id)` | per row | one `get_by_ids(ids)` repository method before the loop |

**Clean:** <list queries you checked that need nothing>
```
Severity: HIGH = a list endpoint, MEDIUM = a detail endpoint reading a to-many relation, LOW = a loop over a bounded tiny set.

## Fix pattern (copy, rename)
```python
from sqlalchemy.orm import joinedload, selectinload

query = (
    select(Listing)
    .options(joinedload(Listing.owner))          # to-one: one JOIN
    .options(selectinload(Listing.messages))     # to-many: one extra IN (...) query, not one per row
    .order_by(Listing.created_at.desc(), Listing.id.desc())
)
```
Report only; the fix goes through the normal edit flow, with a test that creates several rows and asserts the list is still correct.
