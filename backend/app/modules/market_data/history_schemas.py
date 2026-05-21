from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.modules.common.data_status import DataStatus


HistoricalPeriod = Literal["1M", "3M", "6M", "1Y", "5Y"]


class HistoricalPricePoint(BaseModel):
    date: date
    close: float = Field(ge=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    data_status: DataStatus

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper()


class HistoricalPriceSeries(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    period: HistoricalPeriod
    currency: str = Field(default="INR", min_length=3, max_length=3)
    start_date: date
    end_date: date
    prices: list[HistoricalPricePoint] = Field(default_factory=list)
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


class HistoricalPriceResponse(BaseModel):
    period: HistoricalPeriod
    start_date: date
    end_date: date
    generated_at: datetime
    series: list[HistoricalPriceSeries] = Field(default_factory=list)
    data_status: DataStatus
