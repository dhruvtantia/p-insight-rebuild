import io
from collections.abc import Generator
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.modules.uploads.repository import job_mapping, row_errors, row_mapped_data, row_raw_data


@pytest.fixture()
def client(tmp_path) -> Generator[TestClient, None, None]:
    engine = create_engine(
        f"sqlite:///{tmp_path}/p_insight_upload_test.db",
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
        json={"name": "Upload Portfolio", "base_currency": "USD"},
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


def upload_xlsx(client: TestClient, portfolio_id: str, rows: list[list[object]]) -> dict:
    workbook = Workbook()
    sheet = workbook.active
    for row in rows:
        sheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    response = client.post(
        f"/api/portfolios/{portfolio_id}/uploads",
        files={
            "file": (
                "holdings.xlsx",
                buffer.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 201
    return response.json()


def apply_mapping(client: TestClient, upload_job_id: str) -> dict:
    response = client.post(
        f"/api/uploads/{upload_job_id}/column-mapping",
        json={
            "mapping": {
                "symbol": "Ticker",
                "company_name": "Name",
                "quantity": "Shares",
                "average_cost": "Average Cost",
                "market_value": "Market Value",
                "currency": "Currency",
                "sector": "Sector",
                "asset_class": "Asset Class",
                "exchange": "Exchange",
            }
        },
    )
    assert response.status_code == 200
    return response.json()


def validate_upload(client: TestClient, upload_job_id: str) -> dict:
    response = client.post(f"/api/uploads/{upload_job_id}/validate")
    assert response.status_code == 200
    return response.json()


def confirm_upload(client: TestClient, upload_job_id: str) -> dict:
    response = client.post(f"/api/uploads/{upload_job_id}/confirm")
    assert response.status_code == 200
    return response.json()


def test_valid_csv_upload(client: TestClient) -> None:
    portfolio = create_portfolio(client)
    upload = upload_csv(
        client,
        portfolio["id"],
        "Ticker,Name,Shares,Average Cost,Market Value,Currency,Sector,Asset Class,Exchange\n"
        "AAPL,Apple Inc.,10,100,1250,USD,Technology,Equity,NASDAQ\n",
    )

    assert upload["status"] == "uploaded"
    assert upload["total_rows"] == 1
    assert upload["detected_columns"] == [
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
    assert upload["preview_rows"][0]["Ticker"] == "AAPL"


def test_valid_xlsx_upload(client: TestClient) -> None:
    portfolio = create_portfolio(client)
    upload = upload_xlsx(
        client,
        portfolio["id"],
        [
            ["Ticker", "Name", "Shares", "Average Cost", "Market Value", "Currency"],
            ["MSFT", "Microsoft", 5, 200, 1500, "USD"],
        ],
    )

    assert upload["status"] == "uploaded"
    assert upload["total_rows"] == 1
    assert upload["preview_rows"][0]["Ticker"] == "MSFT"


def test_missing_symbol_rejected(client: TestClient) -> None:
    portfolio = create_portfolio(client)
    upload = upload_csv(
        client,
        portfolio["id"],
        "Ticker,Name,Shares,Average Cost,Market Value,Currency,Sector,Asset Class,Exchange\n"
        ",Missing Symbol,10,100,1000,USD,Technology,Equity,NASDAQ\n",
    )
    apply_mapping(client, upload["id"])
    validation = validate_upload(client, upload["id"])

    assert validation["upload_job"]["valid_rows"] == 0
    assert validation["upload_job"]["invalid_rows"] == 1
    assert validation["rows"][0]["status"] == "invalid"
    assert "symbol is required" in validation["rows"][0]["validation_errors"]


def test_invalid_quantity_rejected(client: TestClient) -> None:
    portfolio = create_portfolio(client)
    upload = upload_csv(
        client,
        portfolio["id"],
        "Ticker,Name,Shares,Average Cost,Market Value,Currency,Sector,Asset Class,Exchange\n"
        "AAPL,Apple Inc.,0,100,1000,USD,Technology,Equity,NASDAQ\n",
    )
    apply_mapping(client, upload["id"])
    validation = validate_upload(client, upload["id"])

    assert validation["upload_job"]["valid_rows"] == 0
    assert "quantity must be a positive number" in validation["rows"][0]["validation_errors"]


def test_mapping_required(client: TestClient) -> None:
    portfolio = create_portfolio(client)
    upload = upload_csv(
        client,
        portfolio["id"],
        "Ticker,Name,Shares,Average Cost,Market Value,Currency,Sector,Asset Class,Exchange\n"
        "AAPL,Apple Inc.,10,100,1000,USD,Technology,Equity,NASDAQ\n",
    )

    response = client.post(f"/api/uploads/{upload['id']}/validate")

    assert response.status_code == 422
    assert response.json()["error"]["message"] == "Column mapping is required before validation"


def test_confirm_import_creates_holdings(client: TestClient) -> None:
    portfolio = create_portfolio(client)
    upload = upload_csv(
        client,
        portfolio["id"],
        "Ticker,Name,Shares,Average Cost,Market Value,Currency,Sector,Asset Class,Exchange\n"
        "AAPL,Apple Inc.,10,100,1250,USD,Technology,Equity,NASDAQ\n",
    )
    apply_mapping(client, upload["id"])
    validate_upload(client, upload["id"])
    confirm = confirm_upload(client, upload["id"])
    holdings = client.get(f"/api/portfolios/{portfolio['id']}/holdings")

    assert confirm["status"] == "imported"
    assert confirm["imported_count"] == 1
    assert holdings.status_code == 200
    assert holdings.json()[0]["symbol"] == "AAPL"
    assert holdings.json()[0]["current_price"] == 125


def test_indian_csv_upload_normalizes_symbols_and_keeps_inr(client: TestClient) -> None:
    response = client.post(
        "/api/portfolios",
        json={"name": "India Upload Portfolio", "base_currency": "INR", "benchmark_symbol": "NIFTY 50"},
    )
    assert response.status_code == 201
    portfolio = response.json()

    upload = upload_csv(
        client,
        portfolio["id"],
        "Ticker,Name,Shares,Average Cost,Market Value,Currency,Sector,Asset Class,Exchange\n"
        "RELIANCE.NS,Reliance Industries Ltd,10,2850,28500,INR,Energy,Equity,NSE\n"
        "BSE:500325,Reliance BSE Line,2,2800,5600,INR,Energy,Equity,BSE\n",
    )
    apply_mapping(client, upload["id"])
    validation = validate_upload(client, upload["id"])
    confirm = confirm_upload(client, upload["id"])
    holdings = client.get(f"/api/portfolios/{portfolio['id']}/holdings").json()

    assert validation["upload_job"]["valid_rows"] == 2
    assert confirm["status"] == "imported"
    assert confirm["imported_count"] == 2
    assert sorted(holding["symbol"] for holding in holdings) == ["500325", "RELIANCE"]
    assert {holding["currency"] for holding in holdings} == {"INR"}
    assert {holding["exchange"] for holding in holdings} == {"NSE", "BSE"}


def test_isin_like_symbol_returns_validation_warning(client: TestClient) -> None:
    response = client.post(
        "/api/portfolios",
        json={"name": "India Upload Portfolio", "base_currency": "INR", "benchmark_symbol": "NIFTY 50"},
    )
    assert response.status_code == 201
    portfolio = response.json()

    upload = upload_csv(
        client,
        portfolio["id"],
        "Ticker,Name,Shares,Average Cost,Market Value,Currency,Sector,Asset Class,Exchange\n"
        "INE002A01018,Reliance Industries Ltd,10,2850,28500,INR,Energy,Equity,NSE\n",
    )
    apply_mapping(client, upload["id"])
    validation = validate_upload(client, upload["id"])

    assert validation["upload_job"]["valid_rows"] == 1
    assert validation["upload_job"]["invalid_rows"] == 0
    assert validation["rows"][0]["validation_errors"] == []
    assert validation["rows"][0]["warnings"] == [
        "Symbol appears to be an ISIN. Please map to NSE/BSE trading symbol."
    ]


def test_invalid_rows_do_not_create_holdings(client: TestClient) -> None:
    portfolio = create_portfolio(client)
    upload = upload_csv(
        client,
        portfolio["id"],
        "Ticker,Name,Shares,Average Cost,Market Value,Currency,Sector,Asset Class,Exchange\n"
        "AAPL,Apple Inc.,10,100,1250,USD,Technology,Equity,NASDAQ\n"
        "BAD,Bad Row,-2,100,200,USD,Technology,Equity,NASDAQ\n",
    )
    apply_mapping(client, upload["id"])
    validate_upload(client, upload["id"])
    confirm = confirm_upload(client, upload["id"])
    holdings = client.get(f"/api/portfolios/{portfolio['id']}/holdings").json()
    errors = client.get(f"/api/uploads/{upload['id']}/errors").json()

    assert confirm["status"] == "partial_imported"
    assert confirm["imported_count"] == 1
    assert confirm["invalid_count"] == 1
    assert confirm["duplicate_count"] == 0
    assert confirm["invalid_rows"] == 1
    assert confirm["rejected_row_reasons"] == [
        {
            "row_number": 2,
            "symbol": "BAD",
            "reasons": ["quantity must be a positive number"],
        }
    ]
    assert len(holdings) == 1
    assert holdings[0]["symbol"] == "AAPL"
    assert len(errors["errors"]) == 1


def test_duplicate_symbols_are_skipped(client: TestClient) -> None:
    portfolio = create_portfolio(client)
    existing = client.post(
        f"/api/portfolios/{portfolio['id']}/holdings",
        json={"symbol": "AAPL", "quantity": 1, "average_cost": 90, "current_price": 100},
    )
    assert existing.status_code == 201

    upload = upload_csv(
        client,
        portfolio["id"],
        "Ticker,Name,Shares,Average Cost,Market Value,Currency,Sector,Asset Class,Exchange\n"
        "AAPL,Apple Inc.,10,100,1250,USD,Technology,Equity,NASDAQ\n"
        "MSFT,Microsoft,5,200,1500,USD,Technology,Equity,NASDAQ\n"
        "MSFT,Microsoft Duplicate,3,200,900,USD,Technology,Equity,NASDAQ\n",
    )
    apply_mapping(client, upload["id"])
    validate_upload(client, upload["id"])
    confirm = confirm_upload(client, upload["id"])
    holdings = client.get(f"/api/portfolios/{portfolio['id']}/holdings").json()

    assert confirm["status"] == "partial_imported"
    assert confirm["imported_count"] == 1
    assert confirm["invalid_count"] == 0
    assert confirm["duplicate_count"] == 2
    assert confirm["skipped_count"] == 2
    assert any("AAPL skipped" in warning for warning in confirm["warnings"])
    assert [
        (reason["row_number"], reason["symbol"], reason["reasons"][0])
        for reason in confirm["rejected_row_reasons"]
    ] == [
        (1, "AAPL", "AAPL skipped because it already exists in the portfolio or upload batch"),
        (3, "MSFT", "MSFT skipped because it already exists in the portfolio or upload batch"),
    ]
    assert sorted(holding["symbol"] for holding in holdings) == ["AAPL", "MSFT"]


def test_partial_import_summary_includes_invalid_and_duplicate_reasons(client: TestClient) -> None:
    portfolio = create_portfolio(client)
    existing = client.post(
        f"/api/portfolios/{portfolio['id']}/holdings",
        json={"symbol": "AAPL", "quantity": 1, "average_cost": 90, "current_price": 100},
    )
    assert existing.status_code == 201

    upload = upload_csv(
        client,
        portfolio["id"],
        "Ticker,Name,Shares,Average Cost,Market Value,Currency,Sector,Asset Class,Exchange\n"
        "AAPL,Apple Inc.,10,100,1250,USD,Technology,Equity,NASDAQ\n"
        "MSFT,Microsoft,5,200,1500,USD,Technology,Equity,NASDAQ\n"
        "BAD,Bad Row,-2,200,900,USD,Technology,Equity,NASDAQ\n",
    )
    apply_mapping(client, upload["id"])
    validate_upload(client, upload["id"])
    confirm = confirm_upload(client, upload["id"])

    assert confirm["status"] == "partial_imported"
    assert confirm["imported_count"] == 1
    assert confirm["invalid_count"] == 1
    assert confirm["duplicate_count"] == 1
    assert confirm["skipped_count"] == 1
    assert confirm["invalid_rows"] == 1
    assert confirm["rejected_row_reasons"] == [
        {
            "row_number": 1,
            "symbol": "AAPL",
            "reasons": ["AAPL skipped because it already exists in the portfolio or upload batch"],
        },
        {
            "row_number": 3,
            "symbol": "BAD",
            "reasons": ["quantity must be a positive number"],
        },
    ]


def test_upload_json_helpers_return_safe_defaults_for_invalid_json() -> None:
    row = SimpleNamespace(
        raw_data_json="{not-json",
        mapped_data_json="[1, 2]",
        validation_errors_json='{"not": "a-list"}',
    )
    upload_job = SimpleNamespace(column_mapping_json="{not-json")

    assert row_raw_data(row) == {}
    assert row_mapped_data(row) == {}
    assert row_errors(row) == []
    assert job_mapping(upload_job) == {}
