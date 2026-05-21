from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Holding, User
from app.modules.common.data_status import DataStatus
from app.modules.market_data.history_schemas import HistoricalPriceResponse
from app.modules.market_data.history_service import MarketHistoryService
from app.modules.market_data.symbols import normalize_benchmark_symbol
from app.modules.performance.schemas import (
    NormalizedReturnPoint,
    PortfolioPerformanceHistory,
    PortfolioValuePoint,
)
from app.modules.portfolios.service import PortfolioService


class PerformanceService:
    def __init__(self, db: Session, history_service: MarketHistoryService | None = None):
        self.db = db
        self.history_service = history_service or MarketHistoryService()
        self.portfolio_service = PortfolioService(db)

    def get_history(
        self,
        *,
        portfolio_id: str,
        user: User,
        period: str = "1Y",
        benchmark_symbol: str | None = None,
        end_date: date | None = None,
    ) -> PortfolioPerformanceHistory:
        portfolio = self.portfolio_service.get_portfolio(portfolio_id=portfolio_id, user=user)
        normalized_period = self.history_service.validate_period(period)
        resolved_end = end_date or datetime.now(UTC).date()
        start_date = self.history_service.resolve_start_date(period=normalized_period, end_date=resolved_end)
        benchmark = normalize_benchmark_symbol(benchmark_symbol or portfolio.benchmark_symbol or "NIFTY50") or "NIFTY50"
        holdings = self._list_holdings(portfolio_id=portfolio.id)

        if not holdings:
            return self._empty_response(
                portfolio_id=portfolio.id,
                period=normalized_period,
                start_date=start_date,
                end_date=resolved_end,
                base_currency=portfolio.base_currency,
                benchmark_symbol=benchmark,
                data_status=DataStatus.unavailable_source(
                    provider="historical_market_data",
                    warning="No holdings are available for synthetic performance history.",
                ),
            )

        history = self._fetch_history(
            symbols=[holding.symbol for holding in holdings] + [benchmark],
            period=normalized_period,
            end_date=resolved_end,
        )
        prices_by_symbol = self._prices_by_symbol(history)
        holding_symbols = sorted({holding.symbol for holding in holdings})
        missing_price_symbols = sorted(symbol for symbol in holding_symbols if not prices_by_symbol.get(symbol))
        benchmark_returns = self._normalized_returns(prices_by_symbol.get(benchmark, {}))
        data_status = history.data_status

        if missing_price_symbols:
            data_status = data_status.model_copy(
                update={
                    "warning": (
                        "Synthetic performance history is unavailable because historical prices are missing for: "
                        f"{', '.join(missing_price_symbols)}."
                    )
                }
            )
            return PortfolioPerformanceHistory(
                portfolio_id=portfolio.id,
                period=normalized_period,
                start_date=history.start_date,
                end_date=history.end_date,
                generated_at=datetime.now(UTC),
                base_currency=portfolio.base_currency,
                benchmark_symbol=benchmark,
                benchmark_normalized_return_series=benchmark_returns,
                missing_price_symbols=missing_price_symbols,
                data_status=data_status,
            )

        portfolio_values = self._portfolio_values(holdings=holdings, prices_by_symbol=prices_by_symbol)
        portfolio_returns = self._normalized_returns({point.date: point.value for point in portfolio_values})

        return PortfolioPerformanceHistory(
            portfolio_id=portfolio.id,
            period=normalized_period,
            start_date=history.start_date,
            end_date=history.end_date,
            generated_at=datetime.now(UTC),
            base_currency=portfolio.base_currency,
            benchmark_symbol=benchmark,
            portfolio_value_series=portfolio_values,
            portfolio_normalized_return_series=portfolio_returns,
            benchmark_normalized_return_series=benchmark_returns,
            missing_price_symbols=missing_price_symbols,
            data_status=data_status,
        )

    def _empty_response(
        self,
        *,
        portfolio_id: str,
        period: str,
        start_date: date,
        end_date: date,
        base_currency: str,
        benchmark_symbol: str,
        data_status: DataStatus,
    ) -> PortfolioPerformanceHistory:
        return PortfolioPerformanceHistory(
            portfolio_id=portfolio_id,
            period=period,  # type: ignore[arg-type]
            start_date=start_date,
            end_date=end_date,
            generated_at=datetime.now(UTC),
            base_currency=base_currency,
            benchmark_symbol=benchmark_symbol,
            data_status=data_status,
        )

    def _fetch_history(
        self,
        *,
        symbols: list[str],
        period: str,
        end_date: date,
    ) -> HistoricalPriceResponse:
        return self.history_service.build_mock_response(
            symbols=symbols,
            period=period,
            end_date=end_date,
        )

    def _list_holdings(self, *, portfolio_id: str) -> list[Holding]:
        statement = select(Holding).where(Holding.portfolio_id == portfolio_id).order_by(Holding.symbol.asc())
        return list(self.db.scalars(statement).all())

    def _prices_by_symbol(self, history: HistoricalPriceResponse) -> dict[str, dict[date, float]]:
        return {
            series.symbol: {point.date: float(point.close) for point in series.prices}
            for series in history.series
        }

    def _portfolio_values(
        self,
        *,
        holdings: list[Holding],
        prices_by_symbol: dict[str, dict[date, float]],
    ) -> list[PortfolioValuePoint]:
        common_dates: set[date] | None = None
        for holding in holdings:
            holding_dates = set(prices_by_symbol.get(holding.symbol, {}))
            common_dates = holding_dates if common_dates is None else common_dates & holding_dates

        if not common_dates:
            return []

        currency = holdings[0].currency if holdings else "INR"
        values: list[PortfolioValuePoint] = []
        for price_date in sorted(common_dates):
            total_value = sum(
                float(holding.quantity) * prices_by_symbol[holding.symbol][price_date]
                for holding in holdings
            )
            values.append(
                PortfolioValuePoint(
                    date=price_date,
                    value=round(total_value, 6),
                    currency=currency,
                )
            )
        return values

    def _normalized_returns(self, values_by_date: dict[date, float]) -> list[NormalizedReturnPoint]:
        ordered_values = [(value_date, value) for value_date, value in sorted(values_by_date.items()) if value > 0]
        if not ordered_values:
            return []

        base_value = ordered_values[0][1]
        if base_value <= 0:
            return []

        return [
            NormalizedReturnPoint(
                date=value_date,
                normalized_return=round((value / base_value) - 1, 6),
            )
            for value_date, value in ordered_values
        ]
