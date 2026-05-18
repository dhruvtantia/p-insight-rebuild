from app.db.base import Base
from app.db import models  # noqa: F401


def test_initial_models_are_registered() -> None:
    expected_tables = {
        "users",
        "portfolios",
        "holdings",
        "assets",
        "asset_prices",
        "portfolio_snapshots",
        "analytics_results",
        "ai_conversations",
        "ai_messages",
        "upload_jobs",
        "upload_rows",
        "subscriptions",
        "feature_usage",
        "watchlist_items",
        "broker_connections",
        "broker_accounts",
    }

    assert expected_tables.issubset(Base.metadata.tables.keys())
