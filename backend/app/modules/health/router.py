from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings

router = APIRouter(prefix="/api", tags=["health"])


class AppStatusResponse(BaseModel):
    app_env: str
    demo_mode_enabled: bool
    market_data_provider: str
    market_data_is_mock: bool
    ai_provider_mode: str
    ai_is_mock: bool
    production_safe: bool
    warnings: list[str]


@router.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "p-insight-backend",
    }


@router.get("/status", response_model=AppStatusResponse)
def app_status() -> AppStatusResponse:
    settings = get_settings()
    return AppStatusResponse(
        app_env=settings.app_env,
        demo_mode_enabled=settings.demo_mode_enabled,
        market_data_provider=settings.market_data_provider,
        market_data_is_mock=settings.market_data_is_mock,
        ai_provider_mode=settings.ai_provider_mode,
        ai_is_mock=settings.ai_is_mock,
        production_safe=settings.production_safe,
        warnings=settings.warnings,
    )
