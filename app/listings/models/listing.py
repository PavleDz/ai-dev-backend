from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import TIMESTAMP, CheckConstraint, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.users.models.user import User


class ListingCategory(StrEnum):
    GAMES = "games"
    CONSOLES = "consoles"
    ACCESSORIES = "accessories"


_CATEGORY_LIST = ", ".join(f"'{category.value}'" for category in ListingCategory)


# Example entity, replace with your own (see docs/entities.md).
class Listing(Base):
    __tablename__ = "listings"
    # Invariants live in the database, so they hold no matter which code writes the row (ADR-007).
    __table_args__ = (
        CheckConstraint("price >= 0", name="price_not_negative"),
        CheckConstraint(f"category IN ({_CATEGORY_LIST})", name="category_known"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(Text, default="")
    # asdecimal=False: the API speaks JSON numbers, not decimal strings.
    price: Mapped[float] = mapped_column(Numeric(10, 2, asdecimal=False))
    category: Mapped[str] = mapped_column(String(20))
    city: Mapped[str] = mapped_column(String(80))
    image_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    owner: Mapped[User] = relationship("User", back_populates="listings")
