from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class DBSettings(BaseSettings):
    """Database settings only: alembic and the session factory need nothing else."""

    # SQLite needs no setup. Postgres: postgresql+psycopg://app:app@localhost:5432/app
    DATABASE_URL: str = "sqlite:///./data/app.db"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    model_config = SettingsConfigDict(env_file=".env", use_enum_values=True, extra="ignore")


class Settings(DBSettings):
    ENVIRONMENT: str = "dev"

    # Development default only. Set a random JWT_SECRET_KEY in .env for anything that leaves your
    # laptop: `python -c "import secrets; print(secrets.token_hex(32))"`.
    JWT_SECRET_KEY: str = "dev-only-secret-change-me-before-sharing"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    # NOTE: ALLOWED_ORIGINS='["http://localhost:5173","https://app.example.com"]'
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]
