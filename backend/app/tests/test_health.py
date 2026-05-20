from fastapi.testclient import TestClient

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
        "ai_provider_mode": "mock",
    }
