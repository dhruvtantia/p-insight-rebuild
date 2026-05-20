from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.modules.common.data_status import DataStatus
from app.modules.market_overview.schemas import (
    MarketIndexCard,
    MarketMover,
    MarketOverviewResponse,
    MarketStatus,
    SectorIndexCard,
)


def test_market_overview_response_supports_india_first_contract() -> None:
    as_of = datetime(2026, 5, 21, 10, 30, tzinfo=UTC)
    data_status = DataStatus.mock_source(provider="mock_india", as_of=as_of)

    response = MarketOverviewResponse(
        market_status=MarketStatus(
            market="India",
            exchange="NSE",
            state="open",
            as_of=as_of,
            next_close_at=as_of + timedelta(hours=6),
            data_status=data_status,
        ),
        major_indices=[
            MarketIndexCard(
                symbol="nifty50",
                name="NIFTY 50",
                value=22530.7,
                change=120.5,
                change_percent=0.54,
                exchange="NSE",
                as_of=as_of,
                data_status=data_status,
            ),
            MarketIndexCard(
                symbol="sensex",
                name="Sensex",
                value=74221.1,
                change=-88.3,
                change_percent=-0.12,
                exchange="BSE",
                as_of=as_of,
                data_status=data_status,
            ),
            MarketIndexCard(
                symbol="banknifty",
                name="Bank Nifty",
                value=48075.2,
                change=210.0,
                change_percent=0.44,
                exchange="NSE",
                as_of=as_of,
                data_status=data_status,
            ),
        ],
        sector_indices=[
            SectorIndexCard(
                symbol="NIFTYIT",
                name="NIFTY IT",
                sector="Information Technology",
                value=34210.4,
                change=150.0,
                change_percent=0.43,
                exchange="NSE",
                as_of=as_of,
                data_status=data_status,
            )
        ],
        top_gainers=[
            MarketMover(
                symbol="TCS",
                company_name="Tata Consultancy Services Ltd.",
                last_price=3925.8,
                change=95.2,
                change_percent=2.49,
                exchange="NSE",
                sector="Information Technology",
                as_of=as_of,
                data_status=data_status,
            )
        ],
        top_losers=[
            MarketMover(
                symbol="RELIANCE",
                company_name="Reliance Industries Ltd.",
                last_price=2842.15,
                change=-30.5,
                change_percent=-1.06,
                exchange="NSE",
                sector="Energy",
                as_of=as_of,
                data_status=data_status,
            )
        ],
        generated_at=as_of,
        data_status=data_status,
    )

    assert response.market_status.state == "open"
    assert [index.name for index in response.major_indices] == ["NIFTY 50", "Sensex", "Bank Nifty"]
    assert response.major_indices[0].symbol == "NIFTY50"
    assert response.major_indices[1].symbol == "SENSEX"
    assert response.major_indices[2].symbol == "BANKNIFTY"
    assert response.sector_indices[0].sector == "Information Technology"
    assert response.top_gainers[0].change_percent > 0
    assert response.top_losers[0].change_percent < 0
    assert response.data_status.is_mock is True


def test_market_status_supports_closed_state_and_stale_metadata() -> None:
    as_of = datetime(2026, 5, 21, 16, 0, tzinfo=UTC)
    stale_status = DataStatus.stale_source(provider="nse_bse_future", as_of=as_of)

    market_status = MarketStatus(
        state="closed",
        as_of=as_of,
        next_open_at=as_of + timedelta(hours=17),
        data_status=stale_status,
    )

    assert market_status.market == "India"
    assert market_status.timezone == "Asia/Kolkata"
    assert market_status.data_status.is_stale is True


def test_market_overview_schema_rejects_invalid_market_state() -> None:
    as_of = datetime(2026, 5, 21, tzinfo=UTC)
    data_status = DataStatus.mock_source(provider="mock_india", as_of=as_of)

    with pytest.raises(ValidationError):
        MarketStatus(state="holiday", as_of=as_of, data_status=data_status)
