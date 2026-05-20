from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.modules.common.data_status import DataStatus


class DashboardKpis(BaseModel):
    portfolio_id: str
    base_currency: str = Field(min_length=3, max_length=3)
    total_invested: float = Field(ge=0)
    current_value: float = Field(ge=0)
    unrealized_pnl: float
    return_percent: float | None = None
    holdings_count: int = Field(ge=0)
    priced_holdings_count: int = Field(ge=0)
    largest_holding_symbol: str | None = None
    largest_holding_weight: float | None = Field(default=None, ge=0, le=1)
    cash_weight: float | None = Field(default=None, ge=0, le=1)

    @field_validator("base_currency")
    @classmethod
    def normalize_base_currency(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("largest_holding_symbol")
    @classmethod
    def normalize_largest_holding_symbol(cls, value: str | None) -> str | None:
        if value is None:
            return value
        cleaned = value.strip().upper()
        return cleaned or None


class DashboardTopHolding(BaseModel):
    holding_id: str
    symbol: str = Field(min_length=1, max_length=32)
    company_name: str | None = None
    market_value: float = Field(ge=0)
    weight: float = Field(ge=0, le=1)
    unrealized_gain_loss: float | None = None
    unrealized_gain_loss_pct: float | None = None
    currency: str = Field(min_length=3, max_length=3)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if not cleaned:
            raise ValueError("Symbol cannot be empty")
        return cleaned

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper()


class DashboardAllocationItem(BaseModel):
    dimension: Literal["asset_class", "sector", "currency"]
    name: str = Field(min_length=1, max_length=120)
    value: float = Field(ge=0)
    weight: float = Field(ge=0, le=1)
    symbols: list[str] = Field(default_factory=list)

    @field_validator("symbols")
    @classmethod
    def normalize_symbols(cls, value: list[str]) -> list[str]:
        return [symbol.strip().upper() for symbol in value if symbol.strip()]


class DashboardRiskSummary(BaseModel):
    concentration_status: Literal["empty", "ok", "moderate", "high"]
    largest_holding_symbol: str | None = None
    largest_holding_weight: float | None = Field(default=None, ge=0, le=1)
    top_3_weight: float = Field(ge=0, le=1)
    hhi: float = Field(ge=0, le=1)
    volatility: float | None = None
    volatility_status: Literal["ok", "insufficient_history"]
    sharpe_ratio: float | None = None
    sharpe_ratio_status: Literal["ok", "insufficient_history"]
    max_drawdown: float | None = None
    max_drawdown_status: Literal["ok", "insufficient_history"]
    message: str

    @field_validator("largest_holding_symbol")
    @classmethod
    def normalize_largest_holding_symbol(cls, value: str | None) -> str | None:
        if value is None:
            return value
        cleaned = value.strip().upper()
        return cleaned or None


class DashboardDataQuality(BaseModel):
    holdings_count: int = Field(ge=0)
    priced_holdings_count: int = Field(ge=0)
    missing_price_count: int = Field(ge=0)
    missing_cost_basis_count: int = Field(ge=0)
    stale_price_count: int = Field(ge=0)
    warnings: list[str] = Field(default_factory=list)
    data_status: DataStatus


class DashboardActionItem(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    priority: Literal["low", "medium", "high"]
    category: Literal["setup", "data_quality", "risk", "allocation", "performance"]
    title: str = Field(min_length=1, max_length=140)
    message: str = Field(min_length=1)
    affected_symbols: list[str] = Field(default_factory=list)
    recommended_action: Literal[
        "add_holdings",
        "refresh_prices",
        "review_holdings",
        "review_allocation",
        "review_risk",
        "review_performance",
    ] | None = None

    @field_validator("affected_symbols")
    @classmethod
    def normalize_affected_symbols(cls, value: list[str]) -> list[str]:
        return [symbol.strip().upper() for symbol in value if symbol.strip()]


class DashboardBundleResponse(BaseModel):
    portfolio_id: str
    generated_at: datetime
    kpis: DashboardKpis
    sector_allocation: list[DashboardAllocationItem] = Field(default_factory=list)
    asset_allocation: list[DashboardAllocationItem] = Field(default_factory=list)
    top_holdings: list[DashboardTopHolding] = Field(default_factory=list)
    risk: DashboardRiskSummary
    data_quality: DashboardDataQuality
    action_items: list[DashboardActionItem] = Field(default_factory=list)
    data_status: DataStatus
