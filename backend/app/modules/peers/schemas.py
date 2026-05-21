from typing import Literal

from pydantic import BaseModel, Field

from app.modules.fundamentals.schemas import FundamentalsResponse


MetricDirection = Literal["lower_is_better", "higher_is_better"]


class PeerSetQuality(BaseModel):
    source: Literal["static_india_peer_map"] = "static_india_peer_map"
    is_static: bool = True
    peer_count: int = Field(ge=0)
    covered_peer_count: int = Field(ge=0)
    missing_peer_symbols: list[str] = Field(default_factory=list)
    coverage_percent: float = Field(ge=0, le=100)
    is_sparse: bool


class MetricComparisonRow(BaseModel):
    metric: str
    direction: MetricDirection
    selected_value: float | None = None
    peer_values: dict[str, float | None] = Field(default_factory=dict)
    peer_average: float | None = None
    selected_rank: int | None = None


class PeerComparisonResponse(BaseModel):
    portfolio_id: str
    symbol: str
    selected_company: FundamentalsResponse
    peer_companies: list[FundamentalsResponse] = Field(default_factory=list)
    metric_comparison_table: list[MetricComparisonRow] = Field(default_factory=list)
    simple_ranks: dict[str, dict[str, int | None]] = Field(default_factory=dict)
    peer_set_quality: PeerSetQuality
    warnings: list[str] = Field(default_factory=list)
