from functools import lru_cache

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "P-insight"
    app_env: str = "local"
    service_name: str = "p-insight-backend"
    api_prefix: str = "/api"
    enable_demo_mode: bool = False

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/p_insight"

    market_data_provider: str = "mock"
    market_data_api_key: str | None = None
    polygon_api_key: str | None = None
    fmp_api_key: str | None = None

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    jwt_secret: str | None = None
    frontend_url: str | None = Field(
        default=None,
        description="Public frontend URL allowed by production CORS, for example https://p-insight.vercel.app",
    )
    sentry_dsn: str | None = None

    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        description="Comma-separated allowed CORS origins",
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @computed_field
    @property
    def cors_origin_list(self) -> list[str]:
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        if self.frontend_url:
            origins.append(self.frontend_url.strip())
        return list(dict.fromkeys(origin for origin in origins if origin))

    @computed_field
    @property
    def demo_mode_enabled(self) -> bool:
        return self.app_env.strip().lower() == "local" or self.enable_demo_mode

    @computed_field
    @property
    def ai_provider_mode(self) -> str:
        return "mock"


@lru_cache
def get_settings() -> Settings:
    return Settings()
