from abc import ABC, abstractmethod

from app.modules.market_data.schemas import CompanyProfile, FxRate, PriceHistoryPoint, PriceQuote


class MarketDataProvider(ABC):
    @abstractmethod
    def get_latest_price(self, symbol: str) -> PriceQuote:
        raise NotImplementedError

    @abstractmethod
    def get_batch_prices(self, symbols: list[str]) -> list[PriceQuote]:
        raise NotImplementedError

    @abstractmethod
    def get_price_history(self, symbol: str, start: str, end: str) -> list[PriceHistoryPoint]:
        raise NotImplementedError

    @abstractmethod
    def get_company_profile(self, symbol: str) -> CompanyProfile:
        raise NotImplementedError

    @abstractmethod
    def get_fx_rate(self, from_currency: str, to_currency: str) -> FxRate:
        raise NotImplementedError
