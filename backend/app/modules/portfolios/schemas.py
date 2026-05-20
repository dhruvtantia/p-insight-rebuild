from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.market_data.symbols import normalize_benchmark_symbol


class PortfolioBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    base_currency: str = Field(default="INR", min_length=3, max_length=3)
    benchmark_symbol: str | None = Field(default=None, max_length=24)
    risk_free_rate: float | None = None

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Portfolio name cannot be empty")
        return cleaned

    @field_validator("base_currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("benchmark_symbol")
    @classmethod
    def normalize_benchmark_symbol(cls, value: str | None) -> str | None:
        return normalize_benchmark_symbol(value)


class PortfolioCreate(PortfolioBase):
    pass


class PortfolioUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    base_currency: str | None = Field(default=None, min_length=3, max_length=3)
    benchmark_symbol: str | None = Field(default=None, max_length=24)
    risk_free_rate: float | None = None

    @field_validator("name")
    @classmethod
    def clean_optional_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Portfolio name cannot be empty")
        return cleaned

    @field_validator("base_currency")
    @classmethod
    def normalize_optional_currency(cls, value: str | None) -> str | None:
        return value.strip().upper() if value is not None else None

    @field_validator("benchmark_symbol")
    @classmethod
    def normalize_optional_benchmark_symbol(cls, value: str | None) -> str | None:
        return normalize_benchmark_symbol(value)


class PortfolioResponse(BaseModel):
    id: str
    user_id: str
    name: str
    base_currency: str
    benchmark_symbol: str | None
    risk_free_rate: float | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
