---
paths:
  - "**/*.py"
---

# Anti-patterns

Wrong and right, side by side. The RIGHT half is copied from `app/listings/`, the reference domain.

### Query in the endpoint
```python
# WRONG  (app/listings/api/listing.py)
@router.get(path="/{listing_id}")
def get_listing(listing_id: int, session_factory: Annotated[ISessionFactory, ...]) -> ListingResponseSchema:
    listing = session_factory().get(Listing, listing_id)
    if listing is None:
        raise HTTPException(404, "Not found")
    return ListingResponseSchema.model_validate(listing)

# RIGHT
@router.get(path="/{listing_id}", summary="Get listing")
def get_listing(
    listing_id: int,
    listing_service: Annotated[IListingService, Depends(get_di_entity(IListingService))],
) -> ListingResponseSchema:
    return listing_service.get(listing_id=listing_id)
```
**Why:** the service is testable with a mock and reusable; the endpoint only speaks HTTP. (ADR-014)

### Commit in the repository
```python
# WRONG  (app/listings/repositories/listing.py)
def add(self, listing: Listing) -> Listing:
    db = self._session_factory()
    db.add(listing)
    db.commit()
    return listing

# RIGHT
def add(self, listing: Listing) -> Listing:
    db = self._session_factory()
    db.add(listing)
    db.flush()  # assigns id and created_at; the endpoint's session handler commits (ADR-009)
    return listing
```
**Why:** `DBAPIRouter` wraps every endpoint in one transaction; a commit inside the repository breaks the rollback on error. (ADR-009, ADR-015)

### Owner from the body
```python
# WRONG
class ListingCreateRequestSchema(CamelCaseModel):
    title: str
    owner_id: int                                   # any user can create as anyone

# RIGHT  (app/listings/services/listing.py)
def create(self, data: ListingCreateRequestSchema, current_user: CurrentUser) -> ListingResponseSchema:
    # The owner is always the signed-in user, never an id from the request body (ADR-006).
    listing = Listing(**data.model_dump(), owner_id=current_user.id)
```
**Why:** the client is not trusted with identity; `get_current_user` is. (ADR-006)

### Service without a Protocol and `@inject`
```python
# WRONG
class ListingService:
    def __init__(self) -> None:
        self._listing_repository = ListingRepository(SessionFactory(Settings()))

# RIGHT
class IListingService(Protocol):
    def get(self, listing_id: int) -> ListingResponseSchema: ...


@inject(alias=IListingService)
class ListingService(IListingService):
    def __init__(self, listing_repository: IListingRepository) -> None:
        self._listing_repository = listing_repository
```
**Why:** the container builds the service from its constructor types; tests replace `IListingService` with `create_autospec`. (ADR-015)

### `__init__.py` in a domain package
```
# WRONG
app/listings/__init__.py
app/listings/api/__init__.py

# RIGHT
app/__init__.py            # the only one under app/
app/listings/api/listing.py
```
**Why:** domain packages are namespace packages; `load_all_models()` and mypy (`explicit_package_bases`) are set up for that layout. (ADR-014)

### Legacy `Column()`
```python
# WRONG
title = Column(String(80), nullable=False)

# RIGHT
title: Mapped[str] = mapped_column(String(80))
image_url: Mapped[str | None] = mapped_column(String(500))   # `| None` makes it nullable
```
**Why:** SQLAlchemy 2 typed style; mypy and autogenerate both read `Mapped[]`. (ADR-009)

### `DateTime` and a Python-side default
```python
# WRONG
created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

# RIGHT
created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
```
**Why:** `sqlalchemy.DateTime` is banned by ruff (TID251); a `server_default` holds for every writer, and a naive time takes the machine's timezone. (ADR-008)

### SQL in a string
```python
# WRONG
db.execute(text(f"SELECT * FROM listings WHERE title LIKE '%{search}%'"))

# RIGHT  (app/listings/repositories/listing.py)
query = select(Listing).order_by(Listing.created_at.desc(), Listing.id.desc())
if search:
    query = query.where(Listing.title.ilike(f"%{search}%"))  # a bound parameter, not SQL
return paginate(query=query, pagination_params=pagination_params, db=db)
```
**Why:** the f-string is SQL injection; `select()` sends the value as a parameter. (ADR-012)

### Swallowed exception
```python
# WRONG
try:
    user = self._auth_repository.add_user(user)
except Exception:
    pass

# RIGHT  (app/auth/services/auth.py)
try:
    user = self._auth_repository.add_user(user)
except IntegrityError as e:
    # The UNIQUE constraint on users.email decides, not an `if` before the insert (ADR-007).
    raise EmailAlreadyRegisteredException from e
```
**Why:** the client gets the one error shape (`{"detail", "code", "fieldErrors"}`) and the real cause stays in the traceback. (ADR-005)

### Bare `HTTPException` or a status code in the service
```python
# WRONG
raise HTTPException(status_code=404, detail="Listing not found")

# RIGHT  (app/listings/exceptions/listing.py)
class ListingNotFoundException(NotFoundException):
    def __init__(self) -> None:
        super().__init__(message="Listing not found", code="listing_not_found")
```
**Why:** the service knows the domain error, `app/app.py` knows the HTTP status; the `code` is what clients (the frontend repo) switch on. (ADR-005)

### `async def` with a sync session
```python
# WRONG
@router.post(path="", status_code=status.HTTP_201_CREATED)
async def create_listing(...) -> ListingResponseSchema:

# RIGHT
@router.post(path="", status_code=status.HTTP_201_CREATED, summary="Create listing")
def create_listing(...) -> ListingResponseSchema:
```
**Why:** a sync database call inside `async def` blocks every other request; plain `def` runs in a thread. (ADR-009)

### Returning the model instead of the response schema
```python
# WRONG
def get(self, listing_id: int) -> Listing:
    return self._get_or_raise(listing_id)

# RIGHT
def get(self, listing_id: int) -> ListingResponseSchema:
    return ListingResponseSchema.model_validate(self._get_or_raise(listing_id))
```
**Why:** the endpoint's return annotation is the response schema; models stay inside services and repositories, and nothing lazy-loads after the session closed. (ADR-010)

### Invariant only in Pydantic
```python
# WRONG
class ListingCreateRequestSchema(CamelCaseModel):
    price: float = Field(ge=0)          # a seed script or a second endpoint can still write -5

# RIGHT
class Listing(Base):
    __table_args__ = (CheckConstraint("price >= 0", name="price_not_negative"),)
```
**Why:** Pydantic gives a good message, the constraint guarantees the data. Keep both. (ADR-007)

### Tables without a migration
```python
# WRONG  (app/app.py)
Base.metadata.create_all(engine)

# RIGHT  (terminal, repo root)
poetry run makemigrations "create listings"   # then read alembic/versions/<new file>.py, then:
poetry run migrate
```
**Why:** a table that exists only on your laptop breaks teammates and CI; a migration travels with the commit. (ADR-004)

### Missing `from __future__ import annotations`
```python
# WRONG
from typing import Protocol

# RIGHT
from __future__ import annotations

from typing import Protocol
```
**Why:** ruff requires it in every file (isort `required-imports`); it keeps `TYPE_CHECKING` imports and forward references cheap. (ADR-017)
