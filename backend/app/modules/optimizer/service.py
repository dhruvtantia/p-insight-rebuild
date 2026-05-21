from datetime import UTC, datetime
from math import sqrt

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Holding, User
from app.modules.common.data_status import DataStatus
from app.modules.market_data.history_schemas import HistoricalPriceResponse
from app.modules.market_data.history_service import MarketHistoryService
from app.modules.optimizer.schemas import (
    EfficientFrontierPoint,
    OptimizedWeights,
    OptimizerMetricSet,
    OptimizerRequest,
    OptimizerResponse,
)
from app.modules.portfolios.service import PortfolioService


TRADING_DAYS_PER_YEAR = 252


class OptimizerService:
    def __init__(self, db: Session, history_service: MarketHistoryService | None = None):
        self.db = db
        self.portfolio_service = PortfolioService(db)
        self.history_service = history_service or MarketHistoryService()

    def optimize(self, *, portfolio_id: str, user: User, data: OptimizerRequest) -> OptimizerResponse:
        portfolio = self.portfolio_service.get_portfolio(portfolio_id=portfolio_id, user=user)
        holdings = self._list_holdings(portfolio_id=portfolio.id)
        symbols = sorted({holding.symbol for holding in holdings})
        warnings = ["Optimizer uses historical estimates only and is not investment advice."]

        if len(symbols) < 2:
            warnings.append("At least two holdings are required for optimizer scenarios.")
            return self._insufficient_response(
                portfolio_id=portfolio.id,
                period=data.period,
                warnings=warnings,
                data_status=DataStatus.unavailable_source(
                    provider="historical_market_data",
                    warning="Insufficient holdings for optimization.",
                ),
            )

        history = self.history_service.build_mock_response(symbols=symbols, period=data.period)
        returns_by_symbol = self._aligned_returns(history)
        if len(returns_by_symbol) < 2 or not returns_by_symbol or min(len(values) for values in returns_by_symbol.values()) < 2:
            warnings.append("At least two aligned historical return observations are required.")
            return self._insufficient_response(
                portfolio_id=portfolio.id,
                period=history.period,
                warnings=warnings,
                data_status=history.data_status,
            )

        symbols = sorted(returns_by_symbol)
        mean_returns = self._annualized_mean_returns(returns_by_symbol)
        covariance = self._annualized_covariance(returns_by_symbol, symbols=symbols)
        current_weights = self._current_weights(holdings=holdings, symbols=symbols)
        if not current_weights:
            warnings.append("Current portfolio metrics are unavailable because holdings do not have current prices.")

        min_variance_weights = self._min_variance_weights(covariance=covariance, symbols=symbols)
        max_sharpe_weights = self._max_sharpe_weights(
            mean_returns=mean_returns,
            covariance=covariance,
            symbols=symbols,
        )

        return OptimizerResponse(
            portfolio_id=portfolio.id,
            period=history.period,
            generated_at=datetime.now(UTC),
            status="ok",
            current_portfolio_metrics=self._portfolio_metrics(
                weights=current_weights,
                mean_returns=mean_returns,
                covariance=covariance,
                symbols=symbols,
            ),
            current_weights=current_weights,
            min_variance_target_weights=OptimizedWeights(
                target_weights=min_variance_weights,
                metrics=self._portfolio_metrics(
                    weights=min_variance_weights,
                    mean_returns=mean_returns,
                    covariance=covariance,
                    symbols=symbols,
                ),
            ),
            max_sharpe_target_weights=OptimizedWeights(
                target_weights=max_sharpe_weights,
                metrics=self._portfolio_metrics(
                    weights=max_sharpe_weights,
                    mean_returns=mean_returns,
                    covariance=covariance,
                    symbols=symbols,
                ),
            ),
            efficient_frontier_points=self._efficient_frontier_points(
                min_variance_weights=min_variance_weights,
                max_sharpe_weights=max_sharpe_weights,
                mean_returns=mean_returns,
                covariance=covariance,
                symbols=symbols,
                count=data.frontier_points,
            ),
            data_status=history.data_status,
            warnings=warnings,
        )

    def _insufficient_response(
        self,
        *,
        portfolio_id: str,
        period: str,
        warnings: list[str],
        data_status: DataStatus,
    ) -> OptimizerResponse:
        empty = OptimizedWeights(target_weights={}, metrics=OptimizerMetricSet())
        return OptimizerResponse(
            portfolio_id=portfolio_id,
            period=period,  # type: ignore[arg-type]
            generated_at=datetime.now(UTC),
            status="insufficient_history",
            current_portfolio_metrics=OptimizerMetricSet(),
            current_weights={},
            min_variance_target_weights=empty,
            max_sharpe_target_weights=empty,
            efficient_frontier_points=[],
            data_status=data_status,
            warnings=warnings,
        )

    def _list_holdings(self, *, portfolio_id: str) -> list[Holding]:
        statement = select(Holding).where(Holding.portfolio_id == portfolio_id).order_by(Holding.symbol.asc())
        return list(self.db.scalars(statement).all())

    def _aligned_returns(self, history: HistoricalPriceResponse) -> dict[str, list[float]]:
        prices_by_symbol = {
            series.symbol: {point.date: float(point.close) for point in series.prices if point.close > 0}
            for series in history.series
        }
        if not prices_by_symbol:
            return {}
        common_dates = set.intersection(*(set(prices) for prices in prices_by_symbol.values()))
        if len(common_dates) < 3:
            return {}

        ordered_dates = sorted(common_dates)
        returns_by_symbol: dict[str, list[float]] = {}
        for symbol, prices in prices_by_symbol.items():
            returns: list[float] = []
            for previous_date, current_date in zip(ordered_dates, ordered_dates[1:], strict=False):
                previous_price = prices[previous_date]
                current_price = prices[current_date]
                returns.append((current_price / previous_price) - 1)
            returns_by_symbol[symbol] = returns
        return returns_by_symbol

    def _annualized_mean_returns(self, returns_by_symbol: dict[str, list[float]]) -> dict[str, float]:
        return {
            symbol: round((sum(returns) / len(returns)) * TRADING_DAYS_PER_YEAR, 12)
            for symbol, returns in returns_by_symbol.items()
            if returns
        }

    def _annualized_covariance(
        self,
        returns_by_symbol: dict[str, list[float]],
        *,
        symbols: list[str],
    ) -> dict[str, dict[str, float]]:
        means = {symbol: sum(returns_by_symbol[symbol]) / len(returns_by_symbol[symbol]) for symbol in symbols}
        observation_count = min(len(returns_by_symbol[symbol]) for symbol in symbols)
        covariance: dict[str, dict[str, float]] = {}
        for symbol_a in symbols:
            covariance[symbol_a] = {}
            for symbol_b in symbols:
                numerator = sum(
                    (returns_by_symbol[symbol_a][index] - means[symbol_a])
                    * (returns_by_symbol[symbol_b][index] - means[symbol_b])
                    for index in range(observation_count)
                )
                value = numerator / (observation_count - 1) if observation_count > 1 else 0
                covariance[symbol_a][symbol_b] = value * TRADING_DAYS_PER_YEAR
        return covariance

    def _current_weights(self, *, holdings: list[Holding], symbols: list[str]) -> dict[str, float]:
        values = {
            holding.symbol: (
                float(holding.quantity) * float(holding.current_price)
                if holding.current_price is not None
                else 0
            )
            for holding in holdings
            if holding.symbol in symbols
        }
        total_value = sum(values.values())
        if total_value <= 0:
            return {}
        return {symbol: round(values.get(symbol, 0) / total_value, 6) for symbol in symbols}

    def _min_variance_weights(
        self,
        *,
        covariance: dict[str, dict[str, float]],
        symbols: list[str],
    ) -> dict[str, float]:
        inverse_variances = {
            symbol: 1 / covariance[symbol][symbol] if covariance[symbol][symbol] > 0 else 0
            for symbol in symbols
        }
        return self._normalize_weights(inverse_variances, symbols=symbols)

    def _max_sharpe_weights(
        self,
        *,
        mean_returns: dict[str, float],
        covariance: dict[str, dict[str, float]],
        symbols: list[str],
    ) -> dict[str, float]:
        scores = {
            symbol: max(mean_returns.get(symbol, 0), 0) / covariance[symbol][symbol]
            if covariance[symbol][symbol] > 0
            else 0
            for symbol in symbols
        }
        return self._normalize_weights(scores, symbols=symbols)

    def _normalize_weights(self, values: dict[str, float], *, symbols: list[str]) -> dict[str, float]:
        total = sum(value for value in values.values() if value > 0)
        if total <= 0:
            equal_weight = round(1 / len(symbols), 6) if symbols else 0
            return {symbol: equal_weight for symbol in symbols}
        weights = {symbol: round(max(values.get(symbol, 0), 0) / total, 6) for symbol in symbols}
        return self._rebalance_rounding(weights)

    def _rebalance_rounding(self, weights: dict[str, float]) -> dict[str, float]:
        if not weights:
            return {}
        total = round(sum(weights.values()), 6)
        if total == 1:
            return weights
        first_symbol = sorted(weights)[0]
        weights[first_symbol] = round(weights[first_symbol] + (1 - total), 6)
        return weights

    def _portfolio_metrics(
        self,
        *,
        weights: dict[str, float],
        mean_returns: dict[str, float],
        covariance: dict[str, dict[str, float]],
        symbols: list[str],
    ) -> OptimizerMetricSet:
        if not weights:
            return OptimizerMetricSet()
        expected_return = sum(weights.get(symbol, 0) * mean_returns.get(symbol, 0) for symbol in symbols)
        variance = sum(
            weights.get(symbol_a, 0) * weights.get(symbol_b, 0) * covariance[symbol_a][symbol_b]
            for symbol_a in symbols
            for symbol_b in symbols
        )
        volatility = sqrt(max(variance, 0))
        sharpe = expected_return / volatility if volatility > 0 else None
        return OptimizerMetricSet(
            expected_annual_return=round(expected_return, 6),
            annualized_volatility=round(volatility, 6),
            sharpe_ratio=round(sharpe, 6) if sharpe is not None else None,
        )

    def _efficient_frontier_points(
        self,
        *,
        min_variance_weights: dict[str, float],
        max_sharpe_weights: dict[str, float],
        mean_returns: dict[str, float],
        covariance: dict[str, dict[str, float]],
        symbols: list[str],
        count: int,
    ) -> list[EfficientFrontierPoint]:
        points: list[EfficientFrontierPoint] = []
        for index in range(count):
            blend = index / (count - 1) if count > 1 else 0
            weights = {
                symbol: round(
                    min_variance_weights.get(symbol, 0) * (1 - blend)
                    + max_sharpe_weights.get(symbol, 0) * blend,
                    6,
                )
                for symbol in symbols
            }
            weights = self._rebalance_rounding(weights)
            metrics = self._portfolio_metrics(
                weights=weights,
                mean_returns=mean_returns,
                covariance=covariance,
                symbols=symbols,
            )
            points.append(
                EfficientFrontierPoint(
                    index=index,
                    target_return=metrics.expected_annual_return,
                    annualized_volatility=metrics.annualized_volatility,
                    sharpe_ratio=metrics.sharpe_ratio,
                    weights=weights,
                )
            )
        return points
