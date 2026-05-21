from collections.abc import Sequence
from math import sqrt
from statistics import mean, pstdev


def calculate_downside_deviation(
    returns: Sequence[float],
    *,
    minimum_acceptable_return: float = 0,
    annualization_factor: float = 252,
) -> float | None:
    if len(returns) < 2:
        return None

    downside_returns = [
        min(float(value) - minimum_acceptable_return, 0)
        for value in returns
    ]
    downside_deviation = pstdev(downside_returns)
    return downside_deviation * sqrt(annualization_factor)


def calculate_sortino_ratio(
    returns: Sequence[float],
    *,
    minimum_acceptable_return: float = 0,
    annualization_factor: float = 252,
) -> float | None:
    downside_deviation = calculate_downside_deviation(
        returns,
        minimum_acceptable_return=minimum_acceptable_return,
        annualization_factor=annualization_factor,
    )
    if downside_deviation is None or downside_deviation == 0:
        return None

    excess_return = mean(float(value) - minimum_acceptable_return for value in returns)
    return (excess_return * annualization_factor) / downside_deviation
