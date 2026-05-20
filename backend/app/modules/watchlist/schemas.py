from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.market_data.symbols import normalize_market_symbol


class WatchlistCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=24)
    name: str | None = Field(default=None, max_length=255)
    notes: str | None = None

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return normalize_market_symbol(value).normalized_symbol

    @field_validator("name", "notes")
    @classmethod
    def empty_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class WatchlistItemResponse(BaseModel):
    id: str
    user_id: str
    symbol: str
    name: str | None
    notes: str | None
    current_price: float | None
    price_currency: str | None
    price_source: str | None
    price_as_of: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
