from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.core.feature_flags import require_feature_enabled
from app.db.session import get_db
from app.modules.simulator.schemas import SimulationRequest, SimulationResponse
from app.modules.simulator.service import PortfolioSimulatorService

router = APIRouter(prefix="/api/portfolios/{portfolio_id}", tags=["simulator"])


def require_simulator_enabled() -> None:
    require_feature_enabled("ENABLE_SIMULATOR")


def get_simulator_service(db: Annotated[Session, Depends(get_db)]) -> PortfolioSimulatorService:
    return PortfolioSimulatorService(db)


SimulatorServiceDep = Annotated[PortfolioSimulatorService, Depends(get_simulator_service)]


@router.post("/simulate", response_model=SimulationResponse)
def simulate_portfolio(
    portfolio_id: str,
    data: SimulationRequest,
    _: Annotated[None, Depends(require_simulator_enabled)],
    user: CurrentUser,
    service: SimulatorServiceDep,
):
    return service.simulate(portfolio_id=portfolio_id, user=user, data=data)
