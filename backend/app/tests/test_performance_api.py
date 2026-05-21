from collections.abc import Generator
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.models import Portfolio, User
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
        monkeypatch.setenv("ENABLE_PERFORMANCE_HISTORY", "true")
    else:
        monkeypatch.delenv("ENABLE_PERFORMANCE_HISTORY", raising=False)
    get_settings.cache_clear()

    engine = create_engine(
        f"sqlite:///{tmp_path}/p_insight_performance_api_test.db",
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
    app.state.testing_session_local = TestingSessionLocal

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def create_portfolio(client: TestClient) -> dict:
    response = client.post(
        "/api/portfolios",
        json={"name": "Performance API Portfolio", "base_currency": "INR"},
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


def test_performance_history_disabled_returns_feature_disabled(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=False) as client:
        response = client.get("/api/portfolios/portfolio-1/performance/history?period=1Y")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "feature_disabled"
    assert body["error"]["details"] == {"feature": "ENABLE_PERFORMANCE_HISTORY"}


def test_performance_history_valid_portfolio_returns_synthetic_series(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        portfolio = create_portfolio(client)
        create_holding(client, portfolio["id"])

        response = client.get(f"/api/portfolios/{portfolio['id']}/performance/history?period=1M")

    assert response.status_code == 200
    body = response.json()
    assert body["portfolio_id"] == portfolio["id"]
    assert body["period"] == "1M"
    assert body["benchmark_symbol"] == "NIFTY50"
    assert body["portfolio_value_series"]
    assert body["portfolio_normalized_return_series"]
    assert body["benchmark_normalized_return_series"]
    assert body["portfolio_normalized_return_series"][0]["normalized_return"] == 0
    assert body["benchmark_normalized_return_series"][0]["normalized_return"] == 0
    assert body["missing_price_symbols"] == []
    assert body["assumptions"] == {
        "method": "synthetic_current_holdings",
        "assumes_current_quantities_held_throughout": True,
        "not_transaction_aware": True,
        "not_xirr": True,
        "not_time_weighted_return": True,
    }
    assert body["data_status"]["provider"] == "mock_historical_prices"


def test_performance_history_empty_portfolio_returns_clear_empty_state(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        portfolio = create_portfolio(client)

        response = client.get(f"/api/portfolios/{portfolio['id']}/performance/history?period=1Y")

    assert response.status_code == 200
    body = response.json()
    assert body["portfolio_id"] == portfolio["id"]
    assert body["portfolio_value_series"] == []
    assert body["portfolio_normalized_return_series"] == []
    assert body["benchmark_normalized_return_series"] == []
    assert body["missing_price_symbols"] == []
    assert body["data_status"]["source"] == "unavailable"
    assert "No holdings" in body["data_status"]["warning"]
    assert body["assumptions"]["method"] == "synthetic_current_holdings"


def test_performance_history_rejects_portfolio_owned_by_another_user(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        SessionLocal = client.app.state.testing_session_local
        with SessionLocal() as db:
            other_user = User(email="other-performance@example.com", display_name="Other User")
            db.add(other_user)
            db.flush()
            portfolio = Portfolio(
                user_id=other_user.id,
                name="Other Performance Portfolio",
                base_currency="INR",
                benchmark_symbol="NIFTY50",
            )
            db.add(portfolio)
            db.commit()
            portfolio_id = portfolio.id

        response = client.get(f"/api/portfolios/{portfolio_id}/performance/history?period=1Y")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
