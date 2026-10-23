from __future__ import annotations

from fastapi import APIRouter

from app.auth.api.auth import router as auth_router

router = APIRouter(prefix="/auth", tags=["Auth"])

router.include_router(auth_router)
