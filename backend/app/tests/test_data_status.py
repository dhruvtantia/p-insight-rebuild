from datetime import UTC, datetime

from app.modules.common.data_status import DataStatus
from app.modules.market_data.providers.mock_provider import MockProviderIndia


def test_mock_source_constructor() -> None:
    as_of = datetime(2026, 1, 1, tzinfo=UTC)

    status = DataStatus.mock_source(provider="mock_india", as_of=as_of)

    assert status.source == "mock"
    assert status.provider == "mock_india"
    assert status.is_mock is True
    assert status.is_realtime is False
    assert status.as_of == as_of
    assert status.is_stale is False
    assert "simulated" in status.warning


def test_live_source_constructor() -> None:
    as_of = datetime(2026, 5, 21, tzinfo=UTC)

    status = DataStatus.live_source(provider="real_provider", as_of=as_of)

    assert status.source == "live"
    assert status.provider == "real_provider"
    assert status.is_mock is False
    assert status.is_realtime is True
    assert status.as_of == as_of
    assert status.is_stale is False
    assert status.warning is None


def test_stale_source_constructor() -> None:
    as_of = datetime(2026, 1, 1, tzinfo=UTC)

    status = DataStatus.stale_source(provider="real_provider", as_of=as_of)

    assert status.source == "stale"
    assert status.provider == "real_provider"
    assert status.is_mock is False
    assert status.is_realtime is False
    assert status.as_of == as_of
    assert status.is_stale is True
    assert "stale" in status.warning


def test_unavailable_source_constructor() -> None:
    status = DataStatus.unavailable_source(provider="real_provider")

    assert status.source == "unavailable"
    assert status.provider == "real_provider"
    assert status.is_mock is False
    assert status.is_realtime is False
    assert status.as_of is None
    assert status.is_stale is True
    assert "unavailable" in status.warning


def test_market_mock_provider_exposes_mock_status() -> None:
    quote = MockProviderIndia().get_latest_price("RELIANCE")

    assert quote.source == "mock_india"
    assert quote.data_status is not None
    assert quote.data_status.source == "mock"
    assert quote.data_status.provider == "mock_india"
    assert quote.data_status.is_mock is True
    assert quote.data_status.is_realtime is False
    assert quote.data_status.as_of == quote.as_of
