from collections.abc import Sequence
from math import sqrt
from statistics import mean, stdev


def calculate_sharpe_ratio(
    returns: Sequence[float],
    *,
    risk_free_rate_per_period: float = 0,
    annualization_factor: float = 252,
) -> float | None:
    if len(returns) < 2:
        return None

    excess_returns = [float(value) - risk_free_rate_per_period for value in returns]
    volatility = stdev(excess_returns)
    if volatility == 0:
        return None
    return (mean(excess_returns) / volatility) * sqrt(annualization_factor)
