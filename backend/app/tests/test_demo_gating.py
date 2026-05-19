from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app


@pytest.fixture()
def production_client(tmp_path, monkeypatch) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ENABLE_DEMO_MODE", "false")
    get_settings.cache_clear()

    engine = create_engine(
        f"sqlite:///{tmp_path}/p_insight_demo_gating_test.db",
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
    get_settings.cache_clear()


def test_production_rejects_demo_auth(production_client: TestClient) -> None:
    response = production_client.post(
        "/api/portfolios",
        json={"name": "Blocked Portfolio", "base_currency": "USD"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"
    assert "Demo auth is disabled" in response.json()["error"]["message"]


def test_production_rejects_demo_seed(production_client: TestClient) -> None:
    response = production_client.post("/api/demo/seed")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"
    assert "Demo" in response.json()["error"]["message"]
    assert "disabled" in response.json()["error"]["message"]
