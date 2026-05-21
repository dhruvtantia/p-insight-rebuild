from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.core.feature_flags import require_feature_enabled
from app.db.session import get_db
from app.modules.peers.schemas import PeerComparisonResponse
from app.modules.peers.service import PeerComparisonService

router = APIRouter(prefix="/api/portfolios/{portfolio_id}/peers", tags=["peers"])


def require_peers_enabled() -> None:
    require_feature_enabled("ENABLE_PEERS")


def get_peer_comparison_service(db: Annotated[Session, Depends(get_db)]) -> PeerComparisonService:
    return PeerComparisonService(db)


PeerComparisonServiceDep = Annotated[PeerComparisonService, Depends(get_peer_comparison_service)]


@router.get("/{symbol}", response_model=PeerComparisonResponse)
def compare_peers(
    portfolio_id: str,
    symbol: str,
    _: Annotated[None, Depends(require_peers_enabled)],
    user: CurrentUser,
    service: PeerComparisonServiceDep,
):
    return service.compare(portfolio_id=portfolio_id, symbol=symbol, user=user)
