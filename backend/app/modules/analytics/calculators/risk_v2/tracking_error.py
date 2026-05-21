from collections.abc import Sequence
from math import sqrt
from statistics import stdev


def calculate_tracking_error(
    portfolio_returns: Sequence[float],
    benchmark_returns: Sequence[float],
    *,
    annualization_factor: float = 252,
) -> float | None:
    active_returns = [
        float(portfolio_return) - float(benchmark_return)
        for portfolio_return, benchmark_return in zip(portfolio_returns, benchmark_returns, strict=False)
    ]
    if len(active_returns) < 2:
        return None
    return stdev(active_returns) * sqrt(annualization_factor)
