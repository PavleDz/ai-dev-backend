from __future__ import annotations

from logging import INFO, Formatter, Handler, StreamHandler, getLogger

__all__ = ["getLogger", "set_up_logging"]

logger = getLogger(__name__)


def set_up_logging() -> None:
    """One StreamHandler with one format for the root logger and the app logger."""
    root_logger = getLogger()
    root_logger.handlers = _get_handlers()

    app, *_ = __name__.split(".")
    app_logger = getLogger(app)
    app_logger.handlers = _get_handlers()
    app_logger.level = INFO
    app_logger.propagate = False

    logger.info("Logging setup finished")


def _get_handlers() -> list[Handler]:
    handler = StreamHandler()
    handler.setFormatter(
        Formatter("[%(levelname)s] %(message)s - %(pathname)s:%(lineno)s %(funcName)s")
    )
    return [handler]
