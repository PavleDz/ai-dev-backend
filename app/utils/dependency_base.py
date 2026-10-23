from __future__ import annotations

from typing import Any


class DependencyBase:
    """Class-based dependency base.
    This class serves as a workaround to https://github.com/tiangolo/fastapi/issues/4557
    """

    __globals__: Any = None

    def __init_subclass__(cls, **kw: Any) -> None:
        super().__init_subclass__(**kw)
        cls.__globals__ = cls.__call__.__globals__
