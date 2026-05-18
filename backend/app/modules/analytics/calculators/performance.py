from app.db.models import Holding
from app.modules.analytics.schemas import (
    HoldingAnalytics,
    LargestHolding,
    PerformanceAnalytics,
    PerformanceHolding,
    PortfolioAnalyticsSummary,
)


def build_holding_analytics(holdings: list[Holding]) -> list[HoldingAnalytics]:
    rows: list[HoldingAnalytics] = []
    total_value = sum(_market_value(holding) or 0 for holding in holdings)

    for holding in holdings:
        quantity = float(holding.quantity)
        average_cost = _optional_float(holding.average_cost)
        current_price = _optional_float(holding.current_price)
        market_value = _market_value(holding)
        cost_basis = round(quantity * average_cost, 6) if average_cost is not None else None
        unrealized_gain_loss = (
            round(quantity * (current_price - average_cost), 6)
            if current_price is not None and average_cost is not None
            else None
        )
        unrealized_gain_loss_pct = (
            round(unrealized_gain_loss / cost_basis, 6)
            if unrealized_gain_loss is not None and cost_basis is not None and cost_basis > 0
            else None
        )
        rows.append(
            HoldingAnalytics(
                holding_id=holding.id,
                symbol=holding.symbol,
                quantity=quantity,
                average_cost=average_cost,
                current_price=current_price,
                currency=holding.currency,
                sector=holding.sector,
                asset_class=holding.asset_class,
                market_value=market_value,
                cost_basis=cost_basis,
                unrealized_gain_loss=unrealized_gain_loss,
                unrealized_gain_loss_pct=unrealized_gain_loss_pct,
                weight=round((market_value or 0) / total_value, 6) if total_value > 0 else 0,
            )
        )

    return rows


def calculate_summary(
    *, portfolio_id: str, base_currency: str, holdings: list[HoldingAnalytics]
) -> PortfolioAnalyticsSummary:
    total_value = round(sum(holding.market_value or 0 for holding in holdings), 6)
    total_cost_basis = round(sum(holding.cost_basis or 0 for holding in holdings), 6)
    total_unrealized_gain_loss = round(sum(holding.unrealized_gain_loss or 0 for holding in holdings), 6)
    total_unrealized_gain_loss_pct = (
        round(total_unrealized_gain_loss / total_cost_basis, 6) if total_cost_basis > 0 else None
    )

    return PortfolioAnalyticsSummary(
        portfolio_id=portfolio_id,
        base_currency=base_currency,
        total_portfolio_value=total_value,
        total_cost_basis=total_cost_basis,
        total_unrealized_gain_loss=total_unrealized_gain_loss,
        total_unrealized_gain_loss_pct=total_unrealized_gain_loss_pct,
        holdings=holdings,
        largest_holding=_largest_holding(holdings),
    )


def calculate_performance(holdings: list[HoldingAnalytics]) -> PerformanceAnalytics:
    total_cost_basis = round(sum(holding.cost_basis or 0 for holding in holdings), 6)
    total_unrealized_gain_loss = round(sum(holding.unrealized_gain_loss or 0 for holding in holdings), 6)
    total_unrealized_gain_loss_pct = (
        round(total_unrealized_gain_loss / total_cost_basis, 6) if total_cost_basis > 0 else None
    )
    holdings_with_pl = [
        PerformanceHolding(
            symbol=holding.symbol,
            unrealized_gain_loss=holding.unrealized_gain_loss,
            unrealized_gain_loss_pct=holding.unrealized_gain_loss_pct,
        )
        for holding in holdings
        if holding.unrealized_gain_loss is not None
    ]
    gainers = [holding for holding in holdings_with_pl if holding.unrealized_gain_loss > 0]
    losers = [holding for holding in holdings_with_pl if holding.unrealized_gain_loss < 0]

    return PerformanceAnalytics(
        total_cost_basis=total_cost_basis,
        total_unrealized_gain_loss=total_unrealized_gain_loss,
        total_unrealized_gain_loss_pct=total_unrealized_gain_loss_pct,
        top_gainers=sorted(gainers, key=lambda holding: holding.unrealized_gain_loss, reverse=True)[:5],
        top_losers=sorted(losers, key=lambda holding: holding.unrealized_gain_loss)[:5],
    )


def _largest_holding(holdings: list[HoldingAnalytics]) -> LargestHolding | None:
    priced_holdings = [holding for holding in holdings if holding.market_value is not None]
    if not priced_holdings:
        return None
    largest = max(priced_holdings, key=lambda holding: holding.market_value or 0)
    return LargestHolding(symbol=largest.symbol, market_value=largest.market_value or 0, weight=largest.weight)


def _market_value(holding: Holding) -> float | None:
    current_price = _optional_float(holding.current_price)
    if current_price is None:
        return None
    return round(float(holding.quantity) * current_price, 6)


def _optional_float(value: object) -> float | None:
    return float(value) if value is not None else None
