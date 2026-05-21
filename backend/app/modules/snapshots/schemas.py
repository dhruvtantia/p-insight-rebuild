from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.analytics.schemas import AllocationBucket, ConcentrationRisk


class SnapshotCreate(BaseModel):
    label: str | None = Field(default=None, max_length=120)


class SnapshotPrice(BaseModel):
    symbol: str
    current_price: float | None
    currency: str


class SnapshotHolding(BaseModel):
    holding_id: str
    symbol: str
    company_name: str | None = None
    quantity: float
    average_cost: float | None = None
    current_price: float | None = None
    currency: str
    sector: str | None = None
    asset_class: str | None = None
    exchange: str | None = None
    market_value: float | None = None
    cost_basis: float | None = None
    weight: float


class SnapshotTotals(BaseModel):
    total_value: float
    holdings_value: float
    cash_value: float | None = None
    cost_basis: float


class SnapshotSummary(BaseModel):
    id: str
    portfolio_id: str
    label: str | None = None
    as_of: datetime
    total_value: float
    holdings_value: float
    cash_value: float | None = None
    cost_basis: float
    holdings_count: int
    created_at: datetime


class SnapshotResponse(SnapshotSummary):
    holdings: list[SnapshotHolding] = Field(default_factory=list)
    prices: list[SnapshotPrice] = Field(default_factory=list)
    sector_allocation: list[AllocationBucket] = Field(default_factory=list)
    concentration_summary: ConcentrationRisk
    generated_at: datetime


class QuantityChange(BaseModel):
    symbol: str
    from_quantity: float
    to_quantity: float
    quantity_change: float


class HoldingValueChange(BaseModel):
    symbol: str
    from_value: float | None = None
    to_value: float | None = None
    value_change: float | None = None


class SnapshotValueChanges(BaseModel):
    from_total_value: float
    to_total_value: float
    total_value_change: float
    holdings: list[HoldingValueChange] = Field(default_factory=list)


class SectorAllocationChange(BaseModel):
    name: str
    from_value: float
    to_value: float
    value_change: float
    from_weight: float
    to_weight: float
    weight_change: float


class ConcentrationChange(BaseModel):
    from_status: str
    to_status: str
    from_largest_symbol: str | None = None
    to_largest_symbol: str | None = None
    from_top_5_weight: float
    to_top_5_weight: float
    top_5_weight_change: float


class SnapshotCompareResponse(BaseModel):
    portfolio_id: str
    from_snapshot_id: str
    to_snapshot_id: str
    added_holdings: list[SnapshotHolding] = Field(default_factory=list)
    removed_holdings: list[SnapshotHolding] = Field(default_factory=list)
    quantity_changes: list[QuantityChange] = Field(default_factory=list)
    value_changes: SnapshotValueChanges
    sector_allocation_changes: list[SectorAllocationChange] = Field(default_factory=list)
    concentration_changes: ConcentrationChange
