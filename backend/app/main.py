from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.accounts.router import router as accounts_router
from app.auth.router import router as auth_router
from app.auth.router import users_router
from app.categories.router import router as categories_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import CorrelationIdMiddleware
from app.documents.router import router as documents_router
from app.metrics.router import router as analysis_router
from app.transactions.router import router as transactions_router
from app.rules.router import router as rules_router


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Correlation-ID"],
    )
    register_exception_handlers(app)

    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(accounts_router)
    app.include_router(categories_router)
    app.include_router(transactions_router)
    app.include_router(analysis_router)
    app.include_router(documents_router)
    app.include_router(rules_router)

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
