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
        monkeypatch.setenv("ENABLE_SNAPSHOTS", "true")
    else:
        monkeypatch.delenv("ENABLE_SNAPSHOTS", raising=False)
    get_settings.cache_clear()

    engine = create_engine(
        f"sqlite:///{tmp_path}/p_insight_snapshots_api_test.db",
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
    response = client.post(
        "/api/portfolios",
        json={"name": "Snapshot Portfolio", "base_currency": "INR"},
    )
    assert response.status_code == 201
    return response.json()


def create_holding(
    client: TestClient,
    portfolio_id: str,
    *,
    symbol: str,
    quantity: float,
    current_price: float,
    average_cost: float,
    sector: str,
) -> dict:
    response = client.post(
        f"/api/portfolios/{portfolio_id}/holdings",
        json={
            "symbol": symbol,
            "quantity": quantity,
            "average_cost": average_cost,
            "current_price": current_price,
            "currency": "INR",
            "sector": sector,
            "asset_class": "Equity",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_snapshots_disabled_returns_feature_disabled(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=False) as client:
        response = client.post("/api/portfolios/portfolio-1/snapshots", json={"label": "Disabled"})

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "feature_disabled"
    assert body["error"]["details"] == {"feature": "ENABLE_SNAPSHOTS"}


def test_create_and_list_snapshots(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        portfolio = create_portfolio(client)
        create_holding(
            client,
            portfolio["id"],
            symbol="RELIANCE",
            quantity=10,
            current_price=100,
            average_cost=80,
            sector="Energy",
        )

        create_response = client.post(
            f"/api/portfolios/{portfolio['id']}/snapshots",
            json={"label": "Initial"},
        )
        list_response = client.get(f"/api/portfolios/{portfolio['id']}/snapshots")

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["label"] == "Initial"
    assert created["portfolio_id"] == portfolio["id"]
    assert created["total_value"] == 1000
    assert created["holdings_value"] == 1000
    assert created["cost_basis"] == 800
    assert created["holdings_count"] == 1
    assert created["holdings"][0]["symbol"] == "RELIANCE"
    assert created["prices"] == [{"symbol": "RELIANCE", "current_price": 100.0, "currency": "INR"}]
    assert created["sector_allocation"][0]["name"] == "Energy"
    assert created["concentration_summary"]["status"] == "high"

    assert list_response.status_code == 200
    listed = list_response.json()
    assert len(listed) == 1
    assert listed[0]["id"] == created["id"]
    assert listed[0]["label"] == "Initial"
    assert listed[0]["holdings_count"] == 1


def test_compare_snapshots(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        portfolio = create_portfolio(client)
        reliance = create_holding(
            client,
            portfolio["id"],
            symbol="RELIANCE",
            quantity=10,
            current_price=100,
            average_cost=80,
            sector="Energy",
        )
        itc = create_holding(
            client,
            portfolio["id"],
            symbol="ITC",
            quantity=5,
            current_price=50,
            average_cost=40,
            sector="Consumer Staples",
        )
        first = client.post(f"/api/portfolios/{portfolio['id']}/snapshots", json={"label": "Before"}).json()

        patch_response = client.patch(
            f"/api/portfolios/{portfolio['id']}/holdings/{reliance['id']}",
            json={"quantity": 15, "current_price": 110},
        )
        assert patch_response.status_code == 200
        delete_response = client.delete(f"/api/portfolios/{portfolio['id']}/holdings/{itc['id']}")
        assert delete_response.status_code == 204
        create_holding(
            client,
            portfolio["id"],
            symbol="TCS",
            quantity=2,
            current_price=200,
            average_cost=150,
            sector="Information Technology",
        )
        second = client.post(f"/api/portfolios/{portfolio['id']}/snapshots", json={"label": "After"}).json()

        compare_response = client.get(
            f"/api/portfolios/{portfolio['id']}/snapshots/compare?from_id={first['id']}&to_id={second['id']}"
        )

    assert compare_response.status_code == 200
    body = compare_response.json()
    assert body["from_snapshot_id"] == first["id"]
    assert body["to_snapshot_id"] == second["id"]
    assert [holding["symbol"] for holding in body["added_holdings"]] == ["TCS"]
    assert [holding["symbol"] for holding in body["removed_holdings"]] == ["ITC"]
    assert body["quantity_changes"] == [
        {"symbol": "RELIANCE", "from_quantity": 10.0, "to_quantity": 15.0, "quantity_change": 5.0}
    ]
    assert body["value_changes"]["from_total_value"] == 1250
    assert body["value_changes"]["to_total_value"] == 2050
    assert body["value_changes"]["total_value_change"] == 800
    sector_changes = {change["name"]: change for change in body["sector_allocation_changes"]}
    assert sector_changes["Consumer Staples"]["to_value"] == 0
    assert sector_changes["Information Technology"]["from_value"] == 0
    assert body["concentration_changes"]["from_status"] == "high"
    assert body["concentration_changes"]["to_largest_symbol"] == "RELIANCE"


def test_empty_portfolio_snapshot(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        portfolio = create_portfolio(client)

        response = client.post(f"/api/portfolios/{portfolio['id']}/snapshots", json={"label": "Empty"})

    assert response.status_code == 201
    body = response.json()
    assert body["label"] == "Empty"
    assert body["total_value"] == 0
    assert body["holdings_value"] == 0
    assert body["cost_basis"] == 0
    assert body["holdings_count"] == 0
    assert body["holdings"] == []
    assert body["prices"] == []
    assert body["sector_allocation"] == []
    assert body["concentration_summary"]["status"] == "empty"
