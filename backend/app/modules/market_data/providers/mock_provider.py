from datetime import UTC, date, datetime, timedelta
from hashlib import sha256

from app.modules.market_data.providers.base import MarketDataProvider
from app.modules.market_data.schemas import CompanyProfile, FxRate, PriceHistoryPoint, PriceQuote


MOCK_AS_OF = datetime(2026, 1, 1, tzinfo=UTC)


class MockProvider(MarketDataProvider):
    source = "mock"
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
            currency="USD",
            source=self.source,
            as_of=MOCK_AS_OF,
            is_realtime=False,
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
                    currency="USD",
                    source=self.source,
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
            currency="USD",
            sector="Unknown",
            asset_class="equity",
            exchange=None,
            source=self.source,
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
