"""Demo data for development: `poetry run seed`. Idempotent: running it twice changes nothing."""

from __future__ import annotations

import logging

from app.auth.schemas.auth import LoginRequestSchema, RegisterRequestSchema
from app.auth.services.auth import IAuthService
from app.database.session_handler import db_session_handler
from app.listings.models.listing import ListingCategory
from app.listings.schemas.listing import ListingCreateRequestSchema
from app.listings.services.listing import IListingService
from app.utils.di import get_from_di_container
from app.utils.pagination import PaginationParams

logger = logging.getLogger(__name__)

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "demo1234"

DEMO_LISTINGS = [
    ListingCreateRequestSchema(
        title="PlayStation 5 Slim",
        description="Used for six months, two controllers, original box.",
        price=380,
        category=ListingCategory.CONSOLES,
        city="Podgorica",
    ),
    ListingCreateRequestSchema(
        title="Elden Ring (PS5)",
        description="Disc in perfect condition.",
        price=35,
        category=ListingCategory.GAMES,
        city="Nikšić",
    ),
    ListingCreateRequestSchema(
        title="DualSense controller, white",
        description="Barely used.",
        price=45,
        category=ListingCategory.ACCESSORIES,
        city="Budva",
    ),
]


@db_session_handler
def seed() -> None:
    auth_service = get_from_di_container(IAuthService)
    listing_service = get_from_di_container(IListingService)

    try:
        auth = auth_service.login(LoginRequestSchema(email=DEMO_EMAIL, password=DEMO_PASSWORD))
        logger.info("Demo user already exists: %s", DEMO_EMAIL)
    except Exception:
        auth = auth_service.register(
            RegisterRequestSchema(
                email=DEMO_EMAIL, password=DEMO_PASSWORD, display_name="Demo User"
            )
        )
        logger.info("Created demo user %s / %s", DEMO_EMAIL, DEMO_PASSWORD)

    current_user = auth_service.get_current_user(auth.token)
    existing = listing_service.list(search="", pagination_params=PaginationParams(page=1, size=1))
    if existing.total:
        logger.info("Listings already exist (%s), nothing to do", existing.total)
        return

    for data in DEMO_LISTINGS:
        listing_service.create(data=data, current_user=current_user)
    logger.info("Created %s demo listings", len(DEMO_LISTINGS))
