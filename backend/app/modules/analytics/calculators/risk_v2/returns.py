from collections.abc import Sequence


def calculate_simple_returns(values: Sequence[float]) -> list[float]:
    returns: list[float] = []
    if len(values) < 2:
        return returns

    previous = float(values[0])
    for value in values[1:]:
        current = float(value)
        if previous > 0:
            returns.append((current / previous) - 1)
        previous = current
    return returns


def calculate_excess_returns(returns: Sequence[float], risk_free_rate_per_period: float = 0) -> list[float]:
    return [float(value) - risk_free_rate_per_period for value in returns]
