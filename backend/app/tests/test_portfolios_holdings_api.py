from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.models import Portfolio, User
from app.db.session import get_db
from app.main import create_app


@pytest.fixture()
def client(tmp_path) -> Generator[TestClient, None, None]:
    engine = create_engine(
        f"sqlite:///{tmp_path}/p_insight_api_test.db",
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


def create_portfolio(client: TestClient, name: str = "Core Portfolio") -> dict:
    response = client.post(
        "/api/portfolios",
        json={
            "name": name,
            "base_currency": "USD",
            "benchmark_symbol": "VOO",
            "risk_free_rate": 0.04,
        },
    )
    assert response.status_code == 201
    return response.json()


def create_holding(client: TestClient, portfolio_id: str, symbol: str = "AAPL") -> dict:
    response = client.post(
        f"/api/portfolios/{portfolio_id}/holdings",
        json={
            "symbol": symbol,
            "company_name": "Apple Inc.",
            "quantity": 10,
            "average_cost": 100,
            "current_price": 125,
            "currency": "USD",
            "sector": "Technology",
            "asset_class": "equity",
            "exchange": "NASDAQ",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_create_portfolio(client: TestClient) -> None:
    portfolio = create_portfolio(client)

    assert portfolio["id"]
    assert portfolio["user_id"]
    assert portfolio["name"] == "Core Portfolio"
    assert portfolio["base_currency"] == "USD"
    assert portfolio["benchmark_symbol"] == "VOO"
    assert portfolio["risk_free_rate"] == 0.04
    assert portfolio["created_at"]
    assert portfolio["updated_at"]


def test_create_portfolio_defaults_to_inr_and_nifty50(client: TestClient) -> None:
    response = client.post("/api/portfolios", json={"name": "India Core"})

    assert response.status_code == 201
    portfolio = response.json()
    assert portfolio["base_currency"] == "INR"
    assert portfolio["benchmark_symbol"] == "NIFTY50"


def test_nifty50_benchmark_name_is_normalized(client: TestClient) -> None:
    response = client.post(
        "/api/portfolios",
        json={"name": "Benchmark Portfolio", "benchmark_symbol": "NIFTY 50"},
    )

    assert response.status_code == 201
    assert response.json()["benchmark_symbol"] == "NIFTY50"


def test_list_portfolios(client: TestClient) -> None:
    create_portfolio(client, name="Core Portfolio")
    create_portfolio(client, name="Satellite Portfolio")

    response = client.get("/api/portfolios")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_portfolio(client: TestClient) -> None:
    portfolio = create_portfolio(client)

    response = client.get(f"/api/portfolios/{portfolio['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == portfolio["id"]


def test_update_portfolio(client: TestClient) -> None:
    portfolio = create_portfolio(client)

    response = client.patch(
        f"/api/portfolios/{portfolio['id']}",
        json={"name": "Updated Portfolio", "benchmark_symbol": "SPY"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Portfolio"
    assert response.json()["benchmark_symbol"] == "SPY"


def test_delete_portfolio(client: TestClient) -> None:
    portfolio = create_portfolio(client)

    delete_response = client.delete(f"/api/portfolios/{portfolio['id']}")
    get_response = client.get(f"/api/portfolios/{portfolio['id']}")

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_create_holding(client: TestClient) -> None:
    portfolio = create_portfolio(client)

    holding = create_holding(client, portfolio["id"])

    assert holding["portfolio_id"] == portfolio["id"]
    assert holding["symbol"] == "AAPL"
    assert holding["quantity"] == 10
    assert holding["market_value"] == 1250
    assert holding["unrealized_gain_loss"] == 250


def test_create_indian_holding_normalizes_symbol_defaults(client: TestClient) -> None:
    portfolio_response = client.post("/api/portfolios", json={"name": "India Portfolio"})
    assert portfolio_response.status_code == 201
    portfolio = portfolio_response.json()

    response = client.post(
        f"/api/portfolios/{portfolio['id']}/holdings",
        json={"symbol": "NSE:reliance", "quantity": 10, "average_cost": 2800},
    )

    assert response.status_code == 201
    holding = response.json()
    assert holding["symbol"] == "RELIANCE"
    assert holding["currency"] == "INR"
    assert holding["exchange"] == "NSE"
    assert holding["asset_class"] == "Equity"


def test_list_holdings(client: TestClient) -> None:
    portfolio = create_portfolio(client)
    create_holding(client, portfolio["id"], symbol="AAPL")
    create_holding(client, portfolio["id"], symbol="MSFT")

    response = client.get(f"/api/portfolios/{portfolio['id']}/holdings")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_update_holding(client: TestClient) -> None:
    portfolio = create_portfolio(client)
    holding = create_holding(client, portfolio["id"])

    response = client.patch(
        f"/api/portfolios/{portfolio['id']}/holdings/{holding['id']}",
        json={"quantity": 4, "current_price": 150},
    )

    assert response.status_code == 200
    assert response.json()["quantity"] == 4
    assert response.json()["current_price"] == 150
    assert response.json()["market_value"] == 600
    assert response.json()["unrealized_gain_loss"] == 200


def test_delete_holding(client: TestClient) -> None:
    portfolio = create_portfolio(client)
    holding = create_holding(client, portfolio["id"])

    delete_response = client.delete(f"/api/portfolios/{portfolio['id']}/holdings/{holding['id']}")
    list_response = client.get(f"/api/portfolios/{portfolio['id']}/holdings")

    assert delete_response.status_code == 204
    assert list_response.status_code == 200
    assert list_response.json() == []


def test_invalid_quantity_rejected(client: TestClient) -> None:
    portfolio = create_portfolio(client)

    response = client.post(
        f"/api/portfolios/{portfolio['id']}/holdings",
        json={"symbol": "AAPL", "quantity": 0},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "request_validation_error"


def test_invalid_portfolio_access_rejected(client: TestClient) -> None:
    app = client.app
    SessionLocal = app.state.testing_session_local
    with SessionLocal() as db:
        other_user = User(email="other@p-insight.local", display_name="Other User")
        db.add(other_user)
        db.commit()
        db.refresh(other_user)
        other_portfolio = Portfolio(user_id=other_user.id, name="Other Portfolio", base_currency="USD")
        db.add(other_portfolio)
        db.commit()
        db.refresh(other_portfolio)
        other_portfolio_id = other_portfolio.id

    response = client.get(f"/api/portfolios/{other_portfolio_id}")
    holdings_response = client.get(f"/api/portfolios/{other_portfolio_id}/holdings")

    assert response.status_code == 404
    assert holdings_response.status_code == 404
