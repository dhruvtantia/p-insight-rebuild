from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.modules.ai_advisor.router import conversation_router as ai_conversation_router
from app.modules.ai_advisor.router import portfolio_router as ai_portfolio_router
from app.modules.analytics.router import router as analytics_router
from app.modules.billing.router import router as billing_router
from app.modules.broker_connections.router import router as broker_connections_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.demo.router import router as demo_router
from app.modules.holdings.router import router as holdings_router
from app.modules.health.router import router as health_router
from app.modules.market_data.router import router as market_data_router
from app.modules.market_overview.router import router as market_overview_router
from app.modules.performance.router import router as performance_router
from app.modules.portfolios.router import router as portfolios_router
from app.modules.uploads.router import router as uploads_router
from app.modules.watchlist.router import router as watchlist_router


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
    app.include_router(market_data_router)
    app.include_router(market_overview_router)
    app.include_router(performance_router)
    app.include_router(analytics_router)
    app.include_router(dashboard_router)
    app.include_router(ai_portfolio_router)
    app.include_router(ai_conversation_router)
    app.include_router(watchlist_router)
    app.include_router(broker_connections_router)
    app.include_router(billing_router)
    app.include_router(demo_router)
    app.include_router(uploads_router)
    return app


app = create_app()
