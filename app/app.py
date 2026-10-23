from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config.settings import Settings
from app.database.import_sqlalchemy_models import load_all_models
from app.database.session_factory import ISessionFactory
from app.database.session_handler import db_session_handler
from app.deps import get_di_entity
from app.routes import api_router
from app.utils.di import get_from_di_container
from app.utils.exceptions import (
    AppBaseException,
    ConflictException,
    ForbiddenException,
    HTTPExceptionWithCode,
    InvalidRequestException,
    NotFoundException,
    ServerException,
    UnauthenticatedException,
)

logger = logging.getLogger(__name__)

STATUS_BY_EXCEPTION: dict[type[AppBaseException], int] = {
    NotFoundException: status.HTTP_404_NOT_FOUND,
    InvalidRequestException: status.HTTP_400_BAD_REQUEST,
    UnauthenticatedException: status.HTTP_401_UNAUTHORIZED,
    ForbiddenException: status.HTTP_403_FORBIDDEN,
    ConflictException: status.HTTP_409_CONFLICT,
    ServerException: status.HTTP_500_INTERNAL_SERVER_ERROR,
}


def add_liveness_and_readiness_checks(app: FastAPI) -> None:
    @app.get("/live", include_in_schema=False)
    def liveness_check() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready", include_in_schema=False)
    @db_session_handler
    def readiness_check(
        session_factory: Annotated[ISessionFactory, Depends(get_di_entity(ISessionFactory))],
    ) -> dict[str, str]:
        session = session_factory()
        session.execute(text("SELECT 1"))
        return {"status": "ok"}


def add_exception_handlers(app: FastAPI, settings: Settings) -> None:
    """One error shape for the whole API: {"detail", "code"} plus "fieldErrors" per field (ADR-005)."""

    @app.exception_handler(AppBaseException)
    def app_exception_handler(_request: Request, exc: AppBaseException) -> JSONResponse:
        status_code = next(
            (code for base, code in STATUS_BY_EXCEPTION.items() if isinstance(exc, base)),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        headers = {"WWW-Authenticate": "Bearer"} if status_code == 401 else None
        return JSONResponse(
            status_code=status_code, content=exc.response_content(), headers=headers
        )

    @app.exception_handler(HTTPExceptionWithCode)
    def http_exception_with_code_handler(
        _request: Request, exc: HTTPExceptionWithCode
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "code": exc.code},
            headers=exc.headers or {},
        )

    @app.exception_handler(StarletteHTTPException)
    def http_exception_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
        # Raised by FastAPI itself, e.g. 404 for an unknown route or 405 for a wrong method.
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": str(exc.detail), "code": "http_error"},
            headers=exc.headers or {},
        )

    @app.exception_handler(RequestValidationError)
    def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # loc looks like ("body", "title") or ("query", "search"); the first error per field wins.
        field_errors: dict[str, str] = {}
        for error in exc.errors():
            field = ".".join(str(part) for part in error["loc"][1:]) or str(error["loc"][0])
            field_errors.setdefault(field, error["msg"])
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Validation failed",
                "code": "validation_error",
                "fieldErrors": field_errors,
            },
        )

    # fastapi's default exception handler doesn't send CORS headers
    # (because it removes all headers that were set by other middleware)
    @app.exception_handler(Exception)
    async def default_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled error", exc_info=exc)
        origin = request.headers.get("Origin", "")
        headers = None
        if origin in settings.ALLOWED_ORIGINS:
            headers = {
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
            }
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal Server Error", "code": "internal_error"},
            headers=headers,
        )


def setup_middleware(app: FastAPI, settings: Settings) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def setup_app() -> FastAPI:
    app = FastAPI(title="AI-DEV API", version="0.1.0", redirect_slashes=False)

    app.include_router(api_router)

    load_all_models()

    add_liveness_and_readiness_checks(app)

    settings = get_from_di_container(Settings)

    add_exception_handlers(app, settings)

    setup_middleware(app, settings)

    return app
