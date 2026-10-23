from __future__ import annotations

from app.utils.exceptions import ForbiddenException, NotFoundException


class ListingNotFoundException(NotFoundException):
    def __init__(self) -> None:
        super().__init__(message="Listing not found", code="listing_not_found")


class NotListingOwnerException(ForbiddenException):
    def __init__(self) -> None:
        super().__init__(message="Only the owner can change this listing", code="not_listing_owner")
