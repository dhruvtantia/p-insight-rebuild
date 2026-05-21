from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from app.core.errors import ValidationAppError
from app.modules.common.data_status import DataStatus
from app.modules.market_data.history_schemas import (
    HistoricalPricePoint,
    HistoricalPriceResponse,
    HistoricalPriceSeries,
)
from app.modules.market_data.history_service import MarketHistoryService


def test_historical_price_contract_serializes_empty_series() -> None:
    as_of = datetime(2026, 5, 21, 10, 30, tzinfo=UTC)
    data_status = DataStatus.unavailable_source(provider="historical_market_data")
    response = HistoricalPriceResponse(
        period="1M",
        start_date=date(2026, 4, 21),
        end_date=date(2026, 5, 21),
        generated_at=as_of,
        series=[
            HistoricalPriceSeries(
                symbol="reliance",
                period="1M",
                start_date=date(2026, 4, 21),
                end_date=date(2026, 5, 21),
                data_status=data_status,
            )
        ],
        data_status=data_status,
    )

    payload = response.model_dump(mode="json")

    assert payload["series"][0]["symbol"] == "RELIANCE"
    assert payload["series"][0]["currency"] == "INR"
    assert payload["series"][0]["prices"] == []
    assert payload["data_status"]["source"] == "unavailable"


def test_historical_price_point_requires_non_negative_close() -> None:
    data_status = DataStatus.unavailable_source(provider="historical_market_data")

    with pytest.raises(ValidationError):
        HistoricalPricePoint(date=date(2026, 5, 21), close=-1, data_status=data_status)


def test_history_service_validates_supported_periods_and_normalizes_symbols() -> None:
    response = MarketHistoryService().build_empty_response(
        symbols=["reliance", "RELIANCE.NS", "TCS"],
        period="3m",
        end_date=date(2026, 5, 21),
    )

    assert response.period == "3M"
    assert response.start_date == date(2026, 2, 20)
    assert response.end_date == date(2026, 5, 21)
    assert [series.symbol for series in response.series] == ["RELIANCE", "TCS"]
    assert all(series.prices == [] for series in response.series)
    assert response.data_status.source == "unavailable"


@pytest.mark.parametrize("period", ["1M", "3M", "6M", "1Y", "5Y"])
def test_history_service_accepts_contract_periods(period: str) -> None:
    assert MarketHistoryService().validate_period(period) == period


def test_history_service_rejects_unsupported_period() -> None:
    with pytest.raises(ValidationAppError) as exc_info:
        MarketHistoryService().build_empty_response(
            symbols=["RELIANCE"],
            period="2Y",
            end_date=date(2026, 5, 21),
        )

    assert exc_info.value.error_code == "validation_error"
    assert "Unsupported history period" in exc_info.value.message


def test_history_service_rejects_empty_symbol_list() -> None:
    with pytest.raises(ValidationAppError) as exc_info:
        MarketHistoryService().build_empty_response(
            symbols=[],
            period="1M",
            end_date=date(2026, 5, 21),
        )

    assert exc_info.value.message == "At least one symbol is required"
