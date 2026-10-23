from __future__ import annotations

from collections.abc import Callable
from typing import Any

from kink import di
from kink import inject as kink_inject  # noqa: TID251


def add_to_di_container[T](key: type[T], value: T) -> None:
    di[key] = value


def get_from_di_container[T](key: type[T]) -> T:
    return di[key]


def inject(alias: Any | None = None, singleton: bool = False) -> Any:
    """Register a class in the DI container under its Protocol (`alias`).

    `singleton=False` (the default) builds a fresh instance on every resolve, which is what lets
    tests override a service with a mock and restore it by removing the override.
    """
    return kink_inject(alias=alias, use_factory=not singleton)


def remove_from_di_container(key: type[Any]) -> None:
    del di._services[key]  # noqa: SLF001


def get_di_entity[T](entity: type[T]) -> Callable[[], T]:
    """FastAPI dependency that resolves `entity` from the container at request time."""
    return lambda: get_from_di_container(entity)
