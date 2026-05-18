from app.modules.analytics.calculators.concentration import calculate_concentration_risk
from app.modules.analytics.schemas import HoldingAnalytics, RiskAnalytics, RiskMetric


def calculate_risk(holdings: list[HoldingAnalytics]) -> RiskAnalytics:
    placeholder = RiskMetric(
        value=None,
        status="insufficient_history",
        message="Historical price data is not available yet.",
    )
    return RiskAnalytics(
        volatility=placeholder,
        sharpe_ratio=placeholder,
        max_drawdown=placeholder,
        concentration=calculate_concentration_risk(holdings),
    )
