from app.core.config import Settings


def test_settings_load_defaults() -> None:
    settings = Settings()

    assert settings.app_name == "P-insight"
    assert settings.app_env == "local"
    assert settings.market_data_provider == "mock"
    assert "http://localhost:5173" in settings.cors_origin_list
