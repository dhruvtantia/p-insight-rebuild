from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import ValidationAppError
from app.db.models import Holding, User
from app.modules.common.data_status import DataStatus
from app.modules.fundamentals.providers.base import FundamentalsProvider
from app.modules.fundamentals.providers.mock_fundamentals import MockFundamentalsProvider
from app.modules.fundamentals.schemas import (
    FUNDAMENTAL_METRIC_NAMES,
    FundamentalMetrics,
    FundamentalsResponse,
    PortfolioFundamentalsCoverage,
    PortfolioFundamentalsResponse,
)
from app.modules.portfolios.service import PortfolioService


WEIGHTED_AVERAGE_METRICS = tuple(name for name in FUNDAMENTAL_METRIC_NAMES if name != "market_cap")


class FundamentalsService:
    def __init__(self, db: Session | None = None, provider: FundamentalsProvider | None = None):
        self.db = db
        self.provider = provider or self._build_provider()
        self.portfolio_service = PortfolioService(db) if db is not None else None

    def get_fundamentals(self, *, symbol: str) -> FundamentalsResponse:
        try:
            return self.provider.get_fundamentals(symbol)
        except ValueError as exc:
            raise ValidationAppError("Symbol cannot be empty") from exc

    def get_portfolio_fundamentals(self, *, portfolio_id: str, user: User) -> PortfolioFundamentalsResponse:
        if self.db is None or self.portfolio_service is None:
            raise ValidationAppError("Database session is required for portfolio fundamentals")

        portfolio = self.portfolio_service.get_portfolio(portfolio_id=portfolio_id, user=user)
        holdings = self._list_holdings(portfolio_id=portfolio.id)
        fundamentals = [self.get_fundamentals(symbol=holding.symbol) for holding in holdings]
        weights = self._market_value_weights(holdings)
        covered_symbols = [
            response.symbol
            for response in fundamentals
            if response.coverage.available_metrics
        ]
        missing_symbols = [
            response.symbol
            for response in fundamentals
            if not response.coverage.available_metrics
        ]
        weighted_metrics = self._weighted_metrics(fundamentals=fundamentals, weights=weights)
        total_symbols = len(fundamentals)
        total_weight = sum(weights.values())
        covered_weight = sum(weights.get(symbol, 0) for symbol in covered_symbols)
        warnings = self._warnings(
            holdings=holdings,
            missing_symbols=missing_symbols,
            total_weight=total_weight,
        )

        return PortfolioFundamentalsResponse(
            portfolio_id=portfolio.id,
            fundamentals=fundamentals,
            weighted_metrics=weighted_metrics,
            coverage=PortfolioFundamentalsCoverage(
                covered_symbols=covered_symbols,
                missing_symbols=missing_symbols,
                coverage_percent=round((len(covered_symbols) / total_symbols) * 100, 6) if total_symbols else 0,
                weighted_coverage_percent=round(covered_weight * 100, 6) if total_weight > 0 else 0,
            ),
            missing_symbols=missing_symbols,
            data_status=self._portfolio_data_status(fundamentals=fundamentals),
            warnings=warnings,
        )

    def _build_provider(self) -> FundamentalsProvider:
        settings = get_settings()
        self._ensure_mock_fundamentals_allowed(settings=settings)
        return MockFundamentalsProvider()

    def _ensure_mock_fundamentals_allowed(self, *, settings) -> None:
        if settings.normalized_app_env not in {"local", "test", "demo", "development"}:
            raise ValidationAppError(
                "Mock fundamentals are disabled outside local/test/demo environments. Connect a live fundamentals provider before enabling this in production."
            )

    def _list_holdings(self, *, portfolio_id: str) -> list[Holding]:
        if self.db is None:
            return []
        statement = select(Holding).where(Holding.portfolio_id == portfolio_id).order_by(Holding.symbol.asc())
        return list(self.db.scalars(statement).all())

    def _market_value_weights(self, holdings: list[Holding]) -> dict[str, float]:
        values = {
            holding.symbol: (
                float(holding.quantity) * float(holding.current_price)
                if holding.current_price is not None
                else 0
            )
            for holding in holdings
        }
        total_value = sum(values.values())
        if total_value <= 0:
            return {}
        return {symbol: value / total_value for symbol, value in values.items()}

    def _weighted_metrics(
        self,
        *,
        fundamentals: list[FundamentalsResponse],
        weights: dict[str, float],
    ) -> FundamentalMetrics:
        values: dict[str, float | None] = {}
        for metric_name in WEIGHTED_AVERAGE_METRICS:
            weighted_value = self._weighted_average_metric(
                fundamentals=fundamentals,
                weights=weights,
                metric_name=metric_name,
            )
            values[metric_name] = round(weighted_value, 6) if weighted_value is not None else None

        market_cap = sum(
            response.metrics.market_cap
            for response in fundamentals
            if response.metrics.market_cap is not None and response.coverage.available_metrics
        )
        values["market_cap"] = round(market_cap, 6) if market_cap > 0 else None
        return FundamentalMetrics(**values)

    def _weighted_average_metric(
        self,
        *,
        fundamentals: list[FundamentalsResponse],
        weights: dict[str, float],
        metric_name: str,
    ) -> float | None:
        numerator = 0.0
        denominator = 0.0
        for response in fundamentals:
            metric_value = getattr(response.metrics, metric_name)
            weight = weights.get(response.symbol, 0)
            if metric_value is None or weight <= 0:
                continue
            numerator += float(metric_value) * weight
            denominator += weight
        if denominator <= 0:
            return None
        return numerator / denominator

    def _portfolio_data_status(self, *, fundamentals: list[FundamentalsResponse]):
        if not fundamentals:
            return DataStatus.unavailable_source(
                provider=self.provider.source,
                warning="No holdings are available for portfolio fundamentals.",
            )
        if any(response.data_status.source == "mock" for response in fundamentals):
            status = fundamentals[0].data_status
            missing = [response.symbol for response in fundamentals if not response.coverage.available_metrics]
            if missing:
                return status.model_copy(
                    update={"warning": f"Fundamentals coverage is missing for: {', '.join(missing)}."}
                )
            return status
        return fundamentals[0].data_status

    def _warnings(self, *, holdings: list[Holding], missing_symbols: list[str], total_weight: float) -> list[str]:
        warnings: list[str] = []
        if not holdings:
            warnings.append("No holdings are available for portfolio fundamentals.")
        if missing_symbols:
            warnings.append(f"Fundamentals coverage is missing for: {', '.join(missing_symbols)}.")
        if total_weight <= 0 and holdings:
            warnings.append("Weighted portfolio metrics are unavailable because holdings do not have current prices.")
        return warnings
