from app.core.config import Settings


def test_settings_load_defaults() -> None:
    settings = Settings()

    assert settings.app_name == "P-insight"
    assert settings.app_env == "local"
    assert settings.normalized_app_env == "local"
    assert settings.demo_mode_enabled is True
    assert settings.market_data_provider == "mock_india"
    assert settings.indian_market_data_provider == "mock_india"
    assert settings.resolved_market_data_provider == "mock_india"
    assert settings.market_data_is_mock is True
    assert settings.ai_provider_mode == "mock"
    assert settings.ai_is_mock is True
    assert settings.production_mock_market_data_allowed is True
    assert settings.production_mock_ai_allowed is True
    assert settings.production_safe is False
    assert settings.warnings == [
        "Market data provider 'mock_india' is mock data and is not production-safe.",
        "AI provider mode is mock and is not production-safe.",
    ]
    assert settings.twelve_data_api_key is None
    assert settings.alpha_vantage_api_key is None
    assert settings.marketstack_api_key is None
    assert "http://localhost:5173" in settings.cors_origin_list


def test_settings_adds_frontend_url_to_cors() -> None:
    settings = Settings(frontend_url="https://p-insight.vercel.app")

    assert "http://localhost:5173" in settings.cors_origin_list
    assert "https://p-insight.vercel.app" in settings.cors_origin_list


def test_settings_disables_demo_mode_in_production_by_default() -> None:
    settings = Settings(app_env="production", enable_demo_mode=False)

    assert settings.demo_mode_enabled is False
    assert settings.production_mock_market_data_allowed is False
    assert settings.production_mock_ai_allowed is False
    assert settings.production_safe is False


def test_settings_can_explicitly_enable_demo_mode() -> None:
    settings = Settings(app_env="production", enable_demo_mode=True)

    assert settings.demo_mode_enabled is True
    assert settings.production_mock_market_data_allowed is False
    assert settings.production_mock_ai_allowed is False


def test_settings_allows_test_env_mocks() -> None:
    settings = Settings(app_env="test")

    assert settings.demo_mode_enabled is False
    assert settings.production_mock_market_data_allowed is True
    assert settings.production_mock_ai_allowed is True


def test_settings_production_mock_overrides_do_not_make_config_production_safe() -> None:
    settings = Settings(
        app_env="production",
        allow_production_mock_market_data=True,
        allow_production_mock_ai=True,
    )

    assert settings.production_mock_market_data_allowed is True
    assert settings.production_mock_ai_allowed is True
    assert settings.production_safe is False
    assert any("Production mock market data override is enabled" in warning for warning in settings.warnings)
    assert any("Production mock AI override is enabled" in warning for warning in settings.warnings)
