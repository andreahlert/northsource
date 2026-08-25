"""App factory: pool lifespan, CORS, cache headers, error handlers."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import Settings
from .db import create_pool
from .routes import CountryNotFound, HsNotFound, router

log = logging.getLogger("northsource_api")

CACHE_PUBLIC = "public, max-age=86400"
NO_STORE_PATHS = {"/health", "/ready"}


def create_app(settings: Settings | None = None) -> FastAPI:
    logging.basicConfig(level=logging.INFO)
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.pool = create_pool(settings.database_url)
        app.state.pool.open()
        try:
            yield
        finally:
            app.state.pool.close()

    app = FastAPI(title="northsource API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware, allow_origins=settings.origins, allow_methods=["GET"], allow_headers=["*"]
    )
    app.include_router(router)

    @app.middleware("http")
    async def cache_control(request: Request, call_next):
        response = await call_next(request)
        cacheable = request.url.path not in NO_STORE_PATHS and response.status_code < 300
        response.headers["Cache-Control"] = CACHE_PUBLIC if cacheable else "no-store"
        return response

    @app.exception_handler(HsNotFound)
    async def hs_not_found(request: Request, exc: HsNotFound):
        return JSONResponse(
            status_code=404,
            content={"detail": "HS6 not found", "hs6": exc.hs6, "suggestions": exc.suggestions},
        )

    @app.exception_handler(CountryNotFound)
    async def country_not_found(request: Request, exc: CountryNotFound):
        return JSONResponse(
            status_code=404, content={"detail": "country not found", "iso": exc.iso}
        )

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception):
        log.exception("unhandled error on %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "internal error"},
            headers={"Cache-Control": "no-store"},
        )

    return app
