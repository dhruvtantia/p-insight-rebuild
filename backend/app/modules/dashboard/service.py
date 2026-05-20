from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AssetPrice, Holding, User
from app.modules.analytics.schemas import AllocationBucket, RuleInsight
from app.modules.analytics.service import AnalyticsService
from app.modules.common.data_status import DataStatus
from app.modules.dashboard.schemas import (
    DashboardActionItem,
    DashboardAllocationItem,
    DashboardBundleResponse,
    DashboardDataQuality,
    DashboardKpis,
    DashboardRiskSummary,
    DashboardTopHolding,
)
from app.modules.holdings.service import HoldingService
from app.modules.market_data.service import MarketDataService
from app.modules.portfolios.service import PortfolioService


class DashboardService:
    def __init__(self, db: Session, market_data_service: MarketDataService | None = None):
        self.db = db
        self.portfolio_service = PortfolioService(db)
        self.holding_service = HoldingService(db)
        self.analytics_service = AnalyticsService(db)
        self.market_data_service = market_data_service or MarketDataService(db)

    def get_bundle(self, *, portfolio_id: str, user: User) -> DashboardBundleResponse:
        portfolio = self.portfolio_service.get_portfolio(portfolio_id=portfolio_id, user=user)
        holdings = self.holding_service.list_holdings(portfolio_id=portfolio.id, user=user)
        analytics = self.analytics_service.build_bundle(portfolio_id=portfolio.id, user=user)

        missing_price_count = sum(1 for holding in holdings if holding.current_price is None)
        missing_cost_count = sum(1 for holding in holdings if holding.average_cost is None)
        data_status = self._build_data_status(holdings=holdings, missing_price_count=missing_price_count)
        sorted_priced_holdings = sorted(
            [holding for holding in analytics.summary.holdings if holding.market_value is not None],
            key=lambda holding: holding.market_value or 0,
            reverse=True,
        )

        return DashboardBundleResponse(
            portfolio_id=portfolio.id,
            generated_at=analytics.generated_at,
            kpis=DashboardKpis(
                portfolio_id=portfolio.id,
                base_currency=analytics.summary.base_currency,
                total_invested=analytics.summary.total_cost_basis,
                current_value=analytics.summary.total_portfolio_value,
                unrealized_pnl=analytics.summary.total_unrealized_gain_loss,
                return_percent=analytics.summary.total_unrealized_gain_loss_pct,
                holdings_count=len(holdings),
                priced_holdings_count=len(sorted_priced_holdings),
                largest_holding_symbol=analytics.summary.largest_holding.symbol
                if analytics.summary.largest_holding
                else None,
                largest_holding_weight=analytics.summary.largest_holding.weight
                if analytics.summary.largest_holding
                else None,
                cash_weight=None,
            ),
            sector_allocation=self._allocation_items(
                dimension="sector",
                buckets=analytics.allocation.sector_allocation,
            ),
            asset_allocation=self._allocation_items(
                dimension="asset_class",
                buckets=analytics.allocation.asset_allocation,
            ),
            top_holdings=[
                DashboardTopHolding(
                    holding_id=holding.holding_id,
                    symbol=holding.symbol,
                    market_value=holding.market_value or 0,
                    weight=holding.weight,
                    unrealized_gain_loss=holding.unrealized_gain_loss,
                    unrealized_gain_loss_pct=holding.unrealized_gain_loss_pct,
                    currency=holding.currency,
                )
                for holding in sorted_priced_holdings[:5]
            ],
            risk=DashboardRiskSummary(
                concentration_status=analytics.risk.concentration.status,
                largest_holding_symbol=analytics.risk.concentration.largest_holding.symbol
                if analytics.risk.concentration.largest_holding
                else None,
                largest_holding_weight=analytics.risk.concentration.largest_holding.weight
                if analytics.risk.concentration.largest_holding
                else None,
                top_3_weight=self._top_n_weight(sorted_priced_holdings, limit=3),
                hhi=self._hhi(sorted_priced_holdings),
                volatility=analytics.risk.volatility.value,
                volatility_status=analytics.risk.volatility.status,
                sharpe_ratio=analytics.risk.sharpe_ratio.value,
                sharpe_ratio_status=analytics.risk.sharpe_ratio.status,
                max_drawdown=analytics.risk.max_drawdown.value,
                max_drawdown_status=analytics.risk.max_drawdown.status,
                message=analytics.risk.concentration.message,
            ),
            data_quality=DashboardDataQuality(
                holdings_count=len(holdings),
                priced_holdings_count=len(sorted_priced_holdings),
                missing_price_count=missing_price_count,
                missing_cost_basis_count=missing_cost_count,
                stale_price_count=0,
                warnings=self._data_quality_warnings(
                    missing_price_count=missing_price_count,
                    missing_cost_count=missing_cost_count,
                ),
                data_status=data_status,
            ),
            action_items=[self._action_item_from_rule(rule) for rule in analytics.rules],
            data_status=data_status,
        )

    def _allocation_items(
        self,
        *,
        dimension: str,
        buckets: list[AllocationBucket],
    ) -> list[DashboardAllocationItem]:
        return [
            DashboardAllocationItem(
                dimension=dimension,  # type: ignore[arg-type]
                name=bucket.name,
                value=bucket.value,
                weight=bucket.weight,
                symbols=bucket.symbols,
            )
            for bucket in buckets
        ]

    def _build_data_status(self, *, holdings: list[Holding], missing_price_count: int) -> DataStatus:
        provider_name = self._provider_name()
        if not holdings:
            return DataStatus.unavailable_source(
                provider=provider_name,
                warning="No holdings are available for dashboard data.",
            )

        latest_price = self._latest_asset_price(holdings=holdings)
        if latest_price is None:
            if missing_price_count:
                return DataStatus.unavailable_source(
                    provider=provider_name,
                    warning=f"{missing_price_count} holding(s) do not have current prices.",
                )
            return DataStatus.stale_source(
                provider="manual",
                as_of=None,
                warning="Current prices are from holding records; provider freshness is unavailable.",
            )

        is_mock = latest_price.source.startswith("mock")
        if missing_price_count:
            return DataStatus.stale_source(
                provider=latest_price.source,
                as_of=latest_price.as_of,
                is_mock=is_mock,
                is_realtime=bool(latest_price.is_realtime),
                warning=f"{missing_price_count} holding(s) do not have current prices.",
            )
        if is_mock:
            return DataStatus.mock_source(
                provider=latest_price.source,
                as_of=latest_price.as_of,
                is_realtime=bool(latest_price.is_realtime),
            )
        return DataStatus.live_source(
            provider=latest_price.source,
            as_of=latest_price.as_of,
            is_realtime=bool(latest_price.is_realtime),
        )

    def _latest_asset_price(self, *, holdings: list[Holding]) -> AssetPrice | None:
        symbols = sorted({holding.symbol for holding in holdings})
        if not symbols:
            return None
        return self.db.scalar(
            select(AssetPrice)
            .where(AssetPrice.symbol.in_(symbols))
            .order_by(AssetPrice.as_of.desc(), AssetPrice.created_at.desc())
            .limit(1)
        )

    def _provider_name(self) -> str:
        provider = self.market_data_service.provider
        source = getattr(provider, "source", None)
        if isinstance(source, str) and source:
            return source
        return provider.__class__.__name__

    def _action_item_from_rule(self, rule: RuleInsight) -> DashboardActionItem:
        category_by_rule = {
            "MISSING_PRICE_DATA": "data_quality",
            "MISSING_COST_BASIS": "data_quality",
            "HIGH_CONCENTRATION": "risk",
            "MODERATE_CONCENTRATION": "risk",
            "SINGLE_ASSET_CLASS": "allocation",
            "CURRENCY_EXPOSURE": "allocation",
        }
        action_by_rule = {
            "MISSING_PRICE_DATA": "refresh_prices",
            "MISSING_COST_BASIS": "review_holdings",
            "HIGH_CONCENTRATION": "review_risk",
            "MODERATE_CONCENTRATION": "review_risk",
            "SINGLE_ASSET_CLASS": "review_allocation",
            "CURRENCY_EXPOSURE": "review_allocation",
        }
        return DashboardActionItem(
            id=rule.rule_id.lower(),
            priority=rule.severity,
            category=category_by_rule.get(rule.rule_id, "performance"),  # type: ignore[arg-type]
            title=rule.title,
            message=rule.message,
            affected_symbols=rule.affected_symbols,
            recommended_action=action_by_rule.get(rule.rule_id),  # type: ignore[arg-type]
        )

    def _data_quality_warnings(self, *, missing_price_count: int, missing_cost_count: int) -> list[str]:
        warnings: list[str] = []
        if missing_price_count:
            warnings.append(f"{missing_price_count} holding(s) do not have current prices.")
        if missing_cost_count:
            warnings.append(f"{missing_cost_count} holding(s) do not have average cost data.")
        return warnings

    def _top_n_weight(self, holdings, *, limit: int) -> float:
        return round(sum(holding.weight for holding in holdings[:limit]), 6)

    def _hhi(self, holdings) -> float:
        return round(sum(holding.weight * holding.weight for holding in holdings), 6)
