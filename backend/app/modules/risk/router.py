from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.core.feature_flags import require_feature_enabled
from app.db.session import get_db
from app.modules.risk.schemas import RiskV2Response
from app.modules.risk.service import RiskV2Service

router = APIRouter(prefix="/api/portfolios/{portfolio_id}", tags=["risk"])


def require_risk_v2_enabled() -> None:
    require_feature_enabled("ENABLE_RISK_V2")


def get_risk_v2_service(db: Annotated[Session, Depends(get_db)]) -> RiskV2Service:
    return RiskV2Service(db)


RiskV2ServiceDep = Annotated[RiskV2Service, Depends(get_risk_v2_service)]


@router.get("/risk", response_model=RiskV2Response)
def get_risk_v2(
    portfolio_id: str,
    _: Annotated[None, Depends(require_risk_v2_enabled)],
    user: CurrentUser,
    service: RiskV2ServiceDep,
    period: Annotated[str, Query(min_length=1)] = "1Y",
):
    return service.get_risk(portfolio_id=portfolio_id, user=user, period=period)
