import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AnalyticsResult, Holding, User
from app.modules.analytics.calculators.allocation import calculate_allocation
from app.modules.analytics.calculators.performance import (
    build_holding_analytics,
    calculate_performance,
    calculate_summary,
)
from app.modules.analytics.calculators.risk import calculate_risk
from app.modules.analytics.calculators.rules import evaluate_rules
from app.modules.analytics.schemas import (
    AllocationAnalytics,
    AnalyticsRecalculateResponse,
    AnalyticsSnapshotRecord,
    PerformanceAnalytics,
    PortfolioAnalyticsBundle,
    PortfolioAnalyticsSummary,
    RiskAnalytics,
    RuleInsight,
)
from app.modules.portfolios.service import PortfolioService


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
        self.portfolio_service = PortfolioService(db)

    def get_summary(self, *, portfolio_id: str, user: User) -> PortfolioAnalyticsSummary:
        return self._build_bundle(portfolio_id=portfolio_id, user=user).summary

    def get_allocation(self, *, portfolio_id: str, user: User) -> AllocationAnalytics:
        return self._build_bundle(portfolio_id=portfolio_id, user=user).allocation

    def get_risk(self, *, portfolio_id: str, user: User) -> RiskAnalytics:
        return self._build_bundle(portfolio_id=portfolio_id, user=user).risk

    def get_performance(self, *, portfolio_id: str, user: User) -> PerformanceAnalytics:
        return self._build_bundle(portfolio_id=portfolio_id, user=user).performance

    def get_rules(self, *, portfolio_id: str, user: User) -> list[RuleInsight]:
        return self._build_bundle(portfolio_id=portfolio_id, user=user).rules

    def recalculate(self, *, portfolio_id: str, user: User) -> AnalyticsRecalculateResponse:
        bundle = self._build_bundle(portfolio_id=portfolio_id, user=user)
        stored_results = [
            self._store_result(portfolio_id=portfolio_id, result_type="summary", payload=bundle.summary),
            self._store_result(portfolio_id=portfolio_id, result_type="allocation", payload=bundle.allocation),
            self._store_result(portfolio_id=portfolio_id, result_type="risk", payload=bundle.risk),
            self._store_result(portfolio_id=portfolio_id, result_type="performance", payload=bundle.performance),
            self._store_result(portfolio_id=portfolio_id, result_type="rules", payload=bundle.rules),
            self._store_result(portfolio_id=portfolio_id, result_type="analytics_bundle", payload=bundle),
        ]
        self.db.commit()
        for result in stored_results:
            self.db.refresh(result)

        return AnalyticsRecalculateResponse(
            portfolio_id=portfolio_id,
            generated_at=bundle.generated_at,
            stored_results=[
                AnalyticsSnapshotRecord(id=result.id, result_type=result.result_type) for result in stored_results
            ],
            analytics=bundle,
        )

    def _build_bundle(self, *, portfolio_id: str, user: User) -> PortfolioAnalyticsBundle:
        portfolio = self.portfolio_service.get_portfolio(portfolio_id=portfolio_id, user=user)
        holdings = self._list_holdings(portfolio_id=portfolio.id)
        holding_analytics = build_holding_analytics(holdings)
        summary = calculate_summary(
            portfolio_id=portfolio.id,
            base_currency=portfolio.base_currency,
            holdings=holding_analytics,
        )
        allocation = calculate_allocation(holding_analytics)
        risk = calculate_risk(holding_analytics)
        performance = calculate_performance(holding_analytics)
        rules = evaluate_rules(
            holdings=holding_analytics,
            allocation=allocation,
            base_currency=portfolio.base_currency,
        )

        return PortfolioAnalyticsBundle(
            portfolio_id=portfolio.id,
            generated_at=datetime.now(timezone.utc),
            summary=summary,
            allocation=allocation,
            risk=risk,
            performance=performance,
            rules=rules,
        )

    def _list_holdings(self, *, portfolio_id: str) -> list[Holding]:
        statement = select(Holding).where(Holding.portfolio_id == portfolio_id).order_by(Holding.symbol.asc())
        return list(self.db.scalars(statement).all())

    def _store_result(self, *, portfolio_id: str, result_type: str, payload: object) -> AnalyticsResult:
        if hasattr(payload, "model_dump"):
            result_payload = payload.model_dump(mode="json")  # type: ignore[attr-defined]
        elif isinstance(payload, list):
            result_payload = [
                item.model_dump(mode="json") if hasattr(item, "model_dump") else item for item in payload
            ]
        else:
            result_payload = payload

        result = AnalyticsResult(
            portfolio_id=portfolio_id,
            result_type=result_type,
            result_json=json.dumps(result_payload, sort_keys=True),
            generated_at=datetime.now(timezone.utc),
        )
        self.db.add(result)
        return result
