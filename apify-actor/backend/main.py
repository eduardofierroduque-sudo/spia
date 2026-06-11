import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.analysis import router as privacy_router
from app.api.settings import router as settings_router
from app.api.checkout import router as checkout_router
from app.core.config import get_settings
from app.core.security import (
    APIKeyMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    InputSanitizer,
    audit_logger,
)

logging.basicConfig(level=logging.WARNING, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("spia")


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]

    app = FastAPI(
        title="SPIA — Privacy Auditor",
        version="0.2.1",
        docs_url="/docs",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=["Content-Type", "Authorization", "X-API-Key"],
    )

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(APIKeyMiddleware)

    @app.middleware("http")
    async def log_and_validate(request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"

        query_string = request.url.query or ""
        path = request.url.path or ""
        if InputSanitizer.detect_attack(query_string) or InputSanitizer.detect_attack(path):
            audit_logger.log("blocked_attack", client_ip, "Suspicious pattern in URL")
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid input detected"},
            )

        response = await call_next(request)
        return response

    app.include_router(privacy_router)
    app.include_router(settings_router)
    app.include_router(checkout_router)

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        client_ip = request.client.host if request.client else "unknown"
        audit_logger.log("error", client_ip, str(exc)[:200])
        logger.error("Unhandled exception: %s", str(exc)[:300])
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    return app


app = create_app()
