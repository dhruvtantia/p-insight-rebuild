from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AssetPrice, Holding, User
from app.modules.analytics.service import AnalyticsService
from app.modules.portfolios.service import PortfolioService


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

        return {
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
