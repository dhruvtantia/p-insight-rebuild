from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.models import AnalyticsResult
from app.db.session import get_db
from app.main import create_app


@pytest.fixture()
def client(tmp_path) -> Generator[TestClient, None, None]:
    engine = create_engine(
        f"sqlite:///{tmp_path}/p_insight_analytics_test.db",
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


def create_portfolio(client: TestClient, base_currency: str = "USD") -> dict:
    response = client.post(
        "/api/portfolios",
        json={"name": "Analytics Portfolio", "base_currency": base_currency},
    )
    assert response.status_code == 201
    return response.json()


def create_holding(
    client: TestClient,
    portfolio_id: str,
    *,
    symbol: str,
    quantity: float,
    average_cost: float | None,
    current_price: float | None,
    currency: str = "USD",
    sector: str | None = "Technology",
    asset_class: str | None = "Equity",
) -> dict:
    response = client.post(
        f"/api/portfolios/{portfolio_id}/holdings",
        json={
            "symbol": symbol,
            "quantity": quantity,
            "average_cost": average_cost,
            "current_price": current_price,
            "currency": currency,
            "sector": sector,
            "asset_class": asset_class,
        },
    )
    assert response.status_code == 201
    return response.json()


def seed_priced_portfolio(client: TestClient) -> dict:
    portfolio = create_portfolio(client)
    create_holding(
        client,
        portfolio["id"],
        symbol="AAPL",
        quantity=10,
        average_cost=100,
        current_price=200,
        sector="Technology",
        asset_class="Equity",
    )
    create_holding(
        client,
        portfolio["id"],
        symbol="VOO",
        quantity=5,
        average_cost=300,
        current_price=400,
        sector="ETF",
        asset_class="Fund",
    )
    return portfolio


def test_portfolio_value(client: TestClient) -> None:
    portfolio = seed_priced_portfolio(client)

    response = client.get(f"/api/portfolios/{portfolio['id']}/analytics/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["total_portfolio_value"] == 4000
    assert body["total_cost_basis"] == 2500
    assert body["total_unrealized_gain_loss"] == 1500
    assert body["total_unrealized_gain_loss_pct"] == 0.6


def test_weights_sum_to_approximately_one(client: TestClient) -> None:
    portfolio = seed_priced_portfolio(client)

    response = client.get(f"/api/portfolios/{portfolio['id']}/analytics/summary")

    assert response.status_code == 200
    weights = [holding["weight"] for holding in response.json()["holdings"]]
    assert sum(weights) == pytest.approx(1.0)


def test_sector_allocation(client: TestClient) -> None:
    portfolio = seed_priced_portfolio(client)

    response = client.get(f"/api/portfolios/{portfolio['id']}/analytics/allocation")

    assert response.status_code == 200
    sector_weights = {bucket["name"]: bucket["weight"] for bucket in response.json()["sector_allocation"]}
    assert sector_weights == {"ETF": 0.5, "Technology": 0.5}


def test_asset_allocation(client: TestClient) -> None:
    portfolio = seed_priced_portfolio(client)

    response = client.get(f"/api/portfolios/{portfolio['id']}/analytics/allocation")

    assert response.status_code == 200
    asset_weights = {bucket["name"]: bucket["weight"] for bucket in response.json()["asset_allocation"]}
    assert asset_weights == {"Equity": 0.5, "Fund": 0.5}


def test_concentration_risk(client: TestClient) -> None:
    portfolio = create_portfolio(client)
    create_holding(
        client,
        portfolio["id"],
        symbol="AAPL",
        quantity=10,
        average_cost=100,
        current_price=300,
    )
    create_holding(
        client,
        portfolio["id"],
        symbol="MSFT",
        quantity=1,
        average_cost=100,
        current_price=100,
    )

    response = client.get(f"/api/portfolios/{portfolio['id']}/analytics/risk")

    assert response.status_code == 200
    concentration = response.json()["concentration"]
    assert concentration["status"] == "high"
    assert concentration["largest_holding"]["symbol"] == "AAPL"
    assert concentration["largest_holding"]["weight"] == pytest.approx(0.967742)
    assert response.json()["volatility"]["status"] == "insufficient_history"


def test_missing_price_rule(client: TestClient) -> None:
    portfolio = create_portfolio(client)
    create_holding(
        client,
        portfolio["id"],
        symbol="AAPL",
        quantity=10,
        average_cost=100,
        current_price=None,
    )

    response = client.get(f"/api/portfolios/{portfolio['id']}/analytics/rules")

    assert response.status_code == 200
    rules = {rule["rule_id"]: rule for rule in response.json()}
    assert rules["MISSING_PRICE_DATA"]["severity"] == "medium"
    assert rules["MISSING_PRICE_DATA"]["affected_symbols"] == ["AAPL"]


def test_missing_cost_basis_rule(client: TestClient) -> None:
    portfolio = create_portfolio(client)
    create_holding(
        client,
        portfolio["id"],
        symbol="MSFT",
        quantity=5,
        average_cost=None,
        current_price=200,
    )

    response = client.get(f"/api/portfolios/{portfolio['id']}/analytics/rules")

    assert response.status_code == 200
    rules = {rule["rule_id"]: rule for rule in response.json()}
    assert rules["MISSING_COST_BASIS"]["severity"] == "low"
    assert rules["MISSING_COST_BASIS"]["affected_symbols"] == ["MSFT"]


def test_empty_portfolio_analytics_does_not_crash(client: TestClient) -> None:
    portfolio = create_portfolio(client)

    summary_response = client.get(f"/api/portfolios/{portfolio['id']}/analytics/summary")
    risk_response = client.get(f"/api/portfolios/{portfolio['id']}/analytics/risk")
    rules_response = client.get(f"/api/portfolios/{portfolio['id']}/analytics/rules")

    assert summary_response.status_code == 200
    assert summary_response.json()["total_portfolio_value"] == 0
    assert summary_response.json()["holdings"] == []
    assert risk_response.status_code == 200
    assert risk_response.json()["concentration"]["status"] == "empty"
    assert rules_response.status_code == 200
    assert rules_response.json() == []


def test_recalculate_stores_analytics_results(client: TestClient) -> None:
    portfolio = seed_priced_portfolio(client)

    response = client.post(f"/api/portfolios/{portfolio['id']}/analytics/recalculate")

    assert response.status_code == 200
    body = response.json()
    assert body["analytics"]["summary"]["total_portfolio_value"] == 4000
    assert {result["result_type"] for result in body["stored_results"]} == {
        "summary",
        "allocation",
        "risk",
        "performance",
        "rules",
        "analytics_bundle",
    }

    SessionLocal = client.app.state.testing_session_local
    with SessionLocal() as db:
        stored_results = db.scalars(
            select(AnalyticsResult).where(AnalyticsResult.portfolio_id == portfolio["id"])
        ).all()
        assert len(stored_results) == 6
