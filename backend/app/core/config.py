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

    market_data_provider: str = "mock_india"
    indian_market_data_provider: str = "mock_india"
    market_data_api_key: str | None = None
    polygon_api_key: str | None = None
    fmp_api_key: str | None = None
    twelve_data_api_key: str | None = None
    alpha_vantage_api_key: str | None = None
    marketstack_api_key: str | None = None
    allow_production_mock_market_data: bool = False

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    allow_production_mock_ai: bool = False

    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    jwt_secret: str | None = None
    frontend_url: str | None = Field(
        default=None,
        description="Public frontend URL allowed by production CORS, for example https://p-insight.vercel.app",
    )
    sentry_dsn: str | None = None

    enable_market_overview: bool = False
    enable_dashboard_bundle: bool = False
    enable_upload_suggestions: bool = False
    enable_historical_data: bool = False
    enable_performance_history: bool = False
    enable_risk_v2: bool = False
    enable_snapshots: bool = False
    enable_fundamentals: bool = False
    enable_peers: bool = False
    enable_simulator: bool = False
    enable_optimizer: bool = False
    enable_rebalance_tickets: bool = False

    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        description="Comma-separated allowed CORS origins",
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @computed_field
    @property
    def normalized_app_env(self) -> str:
        return self.app_env.strip().lower()

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
        return self.normalized_app_env == "local" or self.enable_demo_mode

    @computed_field
    @property
    def ai_provider_mode(self) -> str:
        return "mock"

    @computed_field
    @property
    def resolved_market_data_provider(self) -> str:
        provider_name = self.market_data_provider.strip().lower()
        if provider_name in {"india", "indian"}:
            return self.indian_market_data_provider.strip().lower()
        return provider_name

    @computed_field
    @property
    def market_data_is_mock(self) -> bool:
        return self.resolved_market_data_provider in {"mock", "mock_india"}

    @computed_field
    @property
    def ai_is_mock(self) -> bool:
        return self.ai_provider_mode.strip().lower() == "mock"

    @computed_field
    @property
    def production_mock_market_data_allowed(self) -> bool:
        return self.normalized_app_env in {"local", "test", "demo", "development"} or self.allow_production_mock_market_data

    @computed_field
    @property
    def production_mock_ai_allowed(self) -> bool:
        return self.normalized_app_env in {"local", "test", "demo", "development"} or self.allow_production_mock_ai

    @computed_field
    @property
    def production_safe(self) -> bool:
        return not (self.market_data_is_mock or self.ai_is_mock)

    @computed_field
    @property
    def warnings(self) -> list[str]:
        warnings: list[str] = []
        if self.market_data_is_mock:
            warnings.append(
                f"Market data provider '{self.resolved_market_data_provider}' is mock data and is not production-safe."
            )
            if self.normalized_app_env == "production" and self.allow_production_mock_market_data:
                warnings.append(
                    "Production mock market data override is enabled; use this only for explicit test/demo deployments."
                )
        if self.ai_is_mock:
            warnings.append("AI provider mode is mock and is not production-safe.")
            if self.normalized_app_env == "production" and self.allow_production_mock_ai:
                warnings.append(
                    "Production mock AI override is enabled; use this only for explicit test/demo deployments."
                )
        return warnings

    @computed_field
    @property
    def feature_flags(self) -> dict[str, bool]:
        return {
            "ENABLE_MARKET_OVERVIEW": self.enable_market_overview,
            "ENABLE_DASHBOARD_BUNDLE": self.enable_dashboard_bundle,
            "ENABLE_UPLOAD_SUGGESTIONS": self.enable_upload_suggestions,
            "ENABLE_HISTORICAL_DATA": self.enable_historical_data,
            "ENABLE_PERFORMANCE_HISTORY": self.enable_performance_history,
            "ENABLE_RISK_V2": self.enable_risk_v2,
            "ENABLE_SNAPSHOTS": self.enable_snapshots,
            "ENABLE_FUNDAMENTALS": self.enable_fundamentals,
            "ENABLE_PEERS": self.enable_peers,
            "ENABLE_SIMULATOR": self.enable_simulator,
            "ENABLE_OPTIMIZER": self.enable_optimizer,
            "ENABLE_REBALANCE_TICKETS": self.enable_rebalance_tickets,
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
