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
from app.modules.uploads.repository import job_mapping


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@contextmanager
def create_test_client(tmp_path, monkeypatch, *, enabled: bool) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("APP_ENV", "local")
    if enabled:
        monkeypatch.setenv("ENABLE_UPLOAD_SUGGESTIONS", "true")
    else:
        monkeypatch.delenv("ENABLE_UPLOAD_SUGGESTIONS", raising=False)
    get_settings.cache_clear()

    engine = create_engine(
        f"sqlite:///{tmp_path}/p_insight_upload_suggestions_api_test.db",
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
        json={"name": "Upload Suggestions Portfolio", "base_currency": "INR"},
    )
    assert response.status_code == 201
    return response.json()


def upload_csv(client: TestClient, portfolio_id: str, content: str) -> dict:
    response = client.post(
        f"/api/portfolios/{portfolio_id}/uploads",
        files={"file": ("holdings.csv", content.encode("utf-8"), "text/csv")},
    )
    assert response.status_code == 201
    return response.json()


def test_mapping_suggestions_disabled_returns_feature_disabled(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=False) as client:
        response = client.get("/api/uploads/upload-1/mapping-suggestions")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "feature_disabled"
    assert body["error"]["details"] == {"feature": "ENABLE_UPLOAD_SUGGESTIONS"}


def test_mapping_suggestions_for_sample_columns_do_not_mutate_upload_job(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        portfolio = create_portfolio(client)
        upload = upload_csv(
            client,
            portfolio["id"],
            "Ticker,Name,Shares,Average Cost,Market Value,Currency,Sector,Asset Class,Exchange\n"
            "RELIANCE,Reliance Industries Ltd,10,2500,28421.5,INR,Energy,Equity,NSE\n",
        )

        response = client.get(f"/api/uploads/{upload['id']}/mapping-suggestions")

        SessionLocal = client.app.state.testing_session_local
        with SessionLocal() as db:
            upload_job = db.get(models.UploadJob, upload["id"])
            assert upload_job is not None
            persisted_mapping = job_mapping(upload_job)

    assert response.status_code == 200
    body = response.json()
    assert body["upload_job_id"] == upload["id"]
    assert body["detected_columns"] == [
        "Ticker",
        "Name",
        "Shares",
        "Average Cost",
        "Market Value",
        "Currency",
        "Sector",
        "Asset Class",
        "Exchange",
    ]
    mapping = {suggestion["target_field"]: suggestion["source_column"] for suggestion in body["suggestions"]}
    assert mapping == {
        "symbol": "Ticker",
        "quantity": "Shares",
        "average_cost": "Average Cost",
        "market_value": "Market Value",
        "company_name": "Name",
        "sector": "Sector",
        "asset_class": "Asset Class",
        "exchange": "Exchange",
        "currency": "Currency",
    }
    assert all(suggestion["confidence"] >= 0.85 for suggestion in body["suggestions"])
    assert persisted_mapping == {}


def test_mapping_suggestions_unknown_columns_return_no_suggestions(tmp_path, monkeypatch) -> None:
    with create_test_client(tmp_path, monkeypatch, enabled=True) as client:
        portfolio = create_portfolio(client)
        upload = upload_csv(
            client,
            portfolio["id"],
            "Notes,Strategy,Uploaded At\n"
            "Long term,Core,2026-05-21\n",
        )

        response = client.get(f"/api/uploads/{upload['id']}/mapping-suggestions")

    assert response.status_code == 200
    body = response.json()
    assert body["detected_columns"] == ["Notes", "Strategy", "Uploaded At"]
    assert body["suggestions"] == []
