from collections.abc import Sequence


def calculate_drawdowns(values: Sequence[float]) -> list[float]:
    if not values:
        return []

    peak = float(values[0])
    drawdowns: list[float] = []
    for value in values:
        current = float(value)
        if current > peak:
            peak = current
        drawdowns.append((current / peak) - 1 if peak > 0 else 0)
    return drawdowns


def calculate_max_drawdown(values: Sequence[float]) -> float | None:
    drawdowns = calculate_drawdowns(values)
    if not drawdowns:
        return None
    return min(drawdowns)
