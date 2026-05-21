from collections.abc import Sequence
from statistics import mean


def calculate_beta(asset_returns: Sequence[float], benchmark_returns: Sequence[float]) -> float | None:
    paired_returns = [
        (float(asset_return), float(benchmark_return))
        for asset_return, benchmark_return in zip(asset_returns, benchmark_returns, strict=False)
    ]
    if len(paired_returns) < 2:
        return None

    asset_values = [asset_return for asset_return, _ in paired_returns]
    benchmark_values = [benchmark_return for _, benchmark_return in paired_returns]
    benchmark_mean = mean(benchmark_values)
    benchmark_variance = sum((value - benchmark_mean) ** 2 for value in benchmark_values)
    if benchmark_variance == 0:
        return None

    asset_mean = mean(asset_values)
    covariance = sum(
        (asset_value - asset_mean) * (benchmark_value - benchmark_mean)
        for asset_value, benchmark_value in paired_returns
    )
    return covariance / benchmark_variance
