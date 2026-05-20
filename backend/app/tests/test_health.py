from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


def test_health_endpoint() -> None:
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "p-insight-backend",
    }


def test_status_endpoint_exposes_demo_safety_config() -> None:
    client = TestClient(create_app())

    response = client.get("/api/status")

    assert response.status_code == 200
    assert response.json() == {
        "app_env": "local",
        "demo_mode_enabled": True,
        "market_data_provider": "mock_india",
        "market_data_is_mock": True,
        "ai_provider_mode": "mock",
        "ai_is_mock": True,
        "production_safe": False,
        "warnings": [
            "Market data provider 'mock_india' is mock data and is not production-safe.",
            "AI provider mode is mock and is not production-safe.",
        ],
    }


def test_status_endpoint_reports_production_mock_overrides(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ALLOW_PRODUCTION_MOCK_MARKET_DATA", "true")
    monkeypatch.setenv("ALLOW_PRODUCTION_MOCK_AI", "true")
    get_settings.cache_clear()

    client = TestClient(create_app())
    response = client.get("/api/status")

    assert response.status_code == 200
    body = response.json()
    assert body["app_env"] == "production"
    assert body["demo_mode_enabled"] is False
    assert body["market_data_provider"] == "mock_india"
    assert body["market_data_is_mock"] is True
    assert body["ai_provider_mode"] == "mock"
    assert body["ai_is_mock"] is True
    assert body["production_safe"] is False
    assert any("Production mock market data override is enabled" in warning for warning in body["warnings"])
    assert any("Production mock AI override is enabled" in warning for warning in body["warnings"])

    get_settings.cache_clear()
