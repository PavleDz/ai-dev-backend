from __future__ import annotations

import sqlite3
from typing import Protocol

from sqlalchemy import URL, Engine, create_engine, event, make_url
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from sqlalchemy.pool import ConnectionPoolEntry

from app.config.settings import DBSettings
from app.utils.di import inject


def construct_db_url(database_url: str) -> URL:
    return make_url(database_url)


class ISessionFactory(Protocol):
    url: URL
    engine: Engine

    def __call__(self) -> Session:
        """returns Session (connection) objects based on current thread"""


@inject(alias=ISessionFactory, singleton=True)
class SessionFactory(ISessionFactory):
    def __init__(self, settings: DBSettings):
        self.url = construct_db_url(settings.DATABASE_URL)
        is_sqlite = self.url.get_backend_name() == "sqlite"

        if is_sqlite:
            # FastAPI serves requests from a thread pool, so one connection may change threads.
            self.engine = create_engine(self.url, connect_args={"check_same_thread": False})
            event.listen(self.engine, "connect", _enable_sqlite_foreign_keys)
        else:
            self.engine = create_engine(
                self.url,
                pool_pre_ping=True,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
            )

        session_maker = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)
        self._session_factory = scoped_session(session_maker)

    def __call__(self) -> Session:
        return self._session_factory()


def _enable_sqlite_foreign_keys(
    connection: sqlite3.Connection, _record: ConnectionPoolEntry
) -> None:
    # SQLite ignores foreign keys (and ON DELETE CASCADE) unless every connection turns them on.
    connection.execute("PRAGMA foreign_keys=ON")
