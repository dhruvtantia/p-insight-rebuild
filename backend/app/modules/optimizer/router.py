from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.core.feature_flags import require_feature_enabled
from app.db.session import get_db
from app.modules.optimizer.schemas import OptimizerRequest, OptimizerResponse
from app.modules.optimizer.service import OptimizerService

router = APIRouter(prefix="/api/portfolios/{portfolio_id}", tags=["optimizer"])


def require_optimizer_enabled() -> None:
    require_feature_enabled("ENABLE_OPTIMIZER")


def get_optimizer_service(db: Annotated[Session, Depends(get_db)]) -> OptimizerService:
    return OptimizerService(db)


OptimizerServiceDep = Annotated[OptimizerService, Depends(get_optimizer_service)]


@router.post("/optimize", response_model=OptimizerResponse)
def optimize_portfolio(
    portfolio_id: str,
    data: OptimizerRequest,
    _: Annotated[None, Depends(require_optimizer_enabled)],
    user: CurrentUser,
    service: OptimizerServiceDep,
):
    return service.optimize(portfolio_id=portfolio_id, user=user, data=data)
