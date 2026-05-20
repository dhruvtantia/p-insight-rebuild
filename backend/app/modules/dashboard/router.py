from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.core.feature_flags import require_feature_enabled
from app.db.session import get_db
from app.modules.dashboard.schemas import DashboardBundleResponse
from app.modules.dashboard.service import DashboardService

router = APIRouter(prefix="/api/portfolios/{portfolio_id}", tags=["dashboard"])


def require_dashboard_bundle_enabled() -> None:
    require_feature_enabled("ENABLE_DASHBOARD_BUNDLE")


def get_dashboard_service(db: Annotated[Session, Depends(get_db)]) -> DashboardService:
    return DashboardService(db)


DashboardServiceDep = Annotated[DashboardService, Depends(get_dashboard_service)]


@router.get("/dashboard", response_model=DashboardBundleResponse)
def get_dashboard_bundle(
    portfolio_id: str,
    _: Annotated[None, Depends(require_dashboard_bundle_enabled)],
    user: CurrentUser,
    service: DashboardServiceDep,
):
    return service.get_bundle(portfolio_id=portfolio_id, user=user)
