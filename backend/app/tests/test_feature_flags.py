import pytest

from app.core.config import Settings, get_settings
from app.core.feature_flags import FEATURE_FLAGS, FeatureDisabledError, require_feature_enabled


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_feature_flags_default_off() -> None:
    settings = Settings()

    assert set(settings.feature_flags) == set(FEATURE_FLAGS)
    assert all(enabled is False for enabled in settings.feature_flags.values())


def test_explicit_env_true_enables_feature(monkeypatch) -> None:
    monkeypatch.setenv("ENABLE_MARKET_OVERVIEW", "true")

    settings = Settings()

    assert settings.enable_market_overview is True
    assert settings.feature_flags["ENABLE_MARKET_OVERVIEW"] is True


def test_require_feature_enabled_allows_enabled_feature(monkeypatch) -> None:
    monkeypatch.setenv("ENABLE_MARKET_OVERVIEW", "true")

    require_feature_enabled("ENABLE_MARKET_OVERVIEW")


def test_require_feature_enabled_raises_clean_error_for_disabled_feature() -> None:
    with pytest.raises(FeatureDisabledError) as exc_info:
        require_feature_enabled("ENABLE_MARKET_OVERVIEW")

    assert exc_info.value.error_code == "feature_disabled"
    assert exc_info.value.status_code == 404
    assert exc_info.value.details == {"feature": "ENABLE_MARKET_OVERVIEW"}
    assert "disabled" in exc_info.value.message


def test_require_feature_enabled_normalizes_short_feature_name(monkeypatch) -> None:
    monkeypatch.setenv("ENABLE_RISK_V2", "true")

    require_feature_enabled("risk_v2")
