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
        monkeypatch.setenv("ENABLE_REBALANCE_TICKETS", "true")
    else:
        monkeypatch.delenv("ENABLE_REBALANCE_TICKETS", raising=False)
    get_settings.cache_clear()

    engine = create_engine(
        f"sqlite:///{tmp_path}/p_insight_rebalance_tickets_api_test.db",
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
    response = client.post("/api/portfolios", json={"name": "Rebalance Portfolio", "base_currency": "INR"})
    assert response.status_code == 201
    return response.json()


def create_holding(
    client: TestClient,
    portfolio_id: str,
    *,
    symbol: str,
    quantity: float,
    current_price: float | None,
) -> dict:
    response = client.post(
        f"/api/portfolios/{portfolio_id}/holdings",
        json={
            "symbol": symbol,
            "quantity": quantity,
            "average_cost": 100,
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
    create_holding(client, portfolio["id"], symbol="INFY", quantity=2, current_price=250)
    return portfolio


def test_rebalance_tickets_disabled_returns_feature_disabled(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=False) as client:
        response = client.post(
            "/api/portfolios/portfolio-1/rebalance/tickets",
            json={"target_weights": {"RELIANCE": 100}},
        )

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "feature_disabled"
    assert body["error"]["details"] == {"feature": "ENABLE_REBALANCE_TICKETS"}


def test_buy_sell_hold_output(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        portfolio = seed_portfolio(client)

        response = client.post(
            f"/api/portfolios/{portfolio['id']}/rebalance/tickets",
            json={"target_weights": {"RELIANCE": 50, "TCS": 40, "INFY": 10}},
        )

    assert response.status_code == 200
    body = response.json()
    tickets = {ticket["symbol"]: ticket for ticket in body["tickets"]}
    assert body["current_portfolio_value"] == 2500
    assert body["target_portfolio_value"] == 2500
    assert tickets["RELIANCE"]["current_weight"] == 0.4
    assert tickets["RELIANCE"]["target_weight"] == 0.5
    assert tickets["RELIANCE"]["action"] == "buy"
    assert tickets["RELIANCE"]["estimated_shares_to_trade"] == 2.5
    assert tickets["RELIANCE"]["estimated_cash_needed"] == 250
    assert tickets["TCS"]["action"] == "hold"
    assert tickets["TCS"]["estimated_shares_to_trade"] == 0
    assert tickets["INFY"]["action"] == "sell"
    assert tickets["INFY"]["estimated_shares_to_trade"] == 1
    assert tickets["INFY"]["estimated_cash_generated"] == 250
    assert body["leftover_cash"] == 0
    assert any("No trades were executed" in warning for warning in body["warnings"])


def test_missing_price_warns_and_skips_symbol(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        portfolio = create_portfolio(client)
        create_holding(client, portfolio["id"], symbol="RELIANCE", quantity=10, current_price=100)
        create_holding(client, portfolio["id"], symbol="TCS", quantity=5, current_price=None)

        response = client.post(
            f"/api/portfolios/{portfolio['id']}/rebalance/tickets",
            json={"target_weights": {"RELIANCE": 50, "TCS": 50}},
        )

    assert response.status_code == 200
    body = response.json()
    assert [ticket["symbol"] for ticket in body["tickets"]] == ["RELIANCE"]
    assert any("Current price is missing for TCS" in warning for warning in body["warnings"])


def test_cash_contribution_increases_target_value(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        portfolio = seed_portfolio(client)

        response = client.post(
            f"/api/portfolios/{portfolio['id']}/rebalance/tickets",
            json={"target_weights": {"RELIANCE": 40, "TCS": 40, "INFY": 20}, "cash_contribution": 500},
        )

    assert response.status_code == 200
    body = response.json()
    tickets = {ticket["symbol"]: ticket for ticket in body["tickets"]}
    assert body["target_portfolio_value"] == 3000
    assert tickets["RELIANCE"]["target_value"] == 1200
    assert tickets["RELIANCE"]["action"] == "buy"
    assert tickets["RELIANCE"]["estimated_cash_needed"] == 200
    assert tickets["TCS"]["target_value"] == 1200
    assert tickets["TCS"]["estimated_cash_needed"] == 200
    assert tickets["INFY"]["target_value"] == 600
    assert tickets["INFY"]["estimated_cash_needed"] == 100
    assert body["estimated_cash_needed"] == 500
    assert body["leftover_cash"] == 0


def test_weights_validation(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        portfolio = seed_portfolio(client)

        response = client.post(
            f"/api/portfolios/{portfolio['id']}/rebalance/tickets",
            json={"target_weights": {"RELIANCE": 60, "TCS": 20}},
        )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["message"] == "Target weights must sum to 100"
