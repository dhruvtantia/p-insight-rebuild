from app.core.config import get_settings
from app.core.errors import ExternalProviderError
from app.modules.market_data.providers.base import MarketDataProvider
from app.modules.market_data.schemas import CompanyProfile, FxRate, PriceHistoryPoint, PriceQuote


class PlaceholderIndiaProvider(MarketDataProvider):
    source = "india_placeholder"
    provider_display_name = "Indian market data provider"
    api_key_setting = "market_data_api_key"

    def __init__(self, api_key: str | None = None):
        settings = get_settings()
        self.api_key = api_key or getattr(settings, self.api_key_setting) or settings.market_data_api_key

    def get_latest_price(self, symbol: str) -> PriceQuote:
        self._ensure_api_key()
        raise ExternalProviderError(f"{self.provider_display_name} is not implemented yet")

    def get_batch_prices(self, symbols: list[str]) -> list[PriceQuote]:
        self._ensure_api_key()
        raise ExternalProviderError(f"{self.provider_display_name} is not implemented yet")

    def get_price_history(self, symbol: str, start: str, end: str) -> list[PriceHistoryPoint]:
        self._ensure_api_key()
        raise ExternalProviderError(f"{self.provider_display_name} is not implemented yet")

    def get_company_profile(self, symbol: str) -> CompanyProfile:
        self._ensure_api_key()
        raise ExternalProviderError(f"{self.provider_display_name} is not implemented yet")

    def get_fx_rate(self, from_currency: str, to_currency: str) -> FxRate:
        self._ensure_api_key()
        raise ExternalProviderError(f"{self.provider_display_name} is not implemented yet")

    def _ensure_api_key(self) -> None:
        if not self.api_key:
            raise ExternalProviderError(f"{self.provider_display_name} requires a backend API key")


class TwelveDataProvider(PlaceholderIndiaProvider):
    source = "twelve_data"
    provider_display_name = "Twelve Data Indian market data provider"
    api_key_setting = "twelve_data_api_key"


class AlphaVantageProvider(PlaceholderIndiaProvider):
    source = "alpha_vantage"
    provider_display_name = "Alpha Vantage Indian market data provider"
    api_key_setting = "alpha_vantage_api_key"


class MarketstackProvider(PlaceholderIndiaProvider):
    source = "marketstack"
    provider_display_name = "Marketstack Indian market data provider"
    api_key_setting = "marketstack_api_key"


class NseBseProvider(PlaceholderIndiaProvider):
    source = "nse_bse_future"
    provider_display_name = "Future NSE/BSE or TrueData provider"


class BrokerMarketDataProvider(PlaceholderIndiaProvider):
    source = "broker_future"
    provider_display_name = "Future broker market data provider"
