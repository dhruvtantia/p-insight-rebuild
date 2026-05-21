from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.modules.common.data_status import DataStatus
from app.modules.market_data.history_schemas import HistoricalPeriod


class PerformanceAssumptions(BaseModel):
    method: Literal["synthetic_current_holdings"] = "synthetic_current_holdings"
    assumes_current_quantities_held_throughout: bool = True
    not_transaction_aware: bool = True
    not_xirr: bool = True
    not_time_weighted_return: bool = True


class PortfolioValuePoint(BaseModel):
    date: date
    value: float = Field(ge=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper()


class NormalizedReturnPoint(BaseModel):
    date: date
    normalized_return: float


class PortfolioPerformanceHistory(BaseModel):
    portfolio_id: str
    period: HistoricalPeriod
    start_date: date
    end_date: date
    generated_at: datetime
    base_currency: str = Field(default="INR", min_length=3, max_length=3)
    benchmark_symbol: str = Field(default="NIFTY50", min_length=1, max_length=32)
    portfolio_value_series: list[PortfolioValuePoint] = Field(default_factory=list)
    portfolio_normalized_return_series: list[NormalizedReturnPoint] = Field(default_factory=list)
    benchmark_normalized_return_series: list[NormalizedReturnPoint] = Field(default_factory=list)
    missing_price_symbols: list[str] = Field(default_factory=list)
    assumptions: PerformanceAssumptions = Field(default_factory=PerformanceAssumptions)
    data_status: DataStatus

    @field_validator("base_currency")
    @classmethod
    def normalize_base_currency(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("benchmark_symbol")
    @classmethod
    def normalize_benchmark_symbol(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if not cleaned:
            raise ValueError("Benchmark symbol cannot be empty")
        return cleaned
