from __future__ import annotations

from fastapi import APIRouter

from app.auth.routes import router as auth_router
from app.listings.routes import router as listings_router

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(listings_router)
