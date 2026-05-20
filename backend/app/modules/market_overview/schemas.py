from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.modules.common.data_status import DataStatus


class MarketStatus(BaseModel):
    market: str = "India"
    exchange: str | None = None
    state: Literal["open", "closed", "pre_open", "post_close", "unknown"]
    timezone: str = "Asia/Kolkata"
    as_of: datetime
    next_open_at: datetime | None = None
    next_close_at: datetime | None = None
    data_status: DataStatus


class MarketIndexCard(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=120)
    value: float = Field(ge=0)
    change: float | None = None
    change_percent: float | None = None
    currency: str = Field(default="INR", min_length=3, max_length=3)
    exchange: str | None = None
    as_of: datetime
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


class SectorIndexCard(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=120)
    sector: str = Field(min_length=1, max_length=120)
    value: float = Field(ge=0)
    change: float | None = None
    change_percent: float | None = None
    exchange: str | None = None
    as_of: datetime
    data_status: DataStatus

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if not cleaned:
            raise ValueError("Symbol cannot be empty")
        return cleaned


class MarketMover(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    company_name: str
    last_price: float = Field(ge=0)
    change: float | None = None
    change_percent: float
    currency: str = Field(default="INR", min_length=3, max_length=3)
    exchange: str | None = None
    sector: str | None = None
    as_of: datetime
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


class MarketOverviewResponse(BaseModel):
    market_status: MarketStatus
    major_indices: list[MarketIndexCard] = Field(default_factory=list)
    sector_indices: list[SectorIndexCard] = Field(default_factory=list)
    top_gainers: list[MarketMover] = Field(default_factory=list)
    top_losers: list[MarketMover] = Field(default_factory=list)
    generated_at: datetime
    data_status: DataStatus
