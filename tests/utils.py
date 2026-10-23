from __future__ import annotations

from datetime import UTC, datetime

from pydantic_settings import SettingsConfigDict

from app.auth.schemas.auth import CurrentUser
from app.config.settings import Settings


class TestSettings(Settings):
    """Settings for tests: never reads `.env`, so a developer's local config cannot leak in."""

    model_config = SettingsConfigDict(env_file=None, use_enum_values=True, extra="allow")


def create_current_user(id: int = 1, email: str = "test@example.com") -> CurrentUser:
    return CurrentUser(
        id=id, email=email, display_name="Test User", created_at=datetime(2026, 1, 1, tzinfo=UTC)
    )
