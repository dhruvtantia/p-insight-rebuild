from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BrokerConnectionCreate(BaseModel):
    provider: str = Field(min_length=1, max_length=80)

    @field_validator("provider")
    @classmethod
    def clean_provider(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Provider cannot be empty")
        return cleaned


class BrokerConnectionResponse(BaseModel):
    id: str
    provider: str
    status: str
    message: str
    metadata: dict
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BrokerProviderPlaceholder(BaseModel):
    provider: str
    display_name: str
    status: Literal["coming_soon"]
    message: str
