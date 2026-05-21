from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.modules.common.data_status import DataStatus
from app.modules.market_data.history_schemas import HistoricalPeriod
from app.modules.performance.schemas import PerformanceAssumptions


MetricStatusCode = Literal["ok", "insufficient_history", "undefined"]


class RiskMetricStatus(BaseModel):
    status: MetricStatusCode
    message: str


class RiskV2Response(BaseModel):
    portfolio_id: str
    period: HistoricalPeriod
    generated_at: datetime
    benchmark_symbol: str = Field(default="NIFTY50", min_length=1, max_length=32)
    observations: int = Field(ge=0)
    annualized_return: float | None = None
    annualized_volatility: float | None = None
    sharpe_ratio: float | None = None
    sortino_ratio: float | None = None
    max_drawdown: float | None = None
    downside_deviation: float | None = None
    value_at_risk_95: float | None = None
    beta_vs_benchmark: float | None = None
    tracking_error: float | None = None
    information_ratio: float | None = None
    correlation_matrix: dict[str, dict[str, float | None]] | None = None
    metric_status: dict[str, RiskMetricStatus]
    assumptions: PerformanceAssumptions = Field(default_factory=PerformanceAssumptions)
    data_status: DataStatus
