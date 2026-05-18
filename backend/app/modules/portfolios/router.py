from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.db.session import get_db
from app.modules.portfolios.schemas import PortfolioCreate, PortfolioResponse, PortfolioUpdate
from app.modules.portfolios.service import PortfolioService

router = APIRouter(prefix="/api/portfolios", tags=["portfolios"])


def get_portfolio_service(db: Annotated[Session, Depends(get_db)]) -> PortfolioService:
    return PortfolioService(db)


PortfolioServiceDep = Annotated[PortfolioService, Depends(get_portfolio_service)]


@router.post("", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
def create_portfolio(data: PortfolioCreate, user: CurrentUser, service: PortfolioServiceDep):
    return service.create_portfolio(user=user, data=data)


@router.get("", response_model=list[PortfolioResponse])
def list_portfolios(user: CurrentUser, service: PortfolioServiceDep):
    return service.list_portfolios(user=user)


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio(portfolio_id: str, user: CurrentUser, service: PortfolioServiceDep):
    return service.get_portfolio(portfolio_id=portfolio_id, user=user)


@router.patch("/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio(
    portfolio_id: str,
    data: PortfolioUpdate,
    user: CurrentUser,
    service: PortfolioServiceDep,
):
    return service.update_portfolio(portfolio_id=portfolio_id, user=user, data=data)


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio(portfolio_id: str, user: CurrentUser, service: PortfolioServiceDep):
    service.delete_portfolio(portfolio_id=portfolio_id, user=user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
