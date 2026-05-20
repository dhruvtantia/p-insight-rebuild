from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.feature_flags import require_feature_enabled
from app.db.session import get_db
from app.modules.market_overview.schemas import MarketOverviewResponse
from app.modules.market_overview.service import MarketOverviewService

router = APIRouter(prefix="/api/market", tags=["market-overview"])


def require_market_overview_enabled() -> None:
    require_feature_enabled("ENABLE_MARKET_OVERVIEW")


@router.get("/overview", response_model=MarketOverviewResponse)
def get_market_overview(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_market_overview_enabled)],
):
    return MarketOverviewService(db).get_overview()
