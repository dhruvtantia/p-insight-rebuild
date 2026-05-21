from datetime import date

import pytest

from app.core.config import get_settings
from app.core.errors import ValidationAppError
from app.modules.demo.fixtures.historical_prices import build_mock_historical_prices
from app.modules.market_data.history_service import MarketHistoryService


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_mock_historical_prices_are_deterministic() -> None:
    first = build_mock_historical_prices(
        symbol="RELIANCE",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 10),
    )
    second = build_mock_historical_prices(
        symbol="RELIANCE",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 10),
    )

    assert first == second
    assert len(first) == 10
    assert first[0].date == date(2026, 1, 1)
    assert first[-1].date == date(2026, 1, 10)


def test_mock_history_response_marks_data_status_as_mock(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "local")

    response = MarketHistoryService().build_mock_response(
        symbols=["reliance", "TCS"],
        period="1M",
        end_date=date(2026, 5, 21),
    )

    assert response.data_status.source == "mock"
    assert response.data_status.provider == "mock_historical_prices"
    assert response.data_status.is_mock is True
    assert response.data_status.is_realtime is False
    assert [series.symbol for series in response.series] == ["RELIANCE", "TCS"]
    assert all(series.data_status.is_mock is True for series in response.series)
    assert all(point.data_status.is_mock is True for series in response.series for point in series.prices)
    assert all(series.prices for series in response.series)


def test_mock_history_service_blocks_production_without_override(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("ALLOW_PRODUCTION_MOCK_MARKET_DATA", raising=False)

    with pytest.raises(ValidationAppError, match="Mock historical market data is disabled in production"):
        MarketHistoryService().build_mock_response(
            symbols=["RELIANCE"],
            period="1M",
            end_date=date(2026, 5, 21),
        )


def test_mock_history_service_allows_explicit_production_override(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ALLOW_PRODUCTION_MOCK_MARKET_DATA", "true")

    response = MarketHistoryService().build_mock_response(
        symbols=["RELIANCE"],
        period="1M",
        end_date=date(2026, 5, 21),
    )

    assert response.data_status.is_mock is True
    assert response.series[0].prices
