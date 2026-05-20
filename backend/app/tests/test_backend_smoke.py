from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app


@pytest.fixture()
def client(tmp_path, monkeypatch) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "mock_india")
    monkeypatch.setenv("INDIAN_MARKET_DATA_PROVIDER", "mock_india")
    get_settings.cache_clear()

    engine = create_engine(
        f"sqlite:///{tmp_path}/p_insight_backend_smoke_test.db",
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
    get_settings.cache_clear()


def test_backend_smoke_flow(client: TestClient) -> None:
    health_response = client.get("/api/health")
    status_response = client.get("/api/status")

    assert health_response.status_code == 200
    assert health_response.json()["status"] == "ok"
    assert status_response.status_code == 200
    status_body = status_response.json()
    assert status_body["market_data_provider"] == "mock_india"
    assert status_body["market_data_is_mock"] is True
    assert status_body["ai_provider_mode"] == "mock"
    assert status_body["ai_is_mock"] is True
    assert "warnings" in status_body

    create_portfolio_response = client.post(
        "/api/portfolios",
        json={"name": "Smoke Portfolio", "base_currency": "INR", "benchmark_symbol": "NIFTY50"},
    )
    assert create_portfolio_response.status_code == 201
    portfolio = create_portfolio_response.json()
    assert portfolio["id"]
    assert portfolio["name"] == "Smoke Portfolio"

    list_portfolios_response = client.get("/api/portfolios")
    assert list_portfolios_response.status_code == 200
    assert [row["id"] for row in list_portfolios_response.json()] == [portfolio["id"]]

    create_holding_response = client.post(
        f"/api/portfolios/{portfolio['id']}/holdings",
        json={
            "symbol": "RELIANCE",
            "company_name": "Reliance Industries Ltd.",
            "quantity": 2,
            "average_cost": 2500,
            "current_price": 2600,
            "currency": "INR",
            "sector": "Energy",
            "asset_class": "Equity",
            "exchange": "NSE",
        },
    )
    assert create_holding_response.status_code == 201
    holding = create_holding_response.json()
    assert holding["symbol"] == "RELIANCE"

    edit_holding_response = client.patch(
        f"/api/portfolios/{portfolio['id']}/holdings/{holding['id']}",
        json={"quantity": 3, "current_price": 2700},
    )
    assert edit_holding_response.status_code == 200
    assert edit_holding_response.json()["quantity"] == 3
    assert edit_holding_response.json()["current_price"] == 2700

    list_holdings_response = client.get(f"/api/portfolios/{portfolio['id']}/holdings")
    assert list_holdings_response.status_code == 200
    assert len(list_holdings_response.json()) == 1

    upload_response = client.post(
        f"/api/portfolios/{portfolio['id']}/uploads",
        files={
            "file": (
                "smoke-holdings.csv",
                (
                    "Ticker,Name,Shares,Average Cost,Market Value,Currency,Sector,Asset Class,Exchange\n"
                    "TCS,Tata Consultancy Services Ltd,1,3800,3925.8,INR,Information Technology,Equity,NSE\n"
                ).encode("utf-8"),
                "text/csv",
            )
        },
    )
    assert upload_response.status_code == 201
    upload = upload_response.json()
    assert upload["status"] == "uploaded"
    assert upload["total_rows"] == 1

    mapping_response = client.post(
        f"/api/uploads/{upload['id']}/column-mapping",
        json={
            "mapping": {
                "symbol": "Ticker",
                "company_name": "Name",
                "quantity": "Shares",
                "average_cost": "Average Cost",
                "market_value": "Market Value",
                "currency": "Currency",
                "sector": "Sector",
                "asset_class": "Asset Class",
                "exchange": "Exchange",
            }
        },
    )
    assert mapping_response.status_code == 200
    assert mapping_response.json()["mapping"]["symbol"] == "Ticker"

    validation_response = client.post(f"/api/uploads/{upload['id']}/validate")
    assert validation_response.status_code == 200
    validation = validation_response.json()
    assert validation["upload_job"]["valid_rows"] == 1
    assert validation["upload_job"]["invalid_rows"] == 0
    assert validation["rows"][0]["status"] == "valid"

    confirm_response = client.post(f"/api/uploads/{upload['id']}/confirm")
    assert confirm_response.status_code == 200
    confirm = confirm_response.json()
    assert confirm["status"] == "imported"
    assert confirm["imported_count"] == 1

    imported_holdings_response = client.get(f"/api/portfolios/{portfolio['id']}/holdings")
    assert imported_holdings_response.status_code == 200
    assert sorted(row["symbol"] for row in imported_holdings_response.json()) == ["RELIANCE", "TCS"]

    refresh_response = client.post(f"/api/portfolios/{portfolio['id']}/prices/refresh")
    assert refresh_response.status_code == 200
    refresh = refresh_response.json()
    assert refresh["refreshed_count"] == 2
    assert {price["source"] for price in refresh["prices"]} == {"mock_india"}

    summary_response = client.get(f"/api/portfolios/{portfolio['id']}/analytics/summary")
    allocation_response = client.get(f"/api/portfolios/{portfolio['id']}/analytics/allocation")
    risk_response = client.get(f"/api/portfolios/{portfolio['id']}/analytics/risk")
    performance_response = client.get(f"/api/portfolios/{portfolio['id']}/analytics/performance")
    rules_response = client.get(f"/api/portfolios/{portfolio['id']}/analytics/rules")

    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert {
        "portfolio_id",
        "base_currency",
        "holdings",
        "total_portfolio_value",
        "total_cost_basis",
        "total_unrealized_gain_loss",
        "largest_holding",
    }.issubset(summary)
    assert len(summary["holdings"]) == 2

    assert allocation_response.status_code == 200
    assert {"asset_allocation", "sector_allocation", "currency_exposure"}.issubset(allocation_response.json())
    assert risk_response.status_code == 200
    assert {"volatility", "sharpe_ratio", "max_drawdown", "concentration"}.issubset(risk_response.json())
    assert performance_response.status_code == 200
    assert {"total_cost_basis", "total_unrealized_gain_loss", "top_gainers", "top_losers"}.issubset(
        performance_response.json()
    )
    assert rules_response.status_code == 200
    assert isinstance(rules_response.json(), list)

    ai_response = client.post(
        f"/api/portfolios/{portfolio['id']}/ai/question",
        json={"question": "What risk should I review first?"},
    )
    assert ai_response.status_code == 200
    ai = ai_response.json()
    assert {"conversation_id", "mode", "provider", "model", "response", "context", "created_at"}.issubset(ai)
    assert ai["mode"] == "question"
    assert ai["provider"] == "mock"
    assert "What risk should I review first?" in ai["response"]
