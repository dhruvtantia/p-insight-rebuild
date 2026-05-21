from collections.abc import Generator
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@contextmanager
def create_test_client(tmp_path, monkeypatch, *, enabled: bool) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "mock_india")
    monkeypatch.setenv("INDIAN_MARKET_DATA_PROVIDER", "mock_india")
    if enabled:
        monkeypatch.setenv("ENABLE_RISK_V2", "true")
    else:
        monkeypatch.delenv("ENABLE_RISK_V2", raising=False)
    get_settings.cache_clear()

    engine = create_engine(
        f"sqlite:///{tmp_path}/p_insight_risk_v2_api_test.db",
        connect_args={"check_same_thread": False},
        future=True,
    )
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def create_portfolio(client: TestClient) -> dict:
    response = client.post(
        "/api/portfolios",
        json={"name": "Risk V2 Portfolio", "base_currency": "INR"},
    )
    assert response.status_code == 201
    return response.json()


def create_holding(client: TestClient, portfolio_id: str) -> dict:
    response = client.post(
        f"/api/portfolios/{portfolio_id}/holdings",
        json={
            "symbol": "RELIANCE",
            "quantity": 10,
            "average_cost": 2500,
            "current_price": 2842.15,
            "currency": "INR",
            "sector": "Energy",
            "asset_class": "Equity",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_risk_v2_disabled_returns_feature_disabled(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=False) as client:
        response = client.get("/api/portfolios/portfolio-1/risk?period=1Y")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "feature_disabled"
    assert body["error"]["details"] == {"feature": "ENABLE_RISK_V2"}


def test_risk_v2_empty_portfolio_reports_insufficient_history(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        portfolio = create_portfolio(client)

        response = client.get(f"/api/portfolios/{portfolio['id']}/risk?period=1Y")

    assert response.status_code == 200
    body = response.json()
    assert body["portfolio_id"] == portfolio["id"]
    assert body["observations"] == 0
    assert body["annualized_return"] is None
    assert body["annualized_volatility"] is None
    assert body["correlation_matrix"] is None
    assert body["data_status"]["source"] == "unavailable"
    assert body["metric_status"]["annualized_return"]["status"] == "insufficient_history"
    assert body["metric_status"]["beta_vs_benchmark"]["status"] == "insufficient_history"


def test_risk_v2_valid_mock_history_returns_metrics(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        portfolio = create_portfolio(client)
        create_holding(client, portfolio["id"])

        response = client.get(f"/api/portfolios/{portfolio['id']}/risk?period=1M")

    assert response.status_code == 200
    body = response.json()
    assert body["portfolio_id"] == portfolio["id"]
    assert body["period"] == "1M"
    assert body["benchmark_symbol"] == "NIFTY50"
    assert body["observations"] > 1
    assert body["annualized_return"] is not None
    assert body["annualized_volatility"] is not None
    assert body["sharpe_ratio"] is not None
    assert body["sortino_ratio"] is not None
    assert body["max_drawdown"] is not None
    assert body["downside_deviation"] is not None
    assert body["value_at_risk_95"] is not None
    assert body["beta_vs_benchmark"] is not None
    assert body["tracking_error"] is not None
    assert body["information_ratio"] is not None
    assert body["correlation_matrix"]["portfolio"]["portfolio"] == 1
    assert body["correlation_matrix"]["benchmark"]["benchmark"] == 1
    assert body["assumptions"]["method"] == "synthetic_current_holdings"
    assert body["data_status"]["provider"] == "mock_historical_prices"


def test_risk_v2_metric_status_fields_are_returned(tmp_path, monkeypatch) -> None:
    expected_metrics = {
        "annualized_return",
        "annualized_volatility",
        "sharpe_ratio",
        "sortino_ratio",
        "max_drawdown",
        "downside_deviation",
        "value_at_risk_95",
        "beta_vs_benchmark",
        "tracking_error",
        "information_ratio",
        "correlation_matrix",
    }

    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        portfolio = create_portfolio(client)
        create_holding(client, portfolio["id"])

        response = client.get(f"/api/portfolios/{portfolio['id']}/risk?period=1M")

    assert response.status_code == 200
    statuses = response.json()["metric_status"]
    assert set(statuses) == expected_metrics
    assert all("status" in status for status in statuses.values())
    assert all("message" in status for status in statuses.values())
    assert statuses["annualized_volatility"]["status"] == "ok"
