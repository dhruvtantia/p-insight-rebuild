from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.core.feature_flags import require_feature_enabled
from app.db.session import get_db
from app.modules.rebalance.schemas import RebalanceTicketRequest, RebalanceTicketsResponse
from app.modules.rebalance.service import RebalanceTicketService

router = APIRouter(prefix="/api/portfolios/{portfolio_id}/rebalance", tags=["rebalance"])


def require_rebalance_tickets_enabled() -> None:
    require_feature_enabled("ENABLE_REBALANCE_TICKETS")


def get_rebalance_ticket_service(db: Annotated[Session, Depends(get_db)]) -> RebalanceTicketService:
    return RebalanceTicketService(db)


RebalanceTicketServiceDep = Annotated[RebalanceTicketService, Depends(get_rebalance_ticket_service)]


@router.post("/tickets", response_model=RebalanceTicketsResponse)
def estimate_rebalance_tickets(
    portfolio_id: str,
    data: RebalanceTicketRequest,
    _: Annotated[None, Depends(require_rebalance_tickets_enabled)],
    user: CurrentUser,
    service: RebalanceTicketServiceDep,
):
    return service.estimate_tickets(portfolio_id=portfolio_id, user=user, data=data)
