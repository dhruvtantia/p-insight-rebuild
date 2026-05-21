from datetime import UTC, datetime
from statistics import mean

from sqlalchemy.orm import Session

from app.db.models import User
from app.modules.analytics.calculators.risk_v2.beta import calculate_beta
from app.modules.analytics.calculators.risk_v2.correlation import calculate_correlation
from app.modules.analytics.calculators.risk_v2.drawdown import calculate_max_drawdown
from app.modules.analytics.calculators.risk_v2.returns import calculate_simple_returns
from app.modules.analytics.calculators.risk_v2.sharpe import calculate_sharpe_ratio
from app.modules.analytics.calculators.risk_v2.sortino import (
    calculate_downside_deviation,
    calculate_sortino_ratio,
)
from app.modules.analytics.calculators.risk_v2.tracking_error import calculate_tracking_error
from app.modules.analytics.calculators.risk_v2.var import calculate_historical_var
from app.modules.analytics.calculators.risk_v2.volatility import calculate_volatility
from app.modules.performance.schemas import PortfolioPerformanceHistory
from app.modules.performance.service import PerformanceService
from app.modules.risk.schemas import RiskMetricStatus, RiskV2Response

TRADING_DAYS_PER_YEAR = 252


class RiskV2Service:
    def __init__(self, db: Session, performance_service: PerformanceService | None = None):
        self.performance_service = performance_service or PerformanceService(db)

    def get_risk(self, *, portfolio_id: str, user: User, period: str = "1Y") -> RiskV2Response:
        performance = self.performance_service.get_history(
            portfolio_id=portfolio_id,
            user=user,
            period=period,
        )
        portfolio_values = [point.value for point in performance.portfolio_value_series]
        portfolio_returns = calculate_simple_returns(portfolio_values)
        benchmark_returns = calculate_simple_returns(
            [1 + point.normalized_return for point in performance.benchmark_normalized_return_series]
        )
        portfolio_returns, benchmark_returns = self._align_return_lengths(portfolio_returns, benchmark_returns)

        annualized_return = self._annualized_return(portfolio_values)
        annualized_volatility = calculate_volatility(portfolio_returns, annualization_factor=TRADING_DAYS_PER_YEAR)
        sharpe_ratio = calculate_sharpe_ratio(portfolio_returns, annualization_factor=TRADING_DAYS_PER_YEAR)
        sortino_ratio = calculate_sortino_ratio(portfolio_returns, annualization_factor=TRADING_DAYS_PER_YEAR)
        max_drawdown = calculate_max_drawdown(portfolio_values)
        downside_deviation = calculate_downside_deviation(portfolio_returns, annualization_factor=TRADING_DAYS_PER_YEAR)
        value_at_risk_95 = calculate_historical_var(portfolio_returns, confidence_level=0.95)
        beta_vs_benchmark = calculate_beta(portfolio_returns, benchmark_returns)
        tracking_error = calculate_tracking_error(
            portfolio_returns,
            benchmark_returns,
            annualization_factor=TRADING_DAYS_PER_YEAR,
        )
        information_ratio = self._information_ratio(portfolio_returns, benchmark_returns, tracking_error)
        correlation = calculate_correlation(portfolio_returns, benchmark_returns)
        correlation_matrix = self._correlation_matrix(correlation)

        metric_values = {
            "annualized_return": annualized_return,
            "annualized_volatility": annualized_volatility,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "max_drawdown": max_drawdown,
            "downside_deviation": downside_deviation,
            "value_at_risk_95": value_at_risk_95,
            "beta_vs_benchmark": beta_vs_benchmark,
            "tracking_error": tracking_error,
            "information_ratio": information_ratio,
            "correlation_matrix": correlation_matrix,
        }

        return RiskV2Response(
            portfolio_id=performance.portfolio_id,
            period=performance.period,
            generated_at=datetime.now(UTC),
            benchmark_symbol=performance.benchmark_symbol,
            observations=len(portfolio_returns),
            annualized_return=self._round_metric(annualized_return),
            annualized_volatility=self._round_metric(annualized_volatility),
            sharpe_ratio=self._round_metric(sharpe_ratio),
            sortino_ratio=self._round_metric(sortino_ratio),
            max_drawdown=self._round_metric(max_drawdown),
            downside_deviation=self._round_metric(downside_deviation),
            value_at_risk_95=self._round_metric(value_at_risk_95),
            beta_vs_benchmark=self._round_metric(beta_vs_benchmark),
            tracking_error=self._round_metric(tracking_error),
            information_ratio=self._round_metric(information_ratio),
            correlation_matrix=self._round_correlation_matrix(correlation_matrix),
            metric_status=self._metric_statuses(
                metric_values=metric_values,
                performance=performance,
                portfolio_returns=portfolio_returns,
                benchmark_returns=benchmark_returns,
            ),
            assumptions=performance.assumptions,
            data_status=performance.data_status,
        )

    def _annualized_return(self, values: list[float]) -> float | None:
        if len(values) < 2:
            return None
        start_value = float(values[0])
        end_value = float(values[-1])
        periods = len(values) - 1
        if start_value <= 0 or periods <= 0:
            return None
        return (end_value / start_value) ** (TRADING_DAYS_PER_YEAR / periods) - 1

    def _align_return_lengths(
        self,
        portfolio_returns: list[float],
        benchmark_returns: list[float],
    ) -> tuple[list[float], list[float]]:
        aligned_length = min(len(portfolio_returns), len(benchmark_returns))
        if aligned_length == 0:
            return [], []
        return portfolio_returns[-aligned_length:], benchmark_returns[-aligned_length:]

    def _information_ratio(
        self,
        portfolio_returns: list[float],
        benchmark_returns: list[float],
        tracking_error: float | None,
    ) -> float | None:
        if len(portfolio_returns) < 2 or len(benchmark_returns) < 2 or tracking_error is None or tracking_error == 0:
            return None
        active_returns = [
            portfolio_return - benchmark_return
            for portfolio_return, benchmark_return in zip(portfolio_returns, benchmark_returns, strict=False)
        ]
        return (mean(active_returns) * TRADING_DAYS_PER_YEAR) / tracking_error

    def _correlation_matrix(self, correlation: float | None) -> dict[str, dict[str, float | None]] | None:
        if correlation is None:
            return None
        return {
            "portfolio": {"portfolio": 1.0, "benchmark": correlation},
            "benchmark": {"portfolio": correlation, "benchmark": 1.0},
        }

    def _metric_statuses(
        self,
        *,
        metric_values: dict[str, object],
        performance: PortfolioPerformanceHistory,
        portfolio_returns: list[float],
        benchmark_returns: list[float],
    ) -> dict[str, RiskMetricStatus]:
        statuses: dict[str, RiskMetricStatus] = {}
        for metric_name, value in metric_values.items():
            statuses[metric_name] = self._metric_status(
                metric_name=metric_name,
                value=value,
                performance=performance,
                portfolio_returns=portfolio_returns,
                benchmark_returns=benchmark_returns,
            )
        return statuses

    def _metric_status(
        self,
        *,
        metric_name: str,
        value: object,
        performance: PortfolioPerformanceHistory,
        portfolio_returns: list[float],
        benchmark_returns: list[float],
    ) -> RiskMetricStatus:
        if value is not None:
            return RiskMetricStatus(status="ok", message="Metric calculated from synthetic performance history.")
        if performance.missing_price_symbols:
            return RiskMetricStatus(
                status="insufficient_history",
                message="Historical prices are missing for one or more current holdings.",
            )
        if len(portfolio_returns) < 2:
            return RiskMetricStatus(
                status="insufficient_history",
                message="At least two portfolio return observations are required.",
            )
        if metric_name in {
            "beta_vs_benchmark",
            "tracking_error",
            "information_ratio",
            "correlation_matrix",
        } and len(benchmark_returns) < 2:
            return RiskMetricStatus(
                status="insufficient_history",
                message="At least two benchmark return observations are required.",
            )
        return RiskMetricStatus(
            status="undefined",
            message="Metric is undefined for zero-variance or flat return inputs.",
        )

    def _round_metric(self, value: float | None) -> float | None:
        return round(value, 6) if value is not None else None

    def _round_correlation_matrix(
        self,
        matrix: dict[str, dict[str, float | None]] | None,
    ) -> dict[str, dict[str, float | None]] | None:
        if matrix is None:
            return None
        return {
            row_name: {
                column_name: self._round_metric(value)
                for column_name, value in row.items()
            }
            for row_name, row in matrix.items()
        }
