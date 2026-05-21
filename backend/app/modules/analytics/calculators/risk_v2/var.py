from collections.abc import Sequence
from math import ceil


def calculate_historical_var(
    returns: Sequence[float],
    *,
    confidence_level: float = 0.95,
) -> float | None:
    if not returns or confidence_level <= 0 or confidence_level >= 1:
        return None

    sorted_returns = sorted(float(value) for value in returns)
    tail_probability = 1 - confidence_level
    index = min(max(ceil(tail_probability * len(sorted_returns)) - 1, 0), len(sorted_returns) - 1)
    return max(0, -sorted_returns[index])
