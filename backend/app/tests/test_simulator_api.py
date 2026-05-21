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
        monkeypatch.setenv("ENABLE_SIMULATOR", "true")
    else:
        monkeypatch.delenv("ENABLE_SIMULATOR", raising=False)
    get_settings.cache_clear()

    engine = create_engine(
        f"sqlite:///{tmp_path}/p_insight_simulator_api_test.db",
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
    response = client.post("/api/portfolios", json={"name": "Simulator Portfolio", "base_currency": "INR"})
    assert response.status_code == 201
    return response.json()


def create_holding(
    client: TestClient,
    portfolio_id: str,
    *,
    symbol: str,
    quantity: float,
    current_price: float,
    sector: str,
) -> dict:
    response = client.post(
        f"/api/portfolios/{portfolio_id}/holdings",
        json={
            "symbol": symbol,
            "quantity": quantity,
            "average_cost": current_price * 0.8,
            "current_price": current_price,
            "currency": "INR",
            "sector": sector,
            "asset_class": "Equity",
        },
    )
    assert response.status_code == 201
    return response.json()


def seed_portfolio(client: TestClient) -> dict:
    portfolio = create_portfolio(client)
    create_holding(client, portfolio["id"], symbol="RELIANCE", quantity=10, current_price=100, sector="Energy")
    create_holding(client, portfolio["id"], symbol="TCS", quantity=5, current_price=200, sector="IT")
    return portfolio


def test_simulator_disabled_returns_feature_disabled(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=False) as client:
        response = client.post(
            "/api/portfolios/portfolio-1/simulate",
            json={"target_weights": {"RELIANCE": 60, "TCS": 40}},
        )

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "feature_disabled"
    assert body["error"]["details"] == {"feature": "ENABLE_SIMULATOR"}


def test_valid_scenario_returns_simulated_allocation(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        portfolio = seed_portfolio(client)

        response = client.post(
            f"/api/portfolios/{portfolio['id']}/simulate",
            json={"target_weights": {"RELIANCE": 60, "TCS": 40}},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["portfolio_id"] == portfolio["id"]
    assert body["persisted"] is False
    assert {item["symbol"]: item["weight"] for item in body["current_allocation"]} == {
        "RELIANCE": 0.5,
        "TCS": 0.5,
    }
    simulated = {item["symbol"]: item for item in body["simulated_allocation"]}
    assert simulated["RELIANCE"]["weight"] == 0.6
    assert simulated["RELIANCE"]["estimated_value"] == 1200
    assert simulated["TCS"]["weight"] == 0.4
    assert simulated["TCS"]["estimated_value"] == 800
    assert body["estimated_value_distribution"]["total_value"] == 2000
    assert body["concentration_change"]["current_largest_weight"] == 0.5
    assert body["concentration_change"]["simulated_largest_weight"] == 0.6
    assert any("No trades were executed" in warning for warning in body["warnings"])


def test_weights_not_equal_to_100_are_normalized_with_warning(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        portfolio = seed_portfolio(client)

        response = client.post(
            f"/api/portfolios/{portfolio['id']}/simulate",
            json={"target_weights": {"RELIANCE": 30, "TCS": 30}},
        )

    assert response.status_code == 200
    body = response.json()
    simulated = {item["symbol"]: item["weight"] for item in body["simulated_allocation"]}
    assert simulated == {"RELIANCE": 0.5, "TCS": 0.5}
    assert any("sum to 60.0 instead of 100" in warning for warning in body["warnings"])


def test_remove_holding(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        portfolio = seed_portfolio(client)

        response = client.post(
            f"/api/portfolios/{portfolio['id']}/simulate",
            json={"removed_symbols": ["TCS"]},
        )

    assert response.status_code == 200
    body = response.json()
    simulated = {item["symbol"]: item for item in body["simulated_allocation"]}
    assert simulated["RELIANCE"]["weight"] == 1
    assert simulated["RELIANCE"]["estimated_value"] == 2000
    assert simulated["TCS"]["is_removed"] is True
    assert simulated["TCS"]["weight"] == 0
    assert simulated["TCS"]["estimated_value"] == 0
    assert body["concentration_change"]["simulated_largest_symbol"] == "RELIANCE"


def test_add_unknown_symbol_warning(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        portfolio = seed_portfolio(client)

        response = client.post(
            f"/api/portfolios/{portfolio['id']}/simulate",
            json={
                "target_weights": {"RELIANCE": 50, "TCS": 30, "UNKNOWNCO": 20},
                "added_symbols": ["UNKNOWNCO"],
            },
        )

    assert response.status_code == 200
    body = response.json()
    simulated = {item["symbol"]: item for item in body["simulated_allocation"]}
    assert simulated["UNKNOWNCO"]["is_added"] is True
    assert simulated["UNKNOWNCO"]["estimated_value"] == 400
    assert any("UNKNOWNCO" in warning for warning in body["warnings"])
