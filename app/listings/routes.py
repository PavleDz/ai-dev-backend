from __future__ import annotations

from fastapi import APIRouter

from app.listings.api.listing import router as listing_router

router = APIRouter(tags=["Listings"])

router.include_router(listing_router)
