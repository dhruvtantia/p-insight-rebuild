from fastapi import status

from app.core.config import get_settings
from app.core.errors import AppError


FEATURE_FLAGS = (
    "ENABLE_MARKET_OVERVIEW",
    "ENABLE_DASHBOARD_BUNDLE",
    "ENABLE_UPLOAD_SUGGESTIONS",
    "ENABLE_HISTORICAL_DATA",
    "ENABLE_PERFORMANCE_HISTORY",
    "ENABLE_RISK_V2",
    "ENABLE_SNAPSHOTS",
    "ENABLE_FUNDAMENTALS",
    "ENABLE_PEERS",
    "ENABLE_SIMULATOR",
    "ENABLE_OPTIMIZER",
    "ENABLE_REBALANCE_TICKETS",
)


class FeatureDisabledError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "feature_disabled"


def require_feature_enabled(feature_name: str) -> None:
    normalized_name = _normalize_feature_name(feature_name)
    flags = get_settings().feature_flags
    if normalized_name not in flags:
        raise FeatureDisabledError(
            f"Feature flag '{normalized_name}' is not configured.",
            details={"feature": normalized_name},
        )
    if not flags[normalized_name]:
        raise FeatureDisabledError(
            f"Feature '{normalized_name}' is disabled.",
            details={"feature": normalized_name},
        )


def _normalize_feature_name(feature_name: str) -> str:
    cleaned = feature_name.strip().upper()
    if not cleaned:
        raise FeatureDisabledError("Feature name cannot be empty.")
    if cleaned.startswith("ENABLE_"):
        return cleaned
    return f"ENABLE_{cleaned}"
