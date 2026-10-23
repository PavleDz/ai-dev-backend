# Entities

> This file is the contract between the frontend and the backend.
> For each entity: fields with types, relations, who is allowed to do what, and the routes.
> The backend code lives in `app/<name>/` (`models/`, `schemas/`, `repositories/`, `services/`, `api/`, `exceptions/`,
> `routes.py`). The frontend repository carries a copy of this file; its entity type is `src/features/<name>/types.ts`
> and its API functions `src/features/<name>/api/<name>-api.ts`. A change here is a change there, in the same PR.

## Conventions

- Base path: `/api` (the frontend calls `/api/...`; in development Vite proxies it to port 8000)
- JSON keys are camelCase (`imageUrl`, `createdAt`), in requests and responses
- Ids are integers assigned by the backend
- Dates are ISO 8601 strings in UTC (`2026-10-12T09:30:00Z`), assigned by the backend
- Auth: `POST /api/auth/register` or `POST /api/auth/login` return a token; protected routes take
  `Authorization: Bearer <token>`
- `POST` answers `201` with the created record, `DELETE` answers `204` with no body
- `GET` lists are paginated: `?page=1&size=50` (size ≤ 500) answers `{"total", "items", "pages"}`, newest first
- Every error has one shape: `{"detail": "...", "code": "snake_case_code"}` plus `fieldErrors` when a field is at fault; 401 responses also carry `WWW-Authenticate: Bearer`

| Status | When | Body |
| --- | --- | --- |
| 401 | missing token / invalid token / wrong password | `{"detail": "Authentication required", "code": "not_authenticated"}` / `"invalid_token"` / `"invalid_credentials"` |
| 403 | signed in, but not the owner | `{"detail": "Only the owner can change this listing", "code": "not_listing_owner"}` |
| 404 | record does not exist | `{"detail": "Listing not found", "code": "listing_not_found"}` |
| 409 | email already registered | `{"detail": "Email is already registered", "code": "email_already_registered", "fieldErrors": {"email": "Email is already registered"}}` |
| 422 | invalid input | `{"detail": "Validation failed", "code": "validation_error", "fieldErrors": {"title": "String should have at least 3 characters"}}` |

## User

Code: `app/users/models/user.py`, `app/users/schemas/user.py`; register/login/me in `app/auth/`.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| id | number | yes | assigned by the backend |
| email | string, valid email | yes | unique, stored lowercase |
| displayName | string, 1–60 characters | yes | |
| createdAt | date | yes | assigned by the backend |

The password (8–72 characters) is sent only on register and login; it is never returned.

| Route | Auth | Body | Response |
| --- | --- | --- | --- |
| `POST /api/auth/register` | no | `{email, password, displayName}` | `201 {token, user}`, `409` duplicate email |
| `POST /api/auth/login` | no | `{email, password}` | `200 {token, user}`, `401` wrong email or password |
| `GET /api/auth/me` | yes | | `200` user |

## Listing (example, replace with your own)

Code: `app/listings/` (`models/listing.py`, `schemas/listing.py`, `repositories/listing.py`, `services/listing.py`, `api/listing.py`, `exceptions/listing.py`, `routes.py`).

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| id | number | yes | assigned by the backend |
| title | string, 3–80 characters | yes | |
| description | string | no | defaults to `""` |
| price | number ≥ 0, EUR | yes | |
| category | `games` \| `consoles` \| `accessories` | yes | |
| city | string | yes | |
| imageUrl | URL or `null` | no | |
| createdAt | date | yes | assigned by the backend |
| ownerId | number | yes | the signed-in user who created it; assigned by the backend |

**Relations:** a listing belongs to one user (the seller, `ownerId`). Deleting a user deletes their listings.

**Access rules:** everyone can see listings; only a signed-in user can create one; only the owner can edit or delete it.

| Route | Auth | Body | Response |
| --- | --- | --- | --- |
| `GET /api/listings?search=&page=&size=` | no | | `200 {total, items, pages}`, newest first; `search` matches the title, case-insensitive |
| `GET /api/listings/:id` | no | | `200` listing, `404` |
| `POST /api/listings` | yes | `{title, description?, price, category, city, imageUrl?}` | `201` listing, `401`, `422` |
| `PATCH /api/listings/:id` | owner | any subset of the fields above | `200` listing, `401`, `403`, `404`, `422` |
| `DELETE /api/listings/:id` | owner | | `204`, `401`, `403`, `404` |
