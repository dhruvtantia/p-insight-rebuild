from collections.abc import Sequence
from math import sqrt
from statistics import pstdev, stdev


def calculate_volatility(
    returns: Sequence[float],
    *,
    annualization_factor: float = 252,
    sample: bool = True,
) -> float | None:
    if len(returns) < 2:
        return None

    values = [float(value) for value in returns]
    periodic_volatility = stdev(values) if sample else pstdev(values)
    return periodic_volatility * sqrt(annualization_factor)
