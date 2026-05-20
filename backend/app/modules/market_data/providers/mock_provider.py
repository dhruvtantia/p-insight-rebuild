from datetime import UTC, date, datetime, timedelta
from hashlib import sha256

from app.modules.common.data_status import DataStatus
from app.modules.market_data.providers.base import MarketDataProvider
from app.modules.market_data.schemas import CompanyProfile, FxRate, PriceHistoryPoint, PriceQuote
from app.modules.market_data.symbols import normalize_india_symbol_for_provider, normalize_market_symbol


MOCK_AS_OF = datetime(2026, 1, 1, tzinfo=UTC)

class MockProvider(MarketDataProvider):
    source = "mock"
    currency = "USD"
    default_exchange: str | None = None
    common_prices: dict[str, float] = {
        "AAPL": 210.12,
        "MSFT": 425.44,
        "GOOGL": 174.83,
        "AMZN": 186.97,
        "TSLA": 243.18,
        "NVDA": 126.57,
        "SPY": 523.41,
        "VOO": 478.29,
        "QQQ": 449.75,
    }

    def get_latest_price(self, symbol: str) -> PriceQuote:
        normalized_symbol = self._normalize_symbol(symbol)
        return PriceQuote(
            symbol=normalized_symbol,
            price=self._price_for_symbol(normalized_symbol),
            currency=self.currency,
            source=self.source,
            as_of=MOCK_AS_OF,
            is_realtime=False,
            data_status=self._data_status(),
        )

    def get_batch_prices(self, symbols: list[str]) -> list[PriceQuote]:
        return [self.get_latest_price(symbol) for symbol in self._dedupe_symbols(symbols)]

    def get_price_history(self, symbol: str, start: str, end: str) -> list[PriceHistoryPoint]:
        normalized_symbol = self._normalize_symbol(symbol)
        start_date = date.fromisoformat(start)
        end_date = date.fromisoformat(end)
        if end_date < start_date:
            return []

        base_price = self._price_for_symbol(normalized_symbol)
        points: list[PriceHistoryPoint] = []
        current = start_date
        day_index = 0
        while current <= end_date:
            daily_offset = ((day_index % 11) - 5) * 0.0025
            points.append(
                PriceHistoryPoint(
                    symbol=normalized_symbol,
                    date=current.isoformat(),
                    close=round(base_price * (1 + daily_offset), 2),
                    currency=self.currency,
                    source=self.source,
                    data_status=self._data_status(),
                )
            )
            current += timedelta(days=1)
            day_index += 1
        return points

    def get_company_profile(self, symbol: str) -> CompanyProfile:
        normalized_symbol = self._normalize_symbol(symbol)
        return CompanyProfile(
            symbol=normalized_symbol,
            company_name=f"{normalized_symbol} Mock Company",
            currency=self.currency,
            sector="Unknown",
            asset_class="equity",
            exchange=self.default_exchange,
            source=self.source,
            data_status=self._data_status(),
        )

    def get_fx_rate(self, from_currency: str, to_currency: str) -> FxRate:
        normalized_from = from_currency.strip().upper()
        normalized_to = to_currency.strip().upper()
        rate = 1.0 if normalized_from == normalized_to else self._deterministic_fx_rate(normalized_from, normalized_to)
        return FxRate(
            from_currency=normalized_from,
            to_currency=normalized_to,
            rate=rate,
            source=self.source,
            as_of=MOCK_AS_OF,
            is_realtime=False,
            data_status=self._data_status(),
        )

    def _price_for_symbol(self, symbol: str) -> float:
        if symbol in self.common_prices:
            return self.common_prices[symbol]
        digest = sha256(symbol.encode("utf-8")).hexdigest()
        cents = 1_000 + int(digest[:8], 16) % 49_000
        return round(cents / 100, 2)

    def _deterministic_fx_rate(self, from_currency: str, to_currency: str) -> float:
        digest = sha256(f"{from_currency}:{to_currency}".encode("utf-8")).hexdigest()
        basis_points = 5_000 + int(digest[:8], 16) % 15_000
        return round(basis_points / 10_000, 4)

    def _dedupe_symbols(self, symbols: list[str]) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []
        for symbol in symbols:
            normalized_symbol = self._normalize_symbol(symbol)
            if normalized_symbol not in seen:
                seen.add(normalized_symbol)
                deduped.append(normalized_symbol)
        return deduped

    def _normalize_symbol(self, symbol: str) -> str:
        cleaned = symbol.strip().upper()
        if not cleaned:
            raise ValueError("Symbol cannot be empty")
        return cleaned

    def _data_status(self) -> DataStatus:
        return DataStatus.mock_source(provider=self.source, as_of=MOCK_AS_OF, is_realtime=False)


class MockProviderIndia(MockProvider):
    source = "mock_india"
    currency = "INR"
    default_exchange = "NSE"
    common_prices: dict[str, float] = {
        "RELIANCE.NS": 2842.15,
        "TCS.NS": 3925.8,
        "INFY.NS": 1518.4,
        "HDFCBANK.NS": 1642.25,
        "ICICIBANK.NS": 1088.35,
        "SBIN.NS": 742.5,
        "ITC.NS": 438.7,
        "LT.NS": 3560.1,
        "BHARTIARTL.NS": 1216.9,
        "KOTAKBANK.NS": 1712.45,
        "AXISBANK.NS": 1084.6,
        "MARUTI.NS": 11825.25,
        "SUNPHARMA.NS": 1512.3,
        "NIFTYBEES.NS": 246.55,
        "^NSEI": 22530.7,
        "^NSEBANK": 48075.2,
        "BSE:500325": 2840.4,
    }
    company_profiles: dict[str, dict[str, str]] = {
        "RELIANCE.NS": {"company_name": "Reliance Industries Ltd.", "sector": "Energy"},
        "TCS.NS": {"company_name": "Tata Consultancy Services Ltd.", "sector": "Information Technology"},
        "INFY.NS": {"company_name": "Infosys Ltd.", "sector": "Information Technology"},
        "HDFCBANK.NS": {"company_name": "HDFC Bank Ltd.", "sector": "Financial Services"},
        "ICICIBANK.NS": {"company_name": "ICICI Bank Ltd.", "sector": "Financial Services"},
        "SBIN.NS": {"company_name": "State Bank of India", "sector": "Financial Services"},
        "ITC.NS": {"company_name": "ITC Ltd.", "sector": "Consumer Staples"},
        "LT.NS": {"company_name": "Larsen & Toubro Ltd.", "sector": "Industrials"},
        "BHARTIARTL.NS": {"company_name": "Bharti Airtel Ltd.", "sector": "Communication Services"},
        "KOTAKBANK.NS": {"company_name": "Kotak Mahindra Bank Ltd.", "sector": "Financials"},
        "AXISBANK.NS": {"company_name": "Axis Bank Ltd.", "sector": "Financials"},
        "MARUTI.NS": {"company_name": "Maruti Suzuki India Ltd.", "sector": "Consumer Discretionary"},
        "SUNPHARMA.NS": {"company_name": "Sun Pharmaceutical Industries Ltd.", "sector": "Healthcare"},
        "NIFTYBEES.NS": {"company_name": "Nippon India ETF Nifty 50 BeES", "sector": "ETF"},
        "^NSEI": {"company_name": "NIFTY 50 Index", "sector": "Benchmark"},
        "^NSEBANK": {"company_name": "NIFTY Bank Index", "sector": "Benchmark"},
    }

    def get_company_profile(self, symbol: str) -> CompanyProfile:
        normalized_symbol = self._normalize_symbol(symbol)
        symbol_metadata = normalize_market_symbol(normalized_symbol)
        provider_symbol = symbol_metadata.provider_symbol
        profile = self.company_profiles.get(provider_symbol)
        return CompanyProfile(
            symbol=normalized_symbol,
            company_name=profile["company_name"] if profile else f"{normalized_symbol} Mock India Company",
            currency=self.currency,
            sector=profile["sector"] if profile else "Unknown",
            asset_class=symbol_metadata.asset_class,
            exchange=symbol_metadata.exchange,
            source=self.source,
            data_status=self._data_status(),
        )

    def _price_for_symbol(self, symbol: str) -> float:
        provider_symbol = normalize_india_symbol_for_provider(symbol)
        if provider_symbol in self.common_prices:
            return self.common_prices[provider_symbol]
        digest = sha256(provider_symbol.encode("utf-8")).hexdigest()
        paise = 10_000 + int(digest[:8], 16) % 490_000
        return round(paise / 100, 2)

    def _normalize_symbol(self, symbol: str) -> str:
        return normalize_market_symbol(symbol).normalized_symbol
