---
paths:
  - "app/**/api/**"
  - "app/**/schemas/**"
  - "app/**/routes.py"
---

# Backend API

- An endpoint in `app/<domain>/api/<name>.py` parses input, calls one method of the domain service (`I<Name>Service`, resolved with `Depends(get_di_entity(I<Name>Service))`) and returns its result; queries, ownership checks and exceptions live in the service and repository (ADR-014)
- Routers are `DBAPIRouter` from `app.database.session_handler`: every endpoint runs in one transaction, committed on return, rolled back on raise; nothing in a service or repository calls `commit()` (ADR-009)
- Endpoint functions are plain `def`, not `async def`: the database session is synchronous (ADR-009)
- The return type annotation is the response schema (`-> ListingResponseSchema`, `-> Page[ListingResponseSchema]`); a `204` sets `response_model=None`; every schema extends `CamelCaseModel` or `CamelCaseResponseModel` from `app.utils.schemas`, so JSON is camelCase in and out (ADR-010)
- Status codes: `POST` returns `status.HTTP_201_CREATED`, `DELETE` returns `status.HTTP_204_NO_CONTENT` and no body, missing record `404`, not the owner `403`, invalid input `422` with `fieldErrors` (ADR-005)
- Every write endpoint (`POST`, `PATCH`, `DELETE`) takes `current_user: Annotated[CurrentUser, Depends(get_current_user)]` from `app.deps` unless `docs/entities.md` says it is public (ADR-006)
- The record id comes from the path (`/{listing_id}`), the owner from `current_user.id`; request schemas have no `id` or `ownerId` field (ADR-006)
- Validation limits in `schemas/<name>.py` (`min_length`, `max_length`, `ge`, `StrEnum`) match `docs/entities.md` exactly (ADR-002)
- `PATCH` uses a `...UpdateRequestSchema` where every field is optional and the service applies `model_dump(exclude_unset=True)`
- List endpoints take `pagination_params: Annotated[PaginationParams, Depends(get_pagination_params)]` and return `Page[...ResponseSchema]` (`total`, `items`, `pages`) (ADR-016)
- `app/<domain>/routes.py` collects the domain's api routers under one `APIRouter(tags=[...])`; it is registered in `app/routes.py` on `api_router`; the path in `docs/entities.md` is the full path including `/api`
- Every endpoint has `summary=` (and `description=` when the summary is not enough); they are what `/docs` shows the frontend team
