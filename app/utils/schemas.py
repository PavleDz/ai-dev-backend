from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from humps import camelize
from pydantic import AfterValidator, BaseModel, ConfigDict, StringConstraints

NonBlankStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


def _as_utc(value: datetime) -> datetime:
    # SQLite returns naive datetimes, Postgres returns aware ones; the API always answers in UTC.
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


UtcDatetime = Annotated[datetime, AfterValidator(_as_utc)]


class CamelCaseModel(BaseModel):
    """Base of every request/response schema: snake_case in Python, camelCase in JSON."""

    model_config = ConfigDict(alias_generator=camelize, populate_by_name=True)


class CamelCaseResponseModel(CamelCaseModel):
    """Response schema that can be built straight from a SQLAlchemy model (`model_validate`)."""

    model_config = ConfigDict(alias_generator=camelize, populate_by_name=True, from_attributes=True)
