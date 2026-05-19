from app.core.config import Settings


def test_settings_load_defaults() -> None:
    settings = Settings()

    assert settings.app_name == "P-insight"
    assert settings.app_env == "local"
    assert settings.demo_mode_enabled is True
    assert settings.market_data_provider == "mock"
    assert "http://localhost:5173" in settings.cors_origin_list


def test_settings_adds_frontend_url_to_cors() -> None:
    settings = Settings(frontend_url="https://p-insight.vercel.app")

    assert "http://localhost:5173" in settings.cors_origin_list
    assert "https://p-insight.vercel.app" in settings.cors_origin_list


def test_settings_disables_demo_mode_in_production_by_default() -> None:
    settings = Settings(app_env="production", enable_demo_mode=False)

    assert settings.demo_mode_enabled is False


def test_settings_can_explicitly_enable_demo_mode() -> None:
    settings = Settings(app_env="production", enable_demo_mode=True)

    assert settings.demo_mode_enabled is True
