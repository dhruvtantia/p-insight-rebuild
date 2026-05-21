from datetime import UTC, date, datetime, timedelta

from app.core.config import get_settings
from app.core.errors import ValidationAppError
from app.modules.common.data_status import DataStatus
from app.modules.demo.fixtures.historical_prices import (
    build_mock_historical_prices,
    mock_history_data_status,
)
from app.modules.market_data.history_schemas import (
    HistoricalPeriod,
    HistoricalPriceResponse,
    HistoricalPriceSeries,
)
from app.modules.market_data.symbols import normalize_market_symbol


PERIOD_DAYS: dict[HistoricalPeriod, int] = {
    "1M": 30,
    "3M": 90,
    "6M": 180,
    "1Y": 365,
    "5Y": 365 * 5,
}


class MarketHistoryService:
    """Historical market data contract surface.

    This service validates request shape and returns a stable empty response
    until a real historical provider is connected.
    """

    provider_name = "historical_market_data"

    def build_empty_response(
        self,
        *,
        symbols: list[str],
        period: str,
        end_date: date | None = None,
    ) -> HistoricalPriceResponse:
        normalized_period = self.validate_period(period)
        normalized_symbols = self.normalize_symbols(symbols)
        resolved_end = end_date or datetime.now(UTC).date()
        start_date = self.resolve_start_date(period=normalized_period, end_date=resolved_end)
        data_status = DataStatus.unavailable_source(
            provider=self.provider_name,
            warning="Historical market data retrieval is not implemented yet.",
        )

        return HistoricalPriceResponse(
            period=normalized_period,
            start_date=start_date,
            end_date=resolved_end,
            generated_at=datetime.now(UTC),
            series=[
                HistoricalPriceSeries(
                    symbol=symbol,
                    period=normalized_period,
                    currency="INR",
                    start_date=start_date,
                    end_date=resolved_end,
                    prices=[],
                    data_status=data_status,
                )
                for symbol in normalized_symbols
            ],
            data_status=data_status,
        )

    def build_mock_response(
        self,
        *,
        symbols: list[str],
        period: str,
        end_date: date | None = None,
    ) -> HistoricalPriceResponse:
        self._ensure_mock_history_allowed()
        normalized_period = self.validate_period(period)
        normalized_symbols = self.normalize_symbols(symbols)
        resolved_end = end_date or datetime.now(UTC).date()
        start_date = self.resolve_start_date(period=normalized_period, end_date=resolved_end)
        data_status = mock_history_data_status()

        return HistoricalPriceResponse(
            period=normalized_period,
            start_date=start_date,
            end_date=resolved_end,
            generated_at=datetime.now(UTC),
            series=[
                HistoricalPriceSeries(
                    symbol=symbol,
                    period=normalized_period,
                    currency="INR",
                    start_date=start_date,
                    end_date=resolved_end,
                    prices=build_mock_historical_prices(
                        symbol=symbol,
                        start_date=start_date,
                        end_date=resolved_end,
                        currency="INR",
                        data_status=data_status,
                    ),
                    data_status=data_status,
                )
                for symbol in normalized_symbols
            ],
            data_status=data_status,
        )

    def validate_period(self, period: str) -> HistoricalPeriod:
        normalized = period.strip().upper()
        if normalized not in PERIOD_DAYS:
            supported = ", ".join(PERIOD_DAYS)
            raise ValidationAppError(f"Unsupported history period '{period}'. Supported periods: {supported}")
        return normalized  # type: ignore[return-value]

    def normalize_symbols(self, symbols: list[str]) -> list[str]:
        normalized_symbols: list[str] = []
        seen: set[str] = set()
        for symbol in symbols:
            try:
                normalized = normalize_market_symbol(symbol).normalized_symbol
            except ValueError as exc:
                raise ValidationAppError("Symbol cannot be empty") from exc
            if normalized not in seen:
                seen.add(normalized)
                normalized_symbols.append(normalized)

        if not normalized_symbols:
            raise ValidationAppError("At least one symbol is required")
        return normalized_symbols

    def resolve_start_date(self, *, period: HistoricalPeriod, end_date: date) -> date:
        return end_date - timedelta(days=PERIOD_DAYS[period])

    def _ensure_mock_history_allowed(self) -> None:
        settings = get_settings()
        if settings.normalized_app_env == "production" and not settings.production_mock_market_data_allowed:
            raise ValidationAppError(
                "Mock historical market data is disabled in production. Set ALLOW_PRODUCTION_MOCK_MARKET_DATA=true only for explicit test/demo deployments."
            )
