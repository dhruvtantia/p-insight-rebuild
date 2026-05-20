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
        monkeypatch.setenv("ENABLE_DASHBOARD_BUNDLE", "true")
    else:
        monkeypatch.delenv("ENABLE_DASHBOARD_BUNDLE", raising=False)
    get_settings.cache_clear()

    engine = create_engine(
        f"sqlite:///{tmp_path}/p_insight_dashboard_api_test.db",
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
        json={"name": "Dashboard API Portfolio", "base_currency": "INR"},
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


def test_dashboard_bundle_disabled_returns_feature_disabled(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=False) as client:
        response = client.get("/api/portfolios/portfolio-1/dashboard")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "feature_disabled"
    assert body["error"]["details"] == {"feature": "ENABLE_DASHBOARD_BUNDLE"}
    assert "disabled" in body["error"]["message"]


def test_dashboard_bundle_rejects_portfolio_owned_by_another_user(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        SessionLocal = client.app.state.testing_session_local
        with SessionLocal() as db:
            other_user = User(email="other@example.com", display_name="Other User")
            db.add(other_user)
            db.flush()
            portfolio = Portfolio(
                user_id=other_user.id,
                name="Other Portfolio",
                base_currency="INR",
                benchmark_symbol="NIFTY50",
            )
            db.add(portfolio)
            db.commit()
            portfolio_id = portfolio.id

        response = client.get(f"/api/portfolios/{portfolio_id}/dashboard")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_dashboard_bundle_enabled_returns_valid_response_shape(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        portfolio = create_portfolio(client)
        create_holding(client, portfolio["id"])

        response = client.get(f"/api/portfolios/{portfolio['id']}/dashboard")

    assert response.status_code == 200
    body = response.json()
    assert body["portfolio_id"] == portfolio["id"]
    assert {
        "portfolio_id",
        "generated_at",
        "kpis",
        "sector_allocation",
        "asset_allocation",
        "top_holdings",
        "risk",
        "data_quality",
        "action_items",
        "data_status",
    }.issubset(body)
    assert body["kpis"]["total_invested"] == 25000
    assert body["kpis"]["current_value"] == 28421.5
    assert body["kpis"]["unrealized_pnl"] == 3421.5
    assert body["top_holdings"][0]["symbol"] == "RELIANCE"
    assert body["sector_allocation"][0]["name"] == "Energy"
    assert body["asset_allocation"][0]["name"] == "Equity"
    assert body["data_quality"]["missing_price_count"] == 0
    assert body["data_status"]["source"] == "stale"


def test_dashboard_bundle_empty_portfolio_returns_clean_empty_state(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        portfolio = create_portfolio(client)

        response = client.get(f"/api/portfolios/{portfolio['id']}/dashboard")

    assert response.status_code == 200
    body = response.json()
    assert body["kpis"]["current_value"] == 0
    assert body["kpis"]["total_invested"] == 0
    assert body["top_holdings"] == []
    assert body["sector_allocation"] == []
    assert body["asset_allocation"] == []
    assert body["risk"]["concentration_status"] == "empty"
    assert body["data_quality"]["holdings_count"] == 0
    assert body["data_status"]["source"] == "unavailable"
