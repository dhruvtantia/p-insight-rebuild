from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.db.session import get_db
from app.modules.analytics.schemas import (
    AllocationAnalytics,
    AnalyticsRecalculateResponse,
    PerformanceAnalytics,
    PortfolioAnalyticsSummary,
    RiskAnalytics,
    RuleInsight,
)
from app.modules.analytics.service import AnalyticsService

router = APIRouter(prefix="/api/portfolios/{portfolio_id}/analytics", tags=["analytics"])


def get_analytics_service(db: Annotated[Session, Depends(get_db)]) -> AnalyticsService:
    return AnalyticsService(db)


AnalyticsServiceDep = Annotated[AnalyticsService, Depends(get_analytics_service)]


@router.get("/summary", response_model=PortfolioAnalyticsSummary)
def get_summary(portfolio_id: str, user: CurrentUser, service: AnalyticsServiceDep):
    return service.get_summary(portfolio_id=portfolio_id, user=user)


@router.get("/allocation", response_model=AllocationAnalytics)
def get_allocation(portfolio_id: str, user: CurrentUser, service: AnalyticsServiceDep):
    return service.get_allocation(portfolio_id=portfolio_id, user=user)


@router.get("/risk", response_model=RiskAnalytics)
def get_risk(portfolio_id: str, user: CurrentUser, service: AnalyticsServiceDep):
    return service.get_risk(portfolio_id=portfolio_id, user=user)


@router.get("/performance", response_model=PerformanceAnalytics)
def get_performance(portfolio_id: str, user: CurrentUser, service: AnalyticsServiceDep):
    return service.get_performance(portfolio_id=portfolio_id, user=user)


@router.get("/rules", response_model=list[RuleInsight])
def get_rules(portfolio_id: str, user: CurrentUser, service: AnalyticsServiceDep):
    return service.get_rules(portfolio_id=portfolio_id, user=user)


@router.post("/recalculate", response_model=AnalyticsRecalculateResponse)
def recalculate(portfolio_id: str, user: CurrentUser, service: AnalyticsServiceDep):
    return service.recalculate(portfolio_id=portfolio_id, user=user)
