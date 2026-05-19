from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.models import BrokerConnection
from app.db.session import get_db
from app.main import create_app


@pytest.fixture()
def client(tmp_path) -> Generator[TestClient, None, None]:
    engine = create_engine(
        f"sqlite:///{tmp_path}/p_insight_supporting_mvp_test.db",
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


def test_watchlist_crud(client: TestClient) -> None:
    create_response = client.post(
        "/api/watchlist",
        json={"symbol": "aapl", "name": "Apple Inc.", "notes": "Track earnings"},
    )

    assert create_response.status_code == 201
    item = create_response.json()
    assert item["symbol"] == "AAPL"
    assert item["name"] == "Apple Inc."
    assert item["notes"] == "Track earnings"
    assert item["current_price"] is None

    list_response = client.get("/api/watchlist")
    assert list_response.status_code == 200
    assert [row["symbol"] for row in list_response.json()] == ["AAPL"]

    delete_response = client.delete(f"/api/watchlist/{item['id']}")
    assert delete_response.status_code == 204
    assert client.get("/api/watchlist").json() == []


def test_watchlist_rejects_duplicate_symbol(client: TestClient) -> None:
    first_response = client.post("/api/watchlist", json={"symbol": "MSFT"})
    second_response = client.post("/api/watchlist", json={"symbol": "msft"})

    assert first_response.status_code == 201
    assert second_response.status_code == 422
    assert second_response.json()["error"]["code"] == "validation_error"


def test_broker_placeholder_endpoints(client: TestClient) -> None:
    providers_response = client.get("/api/broker-connections/providers")
    create_response = client.post("/api/broker-connections/connect-placeholder", json={"provider": "Plaid"})

    assert providers_response.status_code == 200
    assert {provider["provider"] for provider in providers_response.json()} == {"plaid", "zerodha", "ibkr", "alpaca"}
    assert create_response.status_code == 201
    connection = create_response.json()
    assert connection["provider"] == "Plaid"
    assert connection["status"] == "waitlist_interest"
    assert "coming soon" in connection["message"].lower()

    list_response = client.get("/api/broker-connections")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    delete_response = client.delete(f"/api/broker-connections/{connection['id']}")
    assert delete_response.status_code == 204
    assert client.get("/api/broker-connections").json() == []


def test_broker_connection_handles_invalid_metadata_json(client: TestClient) -> None:
    create_response = client.post("/api/broker-connections/connect-placeholder", json={"provider": "Plaid"})
    assert create_response.status_code == 201
    connection_id = create_response.json()["id"]

    SessionLocal = client.app.state.testing_session_local
    with SessionLocal() as db:
        connection = db.get(BrokerConnection, connection_id)
        assert connection is not None
        connection.metadata_json = "{not-json"
        db.add(connection)
        db.commit()

    list_response = client.get("/api/broker-connections")

    assert list_response.status_code == 200
    connection = list_response.json()[0]
    assert connection["id"] == connection_id
    assert connection["metadata"] == {}
    assert connection["message"] == "Broker sync is coming soon."


def test_billing_placeholder_endpoints(client: TestClient) -> None:
    plan_response = client.get("/api/billing/plan")
    checkout_response = client.post("/api/billing/create-checkout-session")
    webhook_response = client.post("/api/billing/webhook")

    assert plan_response.status_code == 200
    plan = plan_response.json()
    assert plan["current_plan"] == "free"
    assert {option["id"] for option in plan["plans"]} == {"free", "pro", "premium_later"}
    assert plan["usage"]["enforcement_enabled"] is False

    assert checkout_response.status_code == 200
    assert checkout_response.json()["status"] == "coming_soon"
    assert checkout_response.json()["checkout_url"] is None

    assert webhook_response.status_code == 200
    assert webhook_response.json()["received"] is True


def test_demo_seed_endpoint_creates_portfolio_holdings_and_prices(client: TestClient) -> None:
    response = client.post("/api/demo/seed")

    assert response.status_code == 200
    body = response.json()
    assert body["portfolio_name"] == "Demo Growth Portfolio"
    assert body["holdings_count"] == 5
    assert body["symbols"] == ["AAPL", "MSFT", "NVDA", "SPY", "TSLA"]

    portfolios_response = client.get("/api/portfolios")
    assert portfolios_response.status_code == 200
    portfolio = portfolios_response.json()[0]
    assert portfolio["name"] == "Demo Growth Portfolio"

    holdings_response = client.get(f"/api/portfolios/{portfolio['id']}/holdings")
    assert holdings_response.status_code == 200
    holdings = holdings_response.json()
    assert {holding["symbol"] for holding in holdings} == {"AAPL", "MSFT", "NVDA", "SPY", "TSLA"}
    assert all(holding["current_price"] is not None for holding in holdings)
