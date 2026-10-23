from __future__ import annotations

from unittest.mock import Mock

from sqlalchemy import URL, Engine
from sqlalchemy.orm import Session

from app.database.session_factory import ISessionFactory


class MockSessionFactory(ISessionFactory):
    """A fake session factory: unit tests never touch a database."""

    def __init__(self) -> None:
        self.url: URL = Mock(spec=URL)
        self.engine: Engine = Mock(spec=Engine)

    def __call__(self) -> Session:
        return Mock(spec=Session)
