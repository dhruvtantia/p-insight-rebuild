from collections.abc import Generator
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.auth import get_development_user
from app.core.config import get_settings
from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.modules.ai_advisor.context_builder import AIAdvisorContextBuilder


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@contextmanager
def create_test_client(tmp_path, monkeypatch, *, optional_services_enabled: bool) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("APP_ENV", "local")
    optional_flags = [
        "ENABLE_DASHBOARD_BUNDLE",
        "ENABLE_PERFORMANCE_HISTORY",
        "ENABLE_RISK_V2",
        "ENABLE_FUNDAMENTALS",
        "ENABLE_PEERS",
        "ENABLE_SNAPSHOTS",
    ]
    for flag in optional_flags:
        if optional_services_enabled:
            monkeypatch.setenv(flag, "true")
        else:
            monkeypatch.delenv(flag, raising=False)
    get_settings.cache_clear()

    engine = create_engine(
        f"sqlite:///{tmp_path}/p_insight_ai_advisor_context_test.db",
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
        json={"name": "Advisor Context Portfolio", "base_currency": "INR", "benchmark_symbol": "NIFTY50"},
    )
    assert response.status_code == 201
    return response.json()


def create_holding(client: TestClient, portfolio_id: str, *, quantity: float = 10) -> dict:
    response = client.post(
        f"/api/portfolios/{portfolio_id}/holdings",
        json={
            "symbol": "RELIANCE",
            "company_name": "Reliance Industries Ltd.",
            "quantity": quantity,
            "average_cost": 2500,
            "current_price": 2842.15,
            "currency": "INR",
            "sector": "Energy",
            "asset_class": "Equity",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_advisor_context_works_when_optional_services_disabled(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, optional_services_enabled=False) as client:
        portfolio = create_portfolio(client)
        create_holding(client, portfolio["id"])
        SessionLocal = client.app.state.testing_session_local

        with SessionLocal() as db:
            user = get_development_user(db)
            context = AIAdvisorContextBuilder(db).build_context(portfolio_id=portfolio["id"], user=user)

    assert "optional_context" not in context
    assert context["portfolio_summary"]["name"] == "Advisor Context Portfolio"
    assert [holding["symbol"] for holding in context["holdings"]] == ["RELIANCE"]


def test_advisor_context_includes_enabled_optional_blocks(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, optional_services_enabled=True) as client:
        portfolio = create_portfolio(client)
        holding = create_holding(client, portfolio["id"])
        first_snapshot = client.post(f"/api/portfolios/{portfolio['id']}/snapshots", json={"label": "Before"})
        assert first_snapshot.status_code == 201
        patch_response = client.patch(
            f"/api/portfolios/{portfolio['id']}/holdings/{holding['id']}",
            json={"quantity": 12},
        )
        assert patch_response.status_code == 200
        second_snapshot = client.post(f"/api/portfolios/{portfolio['id']}/snapshots", json={"label": "After"})
        assert second_snapshot.status_code == 201
        SessionLocal = client.app.state.testing_session_local

        with SessionLocal() as db:
            user = get_development_user(db)
            context = AIAdvisorContextBuilder(db).build_context(portfolio_id=portfolio["id"], user=user)

    optional_context = context["optional_context"]
    assert {
        "dashboard_summary",
        "performance_history_summary",
        "risk_v2_summary",
        "fundamentals_summary",
        "peer_summary",
        "snapshot_change_summary",
    }.issubset(optional_context)
    assert optional_context["dashboard_summary"]["current_value"] > 0
    assert optional_context["performance_history_summary"]["method"] == "synthetic_current_holdings"
    assert "metric_status" in optional_context["risk_v2_summary"]
    assert optional_context["fundamentals_summary"]["coverage"]["covered_symbols"] == ["RELIANCE"]
    assert optional_context["peer_summary"]["symbol"] == "RELIANCE"
    assert optional_context["snapshot_change_summary"]["snapshot_count"] == 2
    assert optional_context["snapshot_change_summary"]["latest_change"]["quantity_changes"]


def test_advisor_response_avoids_direct_buy_sell_wording(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, optional_services_enabled=True) as client:
        portfolio = create_portfolio(client)
        create_holding(client, portfolio["id"])

        response = client.post(
            f"/api/portfolios/{portfolio['id']}/ai/question",
            json={"question": "Should I buy this or sell this?"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "mock"
    assert body["model"] == "deterministic-advisor-v1"
    assert "buy this" not in body["response"].lower()
    assert "sell this" not in body["response"].lower()
