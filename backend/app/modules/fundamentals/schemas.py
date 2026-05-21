from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.modules.common.data_status import DataStatus


FUNDAMENTAL_METRIC_NAMES = (
    "pe_ratio",
    "forward_pe",
    "price_to_book",
    "ev_to_ebitda",
    "peg",
    "roe",
    "roa",
    "operating_margin",
    "net_margin",
    "revenue_growth",
    "eps_growth",
    "dividend_yield",
    "debt_to_equity",
    "market_cap",
)


class FundamentalMetrics(BaseModel):
    pe_ratio: float | None = Field(default=None, ge=0)
    forward_pe: float | None = Field(default=None, ge=0)
    price_to_book: float | None = Field(default=None, ge=0)
    ev_to_ebitda: float | None = Field(default=None, ge=0)
    peg: float | None = Field(default=None, ge=0)
    roe: float | None = None
    roa: float | None = None
    operating_margin: float | None = None
    net_margin: float | None = None
    revenue_growth: float | None = None
    eps_growth: float | None = None
    dividend_yield: float | None = Field(default=None, ge=0)
    debt_to_equity: float | None = Field(default=None, ge=0)
    market_cap: float | None = Field(default=None, ge=0)


class FundamentalsCoverage(BaseModel):
    provider: str
    available_metrics: list[str] = Field(default_factory=list)
    missing_metrics: list[str] = Field(default_factory=list)
    coverage_ratio: float = Field(ge=0, le=1)
    is_complete: bool


class FundamentalsResponse(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    company_name: str | None = None
    currency: str = Field(default="INR", min_length=3, max_length=3)
    metrics: FundamentalMetrics
    coverage: FundamentalsCoverage
    as_of: datetime
    source: str
    data_status: DataStatus

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


class PortfolioFundamentalsCoverage(BaseModel):
    covered_symbols: list[str] = Field(default_factory=list)
    missing_symbols: list[str] = Field(default_factory=list)
    coverage_percent: float = Field(ge=0, le=100)
    weighted_coverage_percent: float = Field(ge=0, le=100)


class PortfolioFundamentalsResponse(BaseModel):
    portfolio_id: str
    fundamentals: list[FundamentalsResponse] = Field(default_factory=list)
    weighted_metrics: FundamentalMetrics
    coverage: PortfolioFundamentalsCoverage
    missing_symbols: list[str] = Field(default_factory=list)
    data_status: DataStatus
    warnings: list[str] = Field(default_factory=list)
