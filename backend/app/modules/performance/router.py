from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.core.feature_flags import require_feature_enabled
from app.db.session import get_db
from app.modules.performance.schemas import PortfolioPerformanceHistory
from app.modules.performance.service import PerformanceService

router = APIRouter(prefix="/api/portfolios/{portfolio_id}/performance", tags=["performance"])


def require_performance_history_enabled() -> None:
    require_feature_enabled("ENABLE_PERFORMANCE_HISTORY")


def get_performance_service(db: Annotated[Session, Depends(get_db)]) -> PerformanceService:
    return PerformanceService(db)


PerformanceServiceDep = Annotated[PerformanceService, Depends(get_performance_service)]


@router.get("/history", response_model=PortfolioPerformanceHistory)
def get_performance_history(
    portfolio_id: str,
    _: Annotated[None, Depends(require_performance_history_enabled)],
    user: CurrentUser,
    service: PerformanceServiceDep,
    period: Annotated[str, Query(min_length=1)] = "1Y",
):
    return service.get_history(portfolio_id=portfolio_id, user=user, period=period)
