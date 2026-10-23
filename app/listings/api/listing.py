from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Query, status

from app.auth.schemas.auth import CurrentUser
from app.database.session_handler import DBAPIRouter
from app.deps import get_current_user, get_di_entity
from app.listings.schemas.listing import (
    ListingCreateRequestSchema,
    ListingResponseSchema,
    ListingUpdateRequestSchema,
)
from app.listings.services.listing import IListingService
from app.utils.pagination import Page, PaginationParams, get_pagination_params

router = DBAPIRouter(prefix="/listings")


@router.get(
    path="", summary="List listings", description="Newest first; `search` matches the title."
)
def get_listings(
    listing_service: Annotated[IListingService, Depends(get_di_entity(IListingService))],
    pagination_params: Annotated[PaginationParams, Depends(get_pagination_params)],
    search: Annotated[str, Query(max_length=80)] = "",
) -> Page[ListingResponseSchema]:
    return listing_service.list(search=search, pagination_params=pagination_params)


@router.get(path="/{listing_id}", summary="Get listing")
def get_listing(
    listing_id: int,
    listing_service: Annotated[IListingService, Depends(get_di_entity(IListingService))],
) -> ListingResponseSchema:
    return listing_service.get(listing_id=listing_id)


@router.post(path="", status_code=status.HTTP_201_CREATED, summary="Create listing")
def create_listing(
    data: ListingCreateRequestSchema,
    listing_service: Annotated[IListingService, Depends(get_di_entity(IListingService))],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> ListingResponseSchema:
    return listing_service.create(data=data, current_user=current_user)


@router.patch(path="/{listing_id}", summary="Update listing (owner only)")
def update_listing(
    listing_id: int,
    data: ListingUpdateRequestSchema,
    listing_service: Annotated[IListingService, Depends(get_di_entity(IListingService))],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> ListingResponseSchema:
    return listing_service.update(listing_id=listing_id, data=data, current_user=current_user)


@router.delete(
    path="/{listing_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete listing (owner only)",
)
def delete_listing(
    listing_id: int,
    listing_service: Annotated[IListingService, Depends(get_di_entity(IListingService))],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> None:
    listing_service.delete(listing_id=listing_id, current_user=current_user)
