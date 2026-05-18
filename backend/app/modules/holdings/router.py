from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.db.session import get_db
from app.modules.holdings.schemas import HoldingCreate, HoldingResponse, HoldingUpdate
from app.modules.holdings.service import HoldingService

router = APIRouter(prefix="/api/portfolios/{portfolio_id}/holdings", tags=["holdings"])


def get_holding_service(db: Annotated[Session, Depends(get_db)]) -> HoldingService:
    return HoldingService(db)


HoldingServiceDep = Annotated[HoldingService, Depends(get_holding_service)]


@router.get("", response_model=list[HoldingResponse])
def list_holdings(portfolio_id: str, user: CurrentUser, service: HoldingServiceDep):
    return service.list_holdings(portfolio_id=portfolio_id, user=user)


@router.post("", response_model=HoldingResponse, status_code=status.HTTP_201_CREATED)
def create_holding(
    portfolio_id: str,
    data: HoldingCreate,
    user: CurrentUser,
    service: HoldingServiceDep,
):
    return service.create_holding(portfolio_id=portfolio_id, user=user, data=data)


@router.patch("/{holding_id}", response_model=HoldingResponse)
def update_holding(
    portfolio_id: str,
    holding_id: str,
    data: HoldingUpdate,
    user: CurrentUser,
    service: HoldingServiceDep,
):
    return service.update_holding(
        portfolio_id=portfolio_id,
        holding_id=holding_id,
        user=user,
        data=data,
    )


@router.delete("/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_holding(
    portfolio_id: str,
    holding_id: str,
    user: CurrentUser,
    service: HoldingServiceDep,
):
    service.delete_holding(portfolio_id=portfolio_id, holding_id=holding_id, user=user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
