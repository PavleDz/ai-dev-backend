from __future__ import annotations

from pydantic import Field

from app.listings.models.listing import ListingCategory
from app.utils.schemas import CamelCaseModel, CamelCaseResponseModel, UtcDatetime


class ListingCreateRequestSchema(CamelCaseModel):
    title: str = Field(min_length=3, max_length=80)
    description: str = Field(default="", max_length=2000)
    price: float = Field(ge=0)
    category: ListingCategory
    city: str = Field(min_length=1, max_length=80)
    image_url: str | None = Field(default=None, max_length=500)


class ListingUpdateRequestSchema(CamelCaseModel):
    """Every field optional: PATCH changes only what the client sends (`exclude_unset`)."""

    title: str | None = Field(default=None, min_length=3, max_length=80)
    description: str | None = Field(default=None, max_length=2000)
    price: float | None = Field(default=None, ge=0)
    category: ListingCategory | None = None
    city: str | None = Field(default=None, min_length=1, max_length=80)
    image_url: str | None = Field(default=None, max_length=500)


class ListingResponseSchema(CamelCaseResponseModel):
    id: int
    title: str
    description: str
    price: float
    category: ListingCategory
    city: str
    image_url: str | None
    created_at: UtcDatetime
    owner_id: int
