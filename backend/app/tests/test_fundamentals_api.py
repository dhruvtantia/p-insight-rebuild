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
        monkeypatch.setenv("ENABLE_FUNDAMENTALS", "true")
    else:
        monkeypatch.delenv("ENABLE_FUNDAMENTALS", raising=False)
    get_settings.cache_clear()

    engine = create_engine(
        f"sqlite:///{tmp_path}/p_insight_fundamentals_api_test.db",
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
    response = client.post("/api/portfolios", json={"name": "Fundamentals Portfolio", "base_currency": "INR"})
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


def test_fundamentals_disabled_returns_feature_disabled(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=False) as client:
        response = client.get("/api/assets/RELIANCE/fundamentals")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "feature_disabled"
    assert body["error"]["details"] == {"feature": "ENABLE_FUNDAMENTALS"}


def test_single_asset_fundamentals(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        response = client.get("/api/assets/RELIANCE/fundamentals")

    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "RELIANCE"
    assert body["metrics"]["pe_ratio"] == 27.4
    assert body["metrics"]["market_cap"] == 19_400_000_000_000
    assert body["coverage"]["coverage_ratio"] == 1
    assert body["coverage"]["is_complete"] is True
    assert body["data_status"]["source"] == "mock"
    assert body["data_status"]["provider"] == "mock_fundamentals"


def test_portfolio_fundamentals_returns_weighted_metrics(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        portfolio = create_portfolio(client)
        create_holding(client, portfolio["id"], symbol="RELIANCE", quantity=10, current_price=100)
        create_holding(client, portfolio["id"], symbol="TCS", quantity=10, current_price=300)

        response = client.get(f"/api/portfolios/{portfolio['id']}/fundamentals")

    assert response.status_code == 200
    body = response.json()
    assert body["portfolio_id"] == portfolio["id"]
    assert [item["symbol"] for item in body["fundamentals"]] == ["RELIANCE", "TCS"]
    assert body["coverage"]["coverage_percent"] == 100
    assert body["coverage"]["weighted_coverage_percent"] == 100
    assert body["missing_symbols"] == []
    assert body["weighted_metrics"]["pe_ratio"] == pytest.approx(30.7)
    assert body["weighted_metrics"]["roe"] == pytest.approx(0.363)
    assert body["weighted_metrics"]["market_cap"] == 33_600_000_000_000
    assert body["data_status"]["source"] == "mock"
    assert body["warnings"] == []


def test_portfolio_fundamentals_reports_missing_coverage(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        portfolio = create_portfolio(client)
        create_holding(client, portfolio["id"], symbol="RELIANCE", quantity=10, current_price=100)
        create_holding(client, portfolio["id"], symbol="UNKNOWNCO", quantity=10, current_price=100)

        response = client.get(f"/api/portfolios/{portfolio['id']}/fundamentals")

    assert response.status_code == 200
    body = response.json()
    assert body["coverage"]["coverage_percent"] == 50
    assert body["coverage"]["weighted_coverage_percent"] == 50
    assert body["missing_symbols"] == ["UNKNOWNCO"]
    assert body["weighted_metrics"]["pe_ratio"] == 27.4
    assert body["weighted_metrics"]["market_cap"] == 19_400_000_000_000
    assert "UNKNOWNCO" in body["warnings"][0]
    assert "UNKNOWNCO" in body["data_status"]["warning"]
