from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import AssetPrice, Holding, User
from app.modules.analytics.service import AnalyticsService
from app.modules.dashboard.service import DashboardService
from app.modules.fundamentals.service import FundamentalsService
from app.modules.peers.service import PeerComparisonService
from app.modules.performance.service import PerformanceService
from app.modules.portfolios.service import PortfolioService
from app.modules.risk.service import RiskV2Service
from app.modules.snapshots.service import SnapshotService


class AIAdvisorContextBuilder:
    def __init__(self, db: Session):
        self.db = db
        self.portfolio_service = PortfolioService(db)
        self.analytics_service = AnalyticsService(db)

    def build_context(self, *, portfolio_id: str, user: User, user_question: str | None = None) -> dict:
        portfolio = self.portfolio_service.get_portfolio(portfolio_id=portfolio_id, user=user)
        analytics = self.analytics_service.build_bundle(portfolio_id=portfolio.id, user=user)
        holdings = self._list_holdings(portfolio_id=portfolio.id)
        latest_prices = self._latest_prices_by_symbol([holding.symbol for holding in holdings])

        context = {
            "portfolio_summary": {
                "id": portfolio.id,
                "name": portfolio.name,
                "base_currency": portfolio.base_currency,
                "benchmark_symbol": portfolio.benchmark_symbol,
                "risk_free_rate": float(portfolio.risk_free_rate) if portfolio.risk_free_rate is not None else None,
                "total_portfolio_value": analytics.summary.total_portfolio_value,
                "total_cost_basis": analytics.summary.total_cost_basis,
                "total_unrealized_gain_loss": analytics.summary.total_unrealized_gain_loss,
                "total_unrealized_gain_loss_pct": analytics.summary.total_unrealized_gain_loss_pct,
                "largest_holding": analytics.summary.largest_holding.model_dump(mode="json")
                if analytics.summary.largest_holding
                else None,
                "holdings_count": len(holdings),
            },
            "holdings": [
                {
                    "symbol": holding.symbol,
                    "company_name": holding.company_name,
                    "quantity": float(holding.quantity),
                    "average_cost": float(holding.average_cost) if holding.average_cost is not None else None,
                    "current_price": float(holding.current_price) if holding.current_price is not None else None,
                    "currency": holding.currency,
                    "sector": holding.sector,
                    "asset_class": holding.asset_class,
                }
                for holding in holdings
            ],
            "risk_metrics": analytics.risk.model_dump(mode="json"),
            "allocation": analytics.allocation.model_dump(mode="json"),
            "rule_based_insights": [rule.model_dump(mode="json") for rule in analytics.rules],
            "price_freshness": {
                "priced_symbols": sorted(latest_prices.keys()),
                "missing_price_symbols": sorted(
                    holding.symbol for holding in holdings if holding.current_price is None
                ),
                "latest_price_as_of": max(
                    (price.as_of.isoformat() for price in latest_prices.values()),
                    default=None,
                ),
                "latest_price_source": self._latest_price_source(latest_prices),
            },
            "user_question": user_question or "",
        }
        optional_context = self._optional_context(portfolio_id=portfolio.id, user=user, holdings=holdings)
        if optional_context:
            context["optional_context"] = optional_context
        return context

    def _list_holdings(self, *, portfolio_id: str) -> list[Holding]:
        statement = select(Holding).where(Holding.portfolio_id == portfolio_id).order_by(Holding.symbol.asc())
        return list(self.db.scalars(statement).all())

    def _latest_prices_by_symbol(self, symbols: list[str]) -> dict[str, AssetPrice]:
        if not symbols:
            return {}
        statement = (
            select(AssetPrice)
            .where(AssetPrice.symbol.in_(symbols))
            .order_by(AssetPrice.symbol.asc(), AssetPrice.as_of.desc(), AssetPrice.created_at.desc())
        )
        prices: dict[str, AssetPrice] = {}
        for price in self.db.scalars(statement).all():
            if price.symbol not in prices:
                prices[price.symbol] = price
        return prices

    def _latest_price_source(self, latest_prices: dict[str, AssetPrice]) -> str | None:
        if not latest_prices:
            return None
        latest_price = max(latest_prices.values(), key=lambda price: price.as_of)
        return latest_price.source

    def _optional_context(self, *, portfolio_id: str, user: User, holdings: list[Holding]) -> dict:
        settings = get_settings()
        flags = settings.feature_flags
        context: dict = {}

        if flags.get("ENABLE_DASHBOARD_BUNDLE"):
            dashboard_summary = self._safe_optional_block(
                lambda: self._dashboard_summary(portfolio_id=portfolio_id, user=user)
            )
            if dashboard_summary is not None:
                context["dashboard_summary"] = dashboard_summary

        if flags.get("ENABLE_PERFORMANCE_HISTORY"):
            performance_summary = self._safe_optional_block(
                lambda: self._performance_history_summary(portfolio_id=portfolio_id, user=user)
            )
            if performance_summary is not None:
                context["performance_history_summary"] = performance_summary

        if flags.get("ENABLE_RISK_V2"):
            risk_summary = self._safe_optional_block(
                lambda: self._risk_v2_summary(portfolio_id=portfolio_id, user=user)
            )
            if risk_summary is not None:
                context["risk_v2_summary"] = risk_summary

        if flags.get("ENABLE_FUNDAMENTALS"):
            fundamentals_summary = self._safe_optional_block(
                lambda: self._fundamentals_summary(portfolio_id=portfolio_id, user=user)
            )
            if fundamentals_summary is not None:
                context["fundamentals_summary"] = fundamentals_summary

        if flags.get("ENABLE_PEERS") and holdings:
            peer_summary = self._safe_optional_block(
                lambda: self._peer_summary(portfolio_id=portfolio_id, user=user, symbol=holdings[0].symbol)
            )
            if peer_summary is not None:
                context["peer_summary"] = peer_summary

        if flags.get("ENABLE_SNAPSHOTS"):
            snapshot_summary = self._safe_optional_block(
                lambda: self._snapshot_change_summary(portfolio_id=portfolio_id, user=user)
            )
            if snapshot_summary is not None:
                context["snapshot_change_summary"] = snapshot_summary

        return context

    def _safe_optional_block(self, builder):
        try:
            return builder()
        except Exception:
            return None

    def _dashboard_summary(self, *, portfolio_id: str, user: User) -> dict:
        dashboard = DashboardService(self.db).get_bundle(portfolio_id=portfolio_id, user=user)
        return {
            "current_value": dashboard.kpis.current_value,
            "total_invested": dashboard.kpis.total_invested,
            "return_percent": dashboard.kpis.return_percent,
            "largest_holding_symbol": dashboard.kpis.largest_holding_symbol,
            "largest_holding_weight": dashboard.kpis.largest_holding_weight,
            "data_quality": {
                "missing_price_count": dashboard.data_quality.missing_price_count,
                "missing_cost_basis_count": dashboard.data_quality.missing_cost_basis_count,
                "warnings": dashboard.data_quality.warnings,
            },
            "action_items": [item.model_dump(mode="json") for item in dashboard.action_items[:5]],
        }

    def _performance_history_summary(self, *, portfolio_id: str, user: User) -> dict:
        performance = PerformanceService(self.db).get_history(portfolio_id=portfolio_id, user=user)
        portfolio_returns = performance.portfolio_normalized_return_series
        benchmark_returns = performance.benchmark_normalized_return_series
        return {
            "method": performance.assumptions.method,
            "benchmark_symbol": performance.benchmark_symbol,
            "portfolio_points": len(performance.portfolio_value_series),
            "benchmark_points": len(benchmark_returns),
            "latest_portfolio_normalized_return": portfolio_returns[-1].normalized_return
            if portfolio_returns
            else None,
            "latest_benchmark_normalized_return": benchmark_returns[-1].normalized_return
            if benchmark_returns
            else None,
            "missing_price_symbols": performance.missing_price_symbols,
            "data_status": performance.data_status.model_dump(mode="json"),
            "assumptions": performance.assumptions.model_dump(mode="json"),
        }

    def _risk_v2_summary(self, *, portfolio_id: str, user: User) -> dict:
        risk = RiskV2Service(self.db).get_risk(portfolio_id=portfolio_id, user=user)
        return {
            "observations": risk.observations,
            "annualized_return": risk.annualized_return,
            "annualized_volatility": risk.annualized_volatility,
            "sharpe_ratio": risk.sharpe_ratio,
            "sortino_ratio": risk.sortino_ratio,
            "max_drawdown": risk.max_drawdown,
            "value_at_risk_95": risk.value_at_risk_95,
            "beta_vs_benchmark": risk.beta_vs_benchmark,
            "tracking_error": risk.tracking_error,
            "metric_status": {
                name: status.model_dump(mode="json")
                for name, status in risk.metric_status.items()
            },
        }

    def _fundamentals_summary(self, *, portfolio_id: str, user: User) -> dict:
        fundamentals = FundamentalsService(db=self.db).get_portfolio_fundamentals(
            portfolio_id=portfolio_id,
            user=user,
        )
        return {
            "weighted_metrics": fundamentals.weighted_metrics.model_dump(mode="json"),
            "coverage": fundamentals.coverage.model_dump(mode="json"),
            "missing_symbols": fundamentals.missing_symbols,
            "warnings": fundamentals.warnings,
            "data_status": fundamentals.data_status.model_dump(mode="json"),
        }

    def _peer_summary(self, *, portfolio_id: str, user: User, symbol: str) -> dict:
        peers = PeerComparisonService(self.db).compare(portfolio_id=portfolio_id, symbol=symbol, user=user)
        return {
            "symbol": peers.symbol,
            "peer_symbols": [peer.symbol for peer in peers.peer_companies],
            "peer_set_quality": peers.peer_set_quality.model_dump(mode="json"),
            "warnings": peers.warnings,
            "metric_count": len(peers.metric_comparison_table),
        }

    def _snapshot_change_summary(self, *, portfolio_id: str, user: User) -> dict:
        snapshot_service = SnapshotService(self.db)
        snapshots = snapshot_service.list_snapshots(portfolio_id=portfolio_id, user=user)
        summary = {
            "snapshot_count": len(snapshots),
            "latest_snapshot": snapshots[0].model_dump(mode="json") if snapshots else None,
            "latest_change": None,
        }
        if len(snapshots) >= 2:
            comparison = snapshot_service.compare_snapshots(
                portfolio_id=portfolio_id,
                user=user,
                from_id=snapshots[1].id,
                to_id=snapshots[0].id,
            )
            summary["latest_change"] = {
                "added_holdings": [holding.symbol for holding in comparison.added_holdings],
                "removed_holdings": [holding.symbol for holding in comparison.removed_holdings],
                "quantity_changes": [change.model_dump(mode="json") for change in comparison.quantity_changes],
                "total_value_change": comparison.value_changes.total_value_change,
                "concentration_changes": comparison.concentration_changes.model_dump(mode="json"),
            }
        return summary
