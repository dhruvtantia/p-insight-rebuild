from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.modules.common.data_status import DataStatus
from app.modules.market_data.history_schemas import HistoricalPeriod


class OptimizerRequest(BaseModel):
    period: HistoricalPeriod = "1Y"
    frontier_points: int = Field(default=5, ge=2, le=20)


class OptimizerAssumptions(BaseModel):
    long_only: bool = True
    no_taxes: bool = True
    no_transaction_costs: bool = True
    no_liquidity_constraints: bool = True
    historical_estimates_only: bool = True
    not_investment_advice: bool = True


class OptimizerMetricSet(BaseModel):
    expected_annual_return: float | None = None
    annualized_volatility: float | None = None
    sharpe_ratio: float | None = None


class OptimizedWeights(BaseModel):
    target_weights: dict[str, float] = Field(default_factory=dict)
    metrics: OptimizerMetricSet


class EfficientFrontierPoint(BaseModel):
    index: int = Field(ge=0)
    target_return: float | None = None
    annualized_volatility: float | None = None
    sharpe_ratio: float | None = None
    weights: dict[str, float] = Field(default_factory=dict)


class OptimizerResponse(BaseModel):
    portfolio_id: str
    period: HistoricalPeriod
    generated_at: datetime
    status: Literal["ok", "insufficient_history", "unsupported"]
    current_portfolio_metrics: OptimizerMetricSet
    current_weights: dict[str, float] = Field(default_factory=dict)
    min_variance_target_weights: OptimizedWeights
    max_sharpe_target_weights: OptimizedWeights
    efficient_frontier_points: list[EfficientFrontierPoint] = Field(default_factory=list)
    assumptions: OptimizerAssumptions = Field(default_factory=OptimizerAssumptions)
    data_status: DataStatus
    warnings: list[str] = Field(default_factory=list)
