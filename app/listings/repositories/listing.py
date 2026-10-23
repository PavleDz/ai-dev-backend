from __future__ import annotations

from typing import Protocol

from sqlalchemy import select

from app.database.session_factory import ISessionFactory
from app.listings.models.listing import Listing
from app.utils.di import inject
from app.utils.pagination import Page, PaginationParams, paginate


class IListingRepository(Protocol):
    def get_all(self, search: str, pagination_params: PaginationParams) -> Page[Listing]: ...

    def get_by_id(self, listing_id: int) -> Listing | None: ...

    def add(self, listing: Listing) -> Listing: ...

    def delete(self, listing: Listing) -> None: ...


@inject(alias=IListingRepository)
class ListingRepository(IListingRepository):
    def __init__(self, session_factory: ISessionFactory) -> None:
        self._session_factory = session_factory

    def get_all(self, search: str, pagination_params: PaginationParams) -> Page[Listing]:
        db = self._session_factory()
        query = select(Listing).order_by(Listing.created_at.desc(), Listing.id.desc())
        if search:
            query = query.where(Listing.title.ilike(f"%{search}%"))  # a bound parameter, not SQL
        return paginate(query=query, pagination_params=pagination_params, db=db)

    def get_by_id(self, listing_id: int) -> Listing | None:
        db = self._session_factory()
        return db.get(Listing, listing_id)

    def add(self, listing: Listing) -> Listing:
        db = self._session_factory()
        db.add(listing)
        db.flush()  # assigns id and created_at; the endpoint's session handler commits (ADR-009)
        return listing

    def delete(self, listing: Listing) -> None:
        db = self._session_factory()
        db.delete(listing)
        db.flush()
