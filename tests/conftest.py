from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.app import setup_app
from app.config.settings import DBSettings, Settings
from app.utils.di import add_to_di_container
from tests.utils import TestSettings

settings = TestSettings(
    JWT_SECRET_KEY="test_secret_key_with_at_least_32_bytes!", DATABASE_URL="sqlite://"
)
add_to_di_container(Settings, settings)
add_to_di_container(DBSettings, settings)


@pytest.fixture(scope="session")  # only setup app once
def app() -> FastAPI:
    return setup_app()


@pytest.fixture
def client(app: FastAPI) -> Generator[TestClient]:
    with TestClient(app) as c:
        yield c
