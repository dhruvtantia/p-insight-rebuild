from app.core.config import get_settings
from app.core.errors import ExternalProviderError
from app.modules.market_data.providers.base import MarketDataProvider
from app.modules.market_data.schemas import CompanyProfile, FxRate, PriceHistoryPoint, PriceQuote


class FmpProvider(MarketDataProvider):
    source = "fmp"

    def __init__(self, api_key: str | None = None):
        settings = get_settings()
        self.api_key = api_key or settings.fmp_api_key or settings.market_data_api_key

    def get_latest_price(self, symbol: str) -> PriceQuote:
        self._ensure_api_key()
        raise ExternalProviderError("FMP market data provider is not implemented yet")

    def get_batch_prices(self, symbols: list[str]) -> list[PriceQuote]:
        self._ensure_api_key()
        raise ExternalProviderError("FMP market data provider is not implemented yet")

    def get_price_history(self, symbol: str, start: str, end: str) -> list[PriceHistoryPoint]:
        self._ensure_api_key()
        raise ExternalProviderError("FMP market data provider is not implemented yet")

    def get_company_profile(self, symbol: str) -> CompanyProfile:
        self._ensure_api_key()
        raise ExternalProviderError("FMP market data provider is not implemented yet")

    def get_fx_rate(self, from_currency: str, to_currency: str) -> FxRate:
        self._ensure_api_key()
        raise ExternalProviderError("FMP market data provider is not implemented yet")

    def _ensure_api_key(self) -> None:
        if not self.api_key:
            raise ExternalProviderError("FMP market data provider requires FMP_API_KEY or MARKET_DATA_API_KEY")
