from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.core.feature_flags import require_feature_enabled
from app.db.session import get_db
from app.modules.fundamentals.schemas import FundamentalsResponse, PortfolioFundamentalsResponse
from app.modules.fundamentals.service import FundamentalsService

router = APIRouter(tags=["fundamentals"])


def require_fundamentals_enabled() -> None:
    require_feature_enabled("ENABLE_FUNDAMENTALS")


def get_fundamentals_service(db: Annotated[Session, Depends(get_db)]) -> FundamentalsService:
    return FundamentalsService(db=db)


FundamentalsServiceDep = Annotated[FundamentalsService, Depends(get_fundamentals_service)]


@router.get("/api/assets/{symbol}/fundamentals", response_model=FundamentalsResponse)
def get_asset_fundamentals(
    symbol: str,
    _: Annotated[None, Depends(require_fundamentals_enabled)],
    service: FundamentalsServiceDep,
):
    return service.get_fundamentals(symbol=symbol)


@router.get("/api/portfolios/{portfolio_id}/fundamentals", response_model=PortfolioFundamentalsResponse)
def get_portfolio_fundamentals(
    portfolio_id: str,
    _: Annotated[None, Depends(require_fundamentals_enabled)],
    user: CurrentUser,
    service: FundamentalsServiceDep,
):
    return service.get_portfolio_fundamentals(portfolio_id=portfolio_id, user=user)
