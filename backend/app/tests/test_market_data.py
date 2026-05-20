from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.models import AssetPrice, Holding
from app.db.session import get_db
from app.main import create_app
from app.modules.market_data.providers.mock_provider import (
    MockProvider,
    MockProviderIndia,
    normalize_india_symbol_for_provider,
)


@pytest.fixture()
def client(tmp_path) -> Generator[TestClient, None, None]:
    engine = create_engine(
        f"sqlite:///{tmp_path}/p_insight_market_data_test.db",
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
        json={"name": "Market Data Portfolio", "base_currency": "INR"},
    )
    assert response.status_code == 201
    return response.json()


def create_holding(client: TestClient, portfolio_id: str, symbol: str, current_price: float | None = None) -> dict:
    response = client.post(
        f"/api/portfolios/{portfolio_id}/holdings",
        json={
            "symbol": symbol,
            "quantity": 5,
            "average_cost": 100,
            "current_price": current_price,
            "currency": "INR",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_mock_provider_latest_price() -> None:
    quote = MockProvider().get_latest_price("aapl")

    assert quote.symbol == "AAPL"
    assert quote.price == 210.12
    assert quote.source == "mock"
    assert quote.is_realtime is False
    assert quote.as_of.isoformat() == "2026-01-01T00:00:00+00:00"


def test_mock_provider_batch_prices() -> None:
    quotes = MockProvider().get_batch_prices(["AAPL", "msft", "AAPL"])

    assert [quote.symbol for quote in quotes] == ["AAPL", "MSFT"]
    assert [quote.price for quote in quotes] == [210.12, 425.44]


def test_mock_india_provider_returns_inr_mock_prices() -> None:
    provider = MockProviderIndia()

    reliance = provider.get_latest_price("reliance")
    nifty = provider.get_latest_price("NIFTY50")

    assert reliance.symbol == "RELIANCE"
    assert reliance.price == 2842.15
    assert reliance.currency == "INR"
    assert reliance.source == "mock_india"
    assert reliance.is_realtime is False
    assert nifty.symbol == "NIFTY50"
    assert nifty.price == 22530.7
    assert nifty.currency == "INR"
    assert nifty.source == "mock_india"

    banknifty = provider.get_latest_price("BANK NIFTY")
    assert banknifty.symbol == "BANKNIFTY"
    assert banknifty.currency == "INR"
    assert banknifty.source == "mock_india"


def test_india_symbol_normalization_for_future_providers() -> None:
    assert normalize_india_symbol_for_provider("RELIANCE") == "RELIANCE.NS"
    assert normalize_india_symbol_for_provider("tcs") == "TCS.NS"
    assert normalize_india_symbol_for_provider("NIFTY50") == "^NSEI"
    assert normalize_india_symbol_for_provider("INFY.NS") == "INFY.NS"
    assert normalize_india_symbol_for_provider("BANK NIFTY") == "^NSEBANK"


def test_unknown_symbol_deterministic_price() -> None:
    provider = MockProvider()

    first_quote = provider.get_latest_price("XYZ123")
    second_quote = provider.get_latest_price("xyz123")

    assert first_quote.symbol == "XYZ123"
    assert first_quote.price == second_quote.price
    assert first_quote.price > 0


def test_price_api_endpoint_caches_asset_price(client: TestClient) -> None:
    response = client.get("/api/market-data/prices?symbols=RELIANCE,TCS")

    assert response.status_code == 200
    body = response.json()
    assert [price["symbol"] for price in body["prices"]] == ["RELIANCE", "TCS"]
    assert body["prices"][0]["source"] == "mock_india"
    assert body["prices"][0]["currency"] == "INR"
    assert body["prices"][0]["is_realtime"] is False

    SessionLocal = client.app.state.testing_session_local
    with SessionLocal() as db:
        stored_prices = db.scalars(select(AssetPrice).order_by(AssetPrice.symbol)).all()
        assert [price.symbol for price in stored_prices] == ["RELIANCE", "TCS"]


def test_portfolio_price_refresh_updates_holdings(client: TestClient) -> None:
    portfolio = create_portfolio(client)
    reliance_holding = create_holding(client, portfolio["id"], "RELIANCE", current_price=1)
    tcs_holding = create_holding(client, portfolio["id"], "TCS", current_price=2)

    response = client.post(f"/api/portfolios/{portfolio['id']}/prices/refresh")

    assert response.status_code == 200
    body = response.json()
    assert body["portfolio_id"] == portfolio["id"]
    assert body["refreshed_count"] == 2
    assert {price["symbol"]: price["price"] for price in body["prices"]} == {
        "RELIANCE": 2842.15,
        "TCS": 3925.8,
    }
    assert {holding["symbol"]: holding["current_price"] for holding in body["holdings"]} == {
        "RELIANCE": 2842.15,
        "TCS": 3925.8,
    }

    SessionLocal = client.app.state.testing_session_local
    with SessionLocal() as db:
        holdings = db.scalars(select(Holding).order_by(Holding.symbol)).all()
        assert {holding.id for holding in holdings} == {reliance_holding["id"], tcs_holding["id"]}
        assert {holding.symbol: float(holding.current_price) for holding in holdings} == {
            "RELIANCE": 2842.15,
            "TCS": 3925.8,
        }
        stored_prices = db.scalars(select(AssetPrice).order_by(AssetPrice.symbol)).all()
        assert [price.symbol for price in stored_prices] == ["RELIANCE", "TCS"]
