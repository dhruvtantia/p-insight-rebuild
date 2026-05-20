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
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "mock_india")
    monkeypatch.setenv("INDIAN_MARKET_DATA_PROVIDER", "mock_india")
    if enabled:
        monkeypatch.setenv("ENABLE_MARKET_OVERVIEW", "true")
    else:
        monkeypatch.delenv("ENABLE_MARKET_OVERVIEW", raising=False)
    get_settings.cache_clear()

    engine = create_engine(
        f"sqlite:///{tmp_path}/p_insight_market_overview_api_test.db",
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


def test_market_overview_disabled_returns_feature_disabled(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=False) as client:
        response = client.get("/api/market/overview")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "feature_disabled"
    assert body["error"]["details"] == {"feature": "ENABLE_MARKET_OVERVIEW"}
    assert "disabled" in body["error"]["message"]


def test_market_overview_enabled_returns_response(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        response = client.get("/api/market/overview")

    assert response.status_code == 200
    body = response.json()
    assert {"market_status", "major_indices", "sector_indices", "top_gainers", "top_losers", "generated_at", "data_status"}.issubset(
        body
    )
    assert body["market_status"]["market"] == "India"
    assert body["market_status"]["state"] in {"open", "closed"}
    assert body["major_indices"]
    assert body["top_gainers"]
    assert body["top_losers"]


def test_market_overview_enabled_response_includes_data_status(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        response = client.get("/api/market/overview")

    assert response.status_code == 200
    body = response.json()
    assert body["data_status"]["is_mock"] is True
    assert body["data_status"]["provider"] == "mock_india"
    assert body["market_status"]["data_status"]["is_mock"] is True
    assert all(index["data_status"]["is_mock"] is True for index in body["major_indices"])
    assert all(mover["data_status"]["is_mock"] is True for mover in [*body["top_gainers"], *body["top_losers"]])
