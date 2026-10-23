from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import ceil
from typing import Annotated, Any, cast

from fastapi import Query
from pydantic import BaseModel, ConfigDict, NonNegativeInt
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select


class Page[T](BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    total: NonNegativeInt
    items: Sequence[T]
    pages: NonNegativeInt | None


@dataclass
class PaginationParams:
    page: int
    size: int


def get_pagination_params(
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    size: Annotated[int, Query(le=500, description="Page size")] = 50,
) -> PaginationParams:
    return PaginationParams(page=page, size=size)


def paginate[T](query: Select[T], pagination_params: PaginationParams, db: Session) -> Page[T]:
    total = cast(
        int,
        db.scalar(select(func.count()).select_from(query.order_by(None).subquery())),
    )

    pages = None
    limit = None
    offset = None
    if pagination_params.size > 0:
        limit = pagination_params.size
        offset = (pagination_params.page - 1) * limit
        pages = ceil(total / limit)

    items: list[Any] = list(db.scalars(query.limit(limit).offset(offset)).all())

    return Page(total=total, items=items, pages=pages)
