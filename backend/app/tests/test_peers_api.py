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
        monkeypatch.setenv("ENABLE_PEERS", "true")
    else:
        monkeypatch.delenv("ENABLE_PEERS", raising=False)
    get_settings.cache_clear()

    engine = create_engine(
        f"sqlite:///{tmp_path}/p_insight_peers_api_test.db",
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
    response = client.post("/api/portfolios", json={"name": "Peers Portfolio", "base_currency": "INR"})
    assert response.status_code == 201
    return response.json()


def test_peers_disabled_returns_feature_disabled(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=False) as client:
        response = client.get("/api/portfolios/portfolio-1/peers/RELIANCE")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "feature_disabled"
    assert body["error"]["details"] == {"feature": "ENABLE_PEERS"}


def test_known_symbol_returns_peer_comparison(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        portfolio = create_portfolio(client)

        response = client.get(f"/api/portfolios/{portfolio['id']}/peers/RELIANCE")

    assert response.status_code == 200
    body = response.json()
    assert body["portfolio_id"] == portfolio["id"]
    assert body["symbol"] == "RELIANCE"
    assert body["selected_company"]["symbol"] == "RELIANCE"
    assert [company["symbol"] for company in body["peer_companies"]] == ["TCS", "INFY"]
    assert body["peer_set_quality"]["source"] == "static_india_peer_map"
    assert body["peer_set_quality"]["peer_count"] == 2
    assert body["peer_set_quality"]["covered_peer_count"] == 2
    assert body["peer_set_quality"]["coverage_percent"] == 100
    assert body["peer_set_quality"]["is_sparse"] is False
    rows = {row["metric"]: row for row in body["metric_comparison_table"]}
    assert rows["pe_ratio"]["selected_value"] == 27.4
    assert rows["pe_ratio"]["peer_values"] == {"TCS": 31.8, "INFY": 24.7}
    assert rows["pe_ratio"]["selected_rank"] == 2
    assert body["simple_ranks"]["RELIANCE"]["pe_ratio"] == 2
    assert any("static India" in warning for warning in body["warnings"])
    assert any("mock data" in warning for warning in body["warnings"])


def test_unknown_symbol_returns_empty_peer_set_with_warnings(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        portfolio = create_portfolio(client)

        response = client.get(f"/api/portfolios/{portfolio['id']}/peers/UNKNOWNCO")

    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "UNKNOWNCO"
    assert body["selected_company"]["coverage"]["coverage_ratio"] == 0
    assert body["peer_companies"] == []
    assert body["peer_set_quality"]["peer_count"] == 0
    assert body["peer_set_quality"]["is_sparse"] is True
    assert body["metric_comparison_table"][0]["selected_rank"] is None
    assert body["simple_ranks"]["UNKNOWNCO"]["pe_ratio"] is None
    assert any("No static peer set" in warning for warning in body["warnings"])
    assert any("selected symbol UNKNOWNCO" in warning for warning in body["warnings"])


def test_sparse_peer_set_warning(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        portfolio = create_portfolio(client)

        response = client.get(f"/api/portfolios/{portfolio['id']}/peers/TCS")

    assert response.status_code == 200
    body = response.json()
    assert [company["symbol"] for company in body["peer_companies"]] == ["INFY"]
    assert body["peer_set_quality"]["peer_count"] == 1
    assert body["peer_set_quality"]["is_sparse"] is True
    assert any("sparse" in warning for warning in body["warnings"])
