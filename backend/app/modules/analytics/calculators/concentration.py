from app.modules.analytics.schemas import ConcentrationRisk, HoldingAnalytics, LargestHolding


def calculate_concentration_risk(holdings: list[HoldingAnalytics]) -> ConcentrationRisk:
    priced_holdings = [holding for holding in holdings if holding.market_value is not None]
    if not priced_holdings:
        return ConcentrationRisk(
            status="empty",
            largest_holding=None,
            top_5_weight=0,
            message="No priced holdings are available for concentration analysis.",
        )

    largest = max(priced_holdings, key=lambda holding: holding.weight)
    top_5_weight = round(sum(holding.weight for holding in sorted(priced_holdings, key=lambda h: h.weight, reverse=True)[:5]), 6)

    if largest.weight > 0.25:
        status = "high"
        message = f"{largest.symbol} represents {_format_percent(largest.weight)} of the portfolio."
    elif largest.weight > 0.15:
        status = "moderate"
        message = f"{largest.symbol} represents {_format_percent(largest.weight)} of the portfolio."
    else:
        status = "ok"
        message = "No single holding exceeds the concentration thresholds."

    return ConcentrationRisk(
        status=status,
        largest_holding=LargestHolding(
            symbol=largest.symbol,
            market_value=largest.market_value or 0,
            weight=largest.weight,
        ),
        top_5_weight=top_5_weight,
        message=message,
    )


def _format_percent(value: float) -> str:
    return f"{value * 100:.0f}%"
