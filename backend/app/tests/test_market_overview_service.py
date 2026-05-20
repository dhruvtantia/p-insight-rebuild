from datetime import UTC, datetime

import pytest

from app.core.config import get_settings
from app.core.errors import ExternalProviderError
from app.modules.market_data.schemas import PriceQuote
from app.modules.market_overview.service import MarketOverviewService


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_market_overview_mock_provider_response_shape(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "mock_india")

    response = MarketOverviewService(db=object()).get_overview()

    assert response.market_status.market == "India"
    assert response.market_status.state in {"open", "closed"}
    assert response.major_indices
    assert {"NIFTY50", "SENSEX", "BANKNIFTY"}.issubset({index.symbol for index in response.major_indices})
    assert response.sector_indices
    assert response.top_gainers
    assert response.top_losers
    assert response.generated_at is not None


def test_market_overview_data_status_is_explicit(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "mock_india")

    response = MarketOverviewService(db=object()).get_overview()

    assert response.data_status.is_mock is True
    assert response.data_status.provider == "mock_india"
    assert response.market_status.data_status.is_mock is True
    assert all(index.data_status.is_mock is True for index in response.major_indices)
    assert all(sector.data_status.is_mock is True for sector in response.sector_indices)
    assert all(mover.data_status.is_mock is True for mover in [*response.top_gainers, *response.top_losers])


def test_market_overview_gracefully_skips_unavailable_symbols() -> None:
    response = MarketOverviewService(
        db=object(),
        market_data_service=FakeMarketDataService(FakePartialProvider()),
    ).get_overview()

    assert [index.symbol for index in response.major_indices] == ["NIFTY50"]
    assert response.sector_indices == []
    assert response.top_gainers == []
    assert response.top_losers == []
    assert response.data_status.is_mock is True


def test_market_overview_returns_unavailable_status_when_provider_has_no_prices() -> None:
    response = MarketOverviewService(
        db=object(),
        market_data_service=FakeMarketDataService(FakeUnavailableProvider()),
    ).get_overview()

    assert response.major_indices == []
    assert response.sector_indices == []
    assert response.top_gainers == []
    assert response.top_losers == []
    assert response.data_status.source == "unavailable"
    assert response.data_status.provider == "mock_india"
    assert response.data_status.is_stale is True


class FakeMarketDataService:
    def __init__(self, provider):
        self.provider = provider


class FakePartialProvider:
    source = "mock_india"

    def get_latest_price(self, symbol: str) -> PriceQuote:
        if symbol != "NIFTY50":
            raise ExternalProviderError(f"{symbol} is unavailable")
        as_of = datetime(2026, 1, 1, tzinfo=UTC)
        return PriceQuote(
            symbol="NIFTY50",
            price=22530.7,
            currency="INR",
            source=self.source,
            as_of=as_of,
            is_realtime=False,
        )

    def get_company_profile(self, symbol: str):
        raise ExternalProviderError(f"{symbol} profile is unavailable")


class FakeUnavailableProvider:
    source = "mock_india"

    def get_latest_price(self, symbol: str):
        raise ExternalProviderError(f"{symbol} is unavailable")

    def get_company_profile(self, symbol: str):
        raise ExternalProviderError(f"{symbol} profile is unavailable")
