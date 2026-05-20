from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.common.data_status import DataStatus


class PriceQuote(BaseModel):
    symbol: str
    price: float = Field(ge=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    source: str
    as_of: datetime
    is_realtime: bool = False
    data_status: DataStatus | None = None

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
    currency: str = Field(default="INR", min_length=3, max_length=3)
    source: str
    data_status: DataStatus | None = None


class PriceHistoryResponse(BaseModel):
    symbol: str
    start: str
    end: str
    prices: list[PriceHistoryPoint]


class CompanyProfile(BaseModel):
    symbol: str
    company_name: str | None = None
    currency: str = "INR"
    sector: str | None = None
    asset_class: str | None = None
    exchange: str | None = None
    source: str
    data_status: DataStatus | None = None


class FxRate(BaseModel):
    from_currency: str
    to_currency: str
    rate: float = Field(gt=0)
    source: str
    as_of: datetime
    is_realtime: bool = False
    data_status: DataStatus | None = None


class HoldingPriceRefreshItem(BaseModel):
    holding_id: str
    symbol: str
    previous_price: float | None
    current_price: float
    currency: str
    source: str
    as_of: datetime
    is_realtime: bool
    data_status: DataStatus | None = None

    model_config = ConfigDict(from_attributes=True)


class PortfolioPriceRefreshResponse(BaseModel):
    portfolio_id: str
    refreshed_count: int
    prices: list[PriceQuote]
    holdings: list[HoldingPriceRefreshItem]
