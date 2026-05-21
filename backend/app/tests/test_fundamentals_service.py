import pytest

from app.core.config import get_settings
from app.core.errors import ValidationAppError
from app.modules.fundamentals.schemas import FUNDAMENTAL_METRIC_NAMES
from app.modules.fundamentals.service import FundamentalsService


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_known_mock_symbol_returns_fundamentals(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "local")

    response = FundamentalsService().get_fundamentals(symbol="RELIANCE")

    assert response.symbol == "RELIANCE"
    assert response.company_name == "Reliance Industries Ltd."
    assert response.currency == "INR"
    assert response.metrics.pe_ratio == 27.4
    assert response.metrics.forward_pe == 22.8
    assert response.metrics.price_to_book == 2.35
    assert response.metrics.ev_to_ebitda == 13.2
    assert response.metrics.peg == 1.48
    assert response.metrics.roe == 0.087
    assert response.metrics.roa == 0.041
    assert response.metrics.operating_margin == 0.158
    assert response.metrics.net_margin == 0.079
    assert response.metrics.revenue_growth == 0.061
    assert response.metrics.eps_growth == 0.094
    assert response.metrics.dividend_yield == 0.0035
    assert response.metrics.debt_to_equity == 0.42
    assert response.metrics.market_cap == 19_400_000_000_000
    assert response.data_status.source == "mock"
    assert response.data_status.provider == "mock_fundamentals"
    assert response.data_status.is_mock is True


def test_unknown_symbol_returns_no_coverage_without_fabricated_metrics(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")

    response = FundamentalsService().get_fundamentals(symbol="UNKNOWNCO")

    assert response.symbol == "UNKNOWNCO"
    assert response.company_name is None
    assert response.coverage.coverage_ratio == 0
    assert response.coverage.available_metrics == []
    assert response.coverage.missing_metrics == list(FUNDAMENTAL_METRIC_NAMES)
    assert response.coverage.is_complete is False
    assert all(value is None for value in response.metrics.model_dump().values())
    assert "unavailable" in (response.data_status.warning or "")


def test_coverage_metadata_reports_complete_known_mock_symbol(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "demo")

    response = FundamentalsService().get_fundamentals(symbol="TCS.NS")

    assert response.symbol == "TCS"
    assert response.coverage.provider == "mock_fundamentals"
    assert response.coverage.coverage_ratio == 1
    assert response.coverage.available_metrics == list(FUNDAMENTAL_METRIC_NAMES)
    assert response.coverage.missing_metrics == []
    assert response.coverage.is_complete is True


def test_mock_fundamentals_are_blocked_in_production(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")

    with pytest.raises(ValidationAppError, match="Mock fundamentals are disabled"):
        FundamentalsService()
