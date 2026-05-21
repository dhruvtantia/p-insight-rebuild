from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.modules.market_data.symbols import normalize_market_symbol


class HoldingBase(BaseModel):
    symbol: str = Field(min_length=1, max_length=24)
    company_name: str | None = Field(default=None, max_length=255)
    quantity: float = Field(gt=0)
    average_cost: float | None = Field(default=None, ge=0)
    current_price: float | None = Field(default=None, ge=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    sector: str | None = Field(default=None, max_length=120)
    asset_class: str | None = Field(default=None, max_length=80)
    exchange: str | None = Field(default=None, max_length=80)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return normalize_market_symbol(value).normalized_symbol

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper()


class HoldingCreate(HoldingBase):
    pass


class HoldingUpdate(BaseModel):
    symbol: str | None = Field(default=None, min_length=1, max_length=24)
    company_name: str | None = Field(default=None, max_length=255)
    quantity: float | None = Field(default=None, gt=0)
    average_cost: float | None = Field(default=None, ge=0)
    current_price: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    sector: str | None = Field(default=None, max_length=120)
    asset_class: str | None = Field(default=None, max_length=80)
    exchange: str | None = Field(default=None, max_length=80)

    @field_validator("symbol")
    @classmethod
    def normalize_optional_symbol(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return normalize_market_symbol(value).normalized_symbol

    @field_validator("currency")
    @classmethod
    def normalize_optional_currency(cls, value: str | None) -> str | None:
        return value.strip().upper() if value is not None else None


class HoldingResponse(BaseModel):
    id: str
    portfolio_id: str
    symbol: str
    company_name: str | None
    quantity: float
    average_cost: float | None
    current_price: float | None
    currency: str
    sector: str | None
    sector_source: str | None = None
    sector_updated_at: datetime | None = None
    asset_class: str | None
    exchange: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def market_value(self) -> float | None:
        if self.current_price is None:
            return None
        return self.quantity * self.current_price

    @computed_field
    @property
    def unrealized_gain_loss(self) -> float | None:
        if self.current_price is None or self.average_cost is None:
            return None
        return self.quantity * (self.current_price - self.average_cost)
