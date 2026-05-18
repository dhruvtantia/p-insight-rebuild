from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.modules.holdings.router import router as holdings_router
from app.modules.health.router import router as health_router
from app.modules.portfolios.router import router as portfolios_router
from app.modules.uploads.router import router as uploads_router


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()

    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(portfolios_router)
    app.include_router(holdings_router)
    app.include_router(uploads_router)
    return app


app = create_app()
