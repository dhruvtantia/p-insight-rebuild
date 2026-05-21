from collections.abc import Generator
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@contextmanager
def create_test_client(monkeypatch, *, enabled: bool) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("APP_ENV", "local")
    if enabled:
        monkeypatch.setenv("ENABLE_HISTORICAL_DATA", "true")
    else:
        monkeypatch.delenv("ENABLE_HISTORICAL_DATA", raising=False)
    get_settings.cache_clear()

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def test_market_history_disabled_returns_feature_disabled(monkeypatch) -> None:
    with create_test_client(monkeypatch, enabled=False) as client:
        response = client.get("/api/market/history?symbols=RELIANCE&period=1Y")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "feature_disabled"
    assert body["error"]["details"] == {"feature": "ENABLE_HISTORICAL_DATA"}


def test_market_history_enabled_returns_mock_history(monkeypatch) -> None:
    with create_test_client(monkeypatch, enabled=True) as client:
        response = client.get("/api/market/history?symbols=RELIANCE&period=1M")

    assert response.status_code == 200
    body = response.json()
    assert body["period"] == "1M"
    assert body["data_status"]["source"] == "mock"
    assert body["data_status"]["is_mock"] is True
    assert body["data_status"]["provider"] == "mock_historical_prices"
    assert len(body["series"]) == 1
    assert body["series"][0]["symbol"] == "RELIANCE"
    assert body["series"][0]["prices"]
    assert body["series"][0]["prices"][0]["data_status"]["is_mock"] is True


def test_market_history_invalid_period_returns_clean_error(monkeypatch) -> None:
    with create_test_client(monkeypatch, enabled=True) as client:
        response = client.get("/api/market/history?symbols=RELIANCE&period=2Y")

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert "Unsupported history period" in body["error"]["message"]


def test_market_history_supports_multiple_symbols(monkeypatch) -> None:
    with create_test_client(monkeypatch, enabled=True) as client:
        response = client.get("/api/market/history?symbols=RELIANCE,TCS,RELIANCE.NS&period=1Y")

    assert response.status_code == 200
    body = response.json()
    assert body["period"] == "1Y"
    assert [series["symbol"] for series in body["series"]] == ["RELIANCE", "TCS"]
    assert all(series["prices"] for series in body["series"])
    assert all(series["data_status"]["is_mock"] is True for series in body["series"])
