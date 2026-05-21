import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, ValidationAppError
from app.db.models import Holding, PortfolioSnapshot, User
from app.modules.analytics.calculators.allocation import calculate_allocation
from app.modules.analytics.calculators.concentration import calculate_concentration_risk
from app.modules.analytics.calculators.performance import build_holding_analytics, calculate_summary
from app.modules.analytics.schemas import AllocationBucket, ConcentrationRisk
from app.modules.portfolios.service import PortfolioService
from app.modules.snapshots.schemas import (
    ConcentrationChange,
    HoldingValueChange,
    QuantityChange,
    SectorAllocationChange,
    SnapshotCompareResponse,
    SnapshotCreate,
    SnapshotHolding,
    SnapshotPrice,
    SnapshotResponse,
    SnapshotSummary,
    SnapshotValueChanges,
)


class SnapshotNotFoundError(NotFoundError):
    def __init__(self) -> None:
        super().__init__("Snapshot not found")


class SnapshotService:
    def __init__(self, db: Session):
        self.db = db
        self.portfolio_service = PortfolioService(db)

    def create_snapshot(self, *, portfolio_id: str, user: User, data: SnapshotCreate) -> SnapshotResponse:
        portfolio = self.portfolio_service.get_portfolio(portfolio_id=portfolio_id, user=user)
        holdings = self._list_holdings(portfolio_id=portfolio.id)
        generated_at = datetime.now(UTC)
        holding_analytics = build_holding_analytics(holdings)
        summary = calculate_summary(
            portfolio_id=portfolio.id,
            base_currency=portfolio.base_currency,
            holdings=holding_analytics,
        )
        allocation = calculate_allocation(holding_analytics)
        concentration = calculate_concentration_risk(holding_analytics)
        snapshot_holdings = [
            SnapshotHolding(
                holding_id=holding.holding_id,
                symbol=holding.symbol,
                company_name=self._company_name_for_holding(holdings, holding.holding_id),
                quantity=holding.quantity,
                average_cost=holding.average_cost,
                current_price=holding.current_price,
                currency=holding.currency,
                sector=holding.sector,
                asset_class=holding.asset_class,
                exchange=self._exchange_for_holding(holdings, holding.holding_id),
                market_value=holding.market_value,
                cost_basis=holding.cost_basis,
                weight=holding.weight,
            )
            for holding in holding_analytics
        ]
        prices = [
            SnapshotPrice(symbol=holding.symbol, current_price=holding.current_price, currency=holding.currency)
            for holding in snapshot_holdings
        ]
        payload = {
            "schema_version": 1,
            "snapshot_type": "portfolio_state",
            "source": "manual",
            "label": data.label,
            "generated_at": generated_at.isoformat(),
            "portfolio": {
                "id": portfolio.id,
                "name": portfolio.name,
                "base_currency": portfolio.base_currency,
                "benchmark_symbol": portfolio.benchmark_symbol,
            },
            "holdings": [holding.model_dump(mode="json") for holding in snapshot_holdings],
            "prices": [price.model_dump(mode="json") for price in prices],
            "totals": {
                "total_value": summary.total_portfolio_value,
                "holdings_value": summary.total_portfolio_value,
                "cash_value": 0,
                "cost_basis": summary.total_cost_basis,
            },
            "sector_allocation": [bucket.model_dump(mode="json") for bucket in allocation.sector_allocation],
            "concentration_summary": concentration.model_dump(mode="json"),
            "analytics_summary": summary.model_dump(mode="json"),
        }
        snapshot = PortfolioSnapshot(
            portfolio_id=portfolio.id,
            total_value=summary.total_portfolio_value,
            holdings_value=summary.total_portfolio_value,
            cash_value=0,
            snapshot_json=json.dumps(payload, sort_keys=True),
            as_of=generated_at,
        )
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        return self._response_from_record(snapshot)

    def list_snapshots(self, *, portfolio_id: str, user: User) -> list[SnapshotSummary]:
        portfolio = self.portfolio_service.get_portfolio(portfolio_id=portfolio_id, user=user)
        statement = (
            select(PortfolioSnapshot)
            .where(PortfolioSnapshot.portfolio_id == portfolio.id)
            .order_by(PortfolioSnapshot.as_of.desc(), PortfolioSnapshot.created_at.desc())
        )
        return [self._summary_from_record(snapshot) for snapshot in self.db.scalars(statement).all()]

    def compare_snapshots(
        self,
        *,
        portfolio_id: str,
        user: User,
        from_id: str,
        to_id: str,
    ) -> SnapshotCompareResponse:
        portfolio = self.portfolio_service.get_portfolio(portfolio_id=portfolio_id, user=user)
        from_snapshot = self._get_snapshot_record(portfolio_id=portfolio.id, snapshot_id=from_id)
        to_snapshot = self._get_snapshot_record(portfolio_id=portfolio.id, snapshot_id=to_id)
        from_response = self._response_from_record(from_snapshot)
        to_response = self._response_from_record(to_snapshot)
        from_holdings = {holding.symbol: holding for holding in from_response.holdings}
        to_holdings = {holding.symbol: holding for holding in to_response.holdings}
        from_symbols = set(from_holdings)
        to_symbols = set(to_holdings)

        return SnapshotCompareResponse(
            portfolio_id=portfolio.id,
            from_snapshot_id=from_snapshot.id,
            to_snapshot_id=to_snapshot.id,
            added_holdings=[to_holdings[symbol] for symbol in sorted(to_symbols - from_symbols)],
            removed_holdings=[from_holdings[symbol] for symbol in sorted(from_symbols - to_symbols)],
            quantity_changes=self._quantity_changes(from_holdings=from_holdings, to_holdings=to_holdings),
            value_changes=self._value_changes(from_response=from_response, to_response=to_response),
            sector_allocation_changes=self._sector_allocation_changes(
                from_response.sector_allocation,
                to_response.sector_allocation,
            ),
            concentration_changes=self._concentration_change(
                from_response.concentration_summary,
                to_response.concentration_summary,
            ),
        )

    def _list_holdings(self, *, portfolio_id: str) -> list[Holding]:
        statement = select(Holding).where(Holding.portfolio_id == portfolio_id).order_by(Holding.symbol.asc())
        return list(self.db.scalars(statement).all())

    def _get_snapshot_record(self, *, portfolio_id: str, snapshot_id: str) -> PortfolioSnapshot:
        statement = select(PortfolioSnapshot).where(
            PortfolioSnapshot.id == snapshot_id,
            PortfolioSnapshot.portfolio_id == portfolio_id,
        )
        snapshot = self.db.scalar(statement)
        if snapshot is None:
            raise SnapshotNotFoundError()
        return snapshot

    def _response_from_record(self, snapshot: PortfolioSnapshot) -> SnapshotResponse:
        payload = self._payload(snapshot)
        summary = self._summary_from_payload(snapshot=snapshot, payload=payload)
        return SnapshotResponse(
            **summary.model_dump(),
            holdings=[SnapshotHolding(**holding) for holding in payload.get("holdings", [])],
            prices=[SnapshotPrice(**price) for price in payload.get("prices", [])],
            sector_allocation=[AllocationBucket(**bucket) for bucket in payload.get("sector_allocation", [])],
            concentration_summary=ConcentrationRisk(**payload["concentration_summary"]),
            generated_at=self._parse_datetime(payload.get("generated_at")) or snapshot.as_of,
        )

    def _summary_from_record(self, snapshot: PortfolioSnapshot) -> SnapshotSummary:
        return self._summary_from_payload(snapshot=snapshot, payload=self._payload(snapshot))

    def _summary_from_payload(self, *, snapshot: PortfolioSnapshot, payload: dict[str, Any]) -> SnapshotSummary:
        totals = payload.get("totals", {})
        holdings = payload.get("holdings", [])
        return SnapshotSummary(
            id=snapshot.id,
            portfolio_id=snapshot.portfolio_id,
            label=payload.get("label"),
            as_of=snapshot.as_of,
            total_value=float(snapshot.total_value or totals.get("total_value") or 0),
            holdings_value=float(snapshot.holdings_value or totals.get("holdings_value") or 0),
            cash_value=float(snapshot.cash_value) if snapshot.cash_value is not None else totals.get("cash_value"),
            cost_basis=float(totals.get("cost_basis") or 0),
            holdings_count=len(holdings) if isinstance(holdings, list) else 0,
            created_at=snapshot.created_at,
        )

    def _payload(self, snapshot: PortfolioSnapshot) -> dict[str, Any]:
        try:
            payload = json.loads(snapshot.snapshot_json)
        except json.JSONDecodeError as exc:
            raise ValidationAppError("Snapshot payload is not valid JSON") from exc
        if not isinstance(payload, dict):
            raise ValidationAppError("Snapshot payload must be a JSON object")
        return payload

    def _quantity_changes(
        self,
        *,
        from_holdings: dict[str, SnapshotHolding],
        to_holdings: dict[str, SnapshotHolding],
    ) -> list[QuantityChange]:
        changes: list[QuantityChange] = []
        for symbol in sorted(set(from_holdings) & set(to_holdings)):
            from_quantity = from_holdings[symbol].quantity
            to_quantity = to_holdings[symbol].quantity
            if from_quantity != to_quantity:
                changes.append(
                    QuantityChange(
                        symbol=symbol,
                        from_quantity=from_quantity,
                        to_quantity=to_quantity,
                        quantity_change=round(to_quantity - from_quantity, 6),
                    )
                )
        return changes

    def _value_changes(
        self,
        *,
        from_response: SnapshotResponse,
        to_response: SnapshotResponse,
    ) -> SnapshotValueChanges:
        from_holdings = {holding.symbol: holding for holding in from_response.holdings}
        to_holdings = {holding.symbol: holding for holding in to_response.holdings}
        holding_changes: list[HoldingValueChange] = []
        for symbol in sorted(set(from_holdings) | set(to_holdings)):
            from_value = from_holdings.get(symbol).market_value if symbol in from_holdings else None
            to_value = to_holdings.get(symbol).market_value if symbol in to_holdings else None
            value_change = round((to_value or 0) - (from_value or 0), 6)
            if value_change != 0 or from_value != to_value:
                holding_changes.append(
                    HoldingValueChange(
                        symbol=symbol,
                        from_value=from_value,
                        to_value=to_value,
                        value_change=value_change,
                    )
                )
        return SnapshotValueChanges(
            from_total_value=from_response.total_value,
            to_total_value=to_response.total_value,
            total_value_change=round(to_response.total_value - from_response.total_value, 6),
            holdings=holding_changes,
        )

    def _sector_allocation_changes(
        self,
        from_allocation: list[AllocationBucket],
        to_allocation: list[AllocationBucket],
    ) -> list[SectorAllocationChange]:
        from_buckets = {bucket.name: bucket for bucket in from_allocation}
        to_buckets = {bucket.name: bucket for bucket in to_allocation}
        changes: list[SectorAllocationChange] = []
        for name in sorted(set(from_buckets) | set(to_buckets)):
            from_bucket = from_buckets.get(name)
            to_bucket = to_buckets.get(name)
            from_value = from_bucket.value if from_bucket is not None else 0
            to_value = to_bucket.value if to_bucket is not None else 0
            from_weight = from_bucket.weight if from_bucket is not None else 0
            to_weight = to_bucket.weight if to_bucket is not None else 0
            if from_value != to_value or from_weight != to_weight:
                changes.append(
                    SectorAllocationChange(
                        name=name,
                        from_value=from_value,
                        to_value=to_value,
                        value_change=round(to_value - from_value, 6),
                        from_weight=from_weight,
                        to_weight=to_weight,
                        weight_change=round(to_weight - from_weight, 6),
                    )
                )
        return changes

    def _concentration_change(
        self,
        from_concentration: ConcentrationRisk,
        to_concentration: ConcentrationRisk,
    ) -> ConcentrationChange:
        return ConcentrationChange(
            from_status=from_concentration.status,
            to_status=to_concentration.status,
            from_largest_symbol=(
                from_concentration.largest_holding.symbol if from_concentration.largest_holding else None
            ),
            to_largest_symbol=to_concentration.largest_holding.symbol if to_concentration.largest_holding else None,
            from_top_5_weight=from_concentration.top_5_weight,
            to_top_5_weight=to_concentration.top_5_weight,
            top_5_weight_change=round(to_concentration.top_5_weight - from_concentration.top_5_weight, 6),
        )

    def _company_name_for_holding(self, holdings: list[Holding], holding_id: str) -> str | None:
        match = next((holding for holding in holdings if holding.id == holding_id), None)
        return match.company_name if match is not None else None

    def _exchange_for_holding(self, holdings: list[Holding], holding_id: str) -> str | None:
        match = next((holding for holding in holdings if holding.id == holding_id), None)
        return match.exchange if match is not None else None

    def _parse_datetime(self, value: object) -> datetime | None:
        if not isinstance(value, str):
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
