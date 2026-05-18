from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class HoldingAnalytics(BaseModel):
    holding_id: str
    symbol: str
    quantity: float
    average_cost: float | None
    current_price: float | None
    currency: str
    sector: str | None
    asset_class: str | None
    market_value: float | None
    cost_basis: float | None
    unrealized_gain_loss: float | None
    unrealized_gain_loss_pct: float | None
    weight: float


class AllocationBucket(BaseModel):
    name: str
    value: float
    weight: float
    symbols: list[str] = Field(default_factory=list)


class LargestHolding(BaseModel):
    symbol: str
    market_value: float
    weight: float


class PerformanceHolding(BaseModel):
    symbol: str
    unrealized_gain_loss: float
    unrealized_gain_loss_pct: float | None


class PerformanceAnalytics(BaseModel):
    total_cost_basis: float
    total_unrealized_gain_loss: float
    total_unrealized_gain_loss_pct: float | None
    top_gainers: list[PerformanceHolding]
    top_losers: list[PerformanceHolding]


class AllocationAnalytics(BaseModel):
    asset_allocation: list[AllocationBucket]
    sector_allocation: list[AllocationBucket]
    currency_exposure: list[AllocationBucket]


class ConcentrationRisk(BaseModel):
    status: Literal["empty", "ok", "moderate", "high"]
    largest_holding: LargestHolding | None
    top_5_weight: float
    message: str


class RiskMetric(BaseModel):
    value: float | None
    status: Literal["ok", "insufficient_history"]
    message: str


class RiskAnalytics(BaseModel):
    volatility: RiskMetric
    sharpe_ratio: RiskMetric
    max_drawdown: RiskMetric
    concentration: ConcentrationRisk


class RuleInsight(BaseModel):
    rule_id: str
    severity: Literal["low", "medium", "high"]
    title: str
    message: str
    affected_symbols: list[str] = Field(default_factory=list)


class PortfolioAnalyticsSummary(BaseModel):
    portfolio_id: str
    base_currency: str
    total_portfolio_value: float
    total_cost_basis: float
    total_unrealized_gain_loss: float
    total_unrealized_gain_loss_pct: float | None
    holdings: list[HoldingAnalytics]
    largest_holding: LargestHolding | None


class PortfolioAnalyticsBundle(BaseModel):
    portfolio_id: str
    generated_at: datetime
    summary: PortfolioAnalyticsSummary
    allocation: AllocationAnalytics
    risk: RiskAnalytics
    performance: PerformanceAnalytics
    rules: list[RuleInsight]


class AnalyticsSnapshotRecord(BaseModel):
    id: str
    result_type: str


class AnalyticsRecalculateResponse(BaseModel):
    portfolio_id: str
    generated_at: datetime
    stored_results: list[AnalyticsSnapshotRecord]
    analytics: PortfolioAnalyticsBundle
