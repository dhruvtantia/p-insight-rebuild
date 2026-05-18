from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PriceQuote(BaseModel):
    symbol: str
    price: float = Field(ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    source: str
    as_of: datetime
    is_realtime: bool = False

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


class BatchPriceResponse(BaseModel):
    prices: list[PriceQuote]


class PriceHistoryPoint(BaseModel):
    symbol: str
    date: str
    close: float = Field(ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    source: str


class PriceHistoryResponse(BaseModel):
    symbol: str
    start: str
    end: str
    prices: list[PriceHistoryPoint]


class CompanyProfile(BaseModel):
    symbol: str
    company_name: str | None = None
    currency: str = "USD"
    sector: str | None = None
    asset_class: str | None = None
    exchange: str | None = None
    source: str


class FxRate(BaseModel):
    from_currency: str
    to_currency: str
    rate: float = Field(gt=0)
    source: str
    as_of: datetime
    is_realtime: bool = False


class HoldingPriceRefreshItem(BaseModel):
    holding_id: str
    symbol: str
    previous_price: float | None
    current_price: float
    currency: str
    source: str
    as_of: datetime
    is_realtime: bool

    model_config = ConfigDict(from_attributes=True)


class PortfolioPriceRefreshResponse(BaseModel):
    portfolio_id: str
    refreshed_count: int
    prices: list[PriceQuote]
    holdings: list[HoldingPriceRefreshItem]
