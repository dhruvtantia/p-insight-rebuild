from datetime import UTC, date, datetime, timedelta
from hashlib import sha256

from app.modules.common.data_status import DataStatus
from app.modules.market_data.history_schemas import HistoricalPricePoint


MOCK_HISTORY_PROVIDER = "mock_historical_prices"
MOCK_HISTORY_AS_OF = datetime(2026, 1, 1, tzinfo=UTC)


def mock_history_data_status() -> DataStatus:
    return DataStatus.mock_source(
        provider=MOCK_HISTORY_PROVIDER,
        as_of=MOCK_HISTORY_AS_OF,
        is_realtime=False,
        warning="Historical prices are deterministic mock data for tests and local demos only.",
    )


def build_mock_historical_prices(
    *,
    symbol: str,
    start_date: date,
    end_date: date,
    currency: str = "INR",
    data_status: DataStatus | None = None,
) -> list[HistoricalPricePoint]:
    if end_date < start_date:
        return []

    status = data_status or mock_history_data_status()
    base_price = _base_price(symbol)
    points: list[HistoricalPricePoint] = []
    current_date = start_date
    day_index = 0

    while current_date <= end_date:
        trend = 1 + (day_index * 0.00035)
        wave = ((day_index % 17) - 8) * 0.0015
        close = round(max(base_price * (trend + wave), 0.01), 2)
        points.append(
            HistoricalPricePoint(
                date=current_date,
                close=close,
                currency=currency,
                data_status=status,
            )
        )
        current_date += timedelta(days=1)
        day_index += 1

    return points


def _base_price(symbol: str) -> float:
    normalized_symbol = symbol.strip().upper()
    digest = sha256(normalized_symbol.encode("utf-8")).hexdigest()
    paise = 10_000 + int(digest[:8], 16) % 490_000
    return round(paise / 100, 2)
