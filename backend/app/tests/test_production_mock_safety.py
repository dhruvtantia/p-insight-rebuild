import pytest

from app.core.config import get_settings
from app.core.errors import ValidationAppError
from app.modules.ai_advisor.service import AIAdvisorService
from app.modules.market_data.providers.mock_provider import MockProviderIndia
from app.modules.market_data.service import MarketDataService


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_local_mock_market_data_and_ai_are_allowed(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "local")

    market_data = MarketDataService(db=object())
    provider, model = AIAdvisorService(db=object())._provider_metadata()

    assert isinstance(market_data.provider, MockProviderIndia)
    assert provider == "mock"
    assert model == "deterministic-advisor-v1"


def test_test_env_mock_market_data_and_ai_are_allowed(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")

    market_data = MarketDataService(db=object())
    provider, model = AIAdvisorService(db=object())._provider_metadata()

    assert isinstance(market_data.provider, MockProviderIndia)
    assert provider == "mock"
    assert model == "deterministic-advisor-v1"


@pytest.mark.parametrize("provider_name", ["mock", "mock_india"])
def test_production_mock_market_data_is_blocked_without_override(monkeypatch, provider_name: str) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("MARKET_DATA_PROVIDER", provider_name)
    monkeypatch.delenv("ALLOW_PRODUCTION_MOCK_MARKET_DATA", raising=False)

    with pytest.raises(ValidationAppError, match="Mock market data is disabled in production"):
        MarketDataService(db=object())


def test_production_mock_ai_is_blocked_without_override(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("ALLOW_PRODUCTION_MOCK_AI", raising=False)

    with pytest.raises(ValidationAppError, match="Mock AI is disabled in production"):
        AIAdvisorService(db=object())._provider_metadata()


def test_production_mock_overrides_allow_usage_but_do_not_make_status_safe(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ALLOW_PRODUCTION_MOCK_MARKET_DATA", "true")
    monkeypatch.setenv("ALLOW_PRODUCTION_MOCK_AI", "true")

    market_data = MarketDataService(db=object())
    provider, model = AIAdvisorService(db=object())._provider_metadata()
    settings = get_settings()

    assert isinstance(market_data.provider, MockProviderIndia)
    assert provider == "mock"
    assert model == "deterministic-advisor-v1"
    assert settings.production_safe is False
    assert any("Production mock market data override is enabled" in warning for warning in settings.warnings)
    assert any("Production mock AI override is enabled" in warning for warning in settings.warnings)
