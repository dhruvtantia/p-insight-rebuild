from collections.abc import Sequence
from statistics import mean


def calculate_correlation(series_a: Sequence[float], series_b: Sequence[float]) -> float | None:
    paired_values = [
        (float(value_a), float(value_b))
        for value_a, value_b in zip(series_a, series_b, strict=False)
    ]
    if len(paired_values) < 2:
        return None

    values_a = [value_a for value_a, _ in paired_values]
    values_b = [value_b for _, value_b in paired_values]
    mean_a = mean(values_a)
    mean_b = mean(values_b)
    variance_a = sum((value - mean_a) ** 2 for value in values_a)
    variance_b = sum((value - mean_b) ** 2 for value in values_b)
    if variance_a == 0 or variance_b == 0:
        return None

    covariance = sum(
        (value_a - mean_a) * (value_b - mean_b)
        for value_a, value_b in paired_values
    )
    return covariance / (variance_a * variance_b) ** 0.5
