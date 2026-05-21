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
    if enabled:
        monkeypatch.setenv("ENABLE_OPTIMIZER", "true")
    else:
        monkeypatch.delenv("ENABLE_OPTIMIZER", raising=False)
    get_settings.cache_clear()

    engine = create_engine(
        f"sqlite:///{tmp_path}/p_insight_optimizer_api_test.db",
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
    response = client.post("/api/portfolios", json={"name": "Optimizer Portfolio", "base_currency": "INR"})
    assert response.status_code == 201
    return response.json()


def create_holding(
    client: TestClient,
    portfolio_id: str,
    *,
    symbol: str,
    quantity: float,
    current_price: float,
) -> dict:
    response = client.post(
        f"/api/portfolios/{portfolio_id}/holdings",
        json={
            "symbol": symbol,
            "quantity": quantity,
            "average_cost": current_price * 0.8,
            "current_price": current_price,
            "currency": "INR",
            "sector": "Equity",
            "asset_class": "Equity",
        },
    )
    assert response.status_code == 201
    return response.json()


def seed_portfolio(client: TestClient) -> dict:
    portfolio = create_portfolio(client)
    create_holding(client, portfolio["id"], symbol="RELIANCE", quantity=10, current_price=100)
    create_holding(client, portfolio["id"], symbol="TCS", quantity=5, current_price=200)
    return portfolio


def test_optimizer_disabled_returns_feature_disabled(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=False) as client:
        response = client.post("/api/portfolios/portfolio-1/optimize", json={"period": "1M"})

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "feature_disabled"
    assert body["error"]["details"] == {"feature": "ENABLE_OPTIMIZER"}


def test_optimizer_returns_insufficient_history_for_empty_portfolio(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        portfolio = create_portfolio(client)

        response = client.post(f"/api/portfolios/{portfolio['id']}/optimize", json={"period": "1M"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "insufficient_history"
    assert body["current_portfolio_metrics"] == {
        "expected_annual_return": None,
        "annualized_volatility": None,
        "sharpe_ratio": None,
    }
    assert body["min_variance_target_weights"]["target_weights"] == {}
    assert body["max_sharpe_target_weights"]["target_weights"] == {}
    assert body["efficient_frontier_points"] == []
    assert any("At least two holdings" in warning for warning in body["warnings"])


def test_optimizer_valid_mock_history_returns_targets_and_frontier(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        portfolio = seed_portfolio(client)

        response = client.post(
            f"/api/portfolios/{portfolio['id']}/optimize",
            json={"period": "1M", "frontier_points": 4},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["portfolio_id"] == portfolio["id"]
    assert body["period"] == "1M"
    assert body["status"] == "ok"
    assert body["data_status"]["provider"] == "mock_historical_prices"
    assert body["current_weights"] == {"RELIANCE": 0.5, "TCS": 0.5}
    assert body["current_portfolio_metrics"]["annualized_volatility"] is not None
    assert set(body["min_variance_target_weights"]["target_weights"]) == {"RELIANCE", "TCS"}
    assert sum(body["min_variance_target_weights"]["target_weights"].values()) == pytest.approx(1)
    assert set(body["max_sharpe_target_weights"]["target_weights"]) == {"RELIANCE", "TCS"}
    assert sum(body["max_sharpe_target_weights"]["target_weights"].values()) == pytest.approx(1)
    assert len(body["efficient_frontier_points"]) == 4
    assert body["efficient_frontier_points"][0]["weights"] == body["min_variance_target_weights"]["target_weights"]
    assert body["efficient_frontier_points"][-1]["weights"] == body["max_sharpe_target_weights"]["target_weights"]


def test_optimizer_assumptions_are_included(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        portfolio = seed_portfolio(client)

        response = client.post(f"/api/portfolios/{portfolio['id']}/optimize", json={"period": "1M"})

    assert response.status_code == 200
    assumptions = response.json()["assumptions"]
    assert assumptions == {
        "long_only": True,
        "no_taxes": True,
        "no_transaction_costs": True,
        "no_liquidity_constraints": True,
        "historical_estimates_only": True,
        "not_investment_advice": True,
    }
