from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.modules.market_data.symbols import normalize_market_symbol


class RebalanceTicketRequest(BaseModel):
    target_weights: dict[str, float] = Field(min_length=1)
    cash_contribution: float | None = Field(default=None, ge=0)
    cash_withdrawal: float | None = Field(default=None, ge=0)

    @field_validator("target_weights")
    @classmethod
    def normalize_target_weights(cls, value: dict[str, float]) -> dict[str, float]:
        normalized_weights: dict[str, float] = {}
        for symbol, weight in value.items():
            normalized_symbol = normalize_market_symbol(symbol).normalized_symbol
            normalized_weights[normalized_symbol] = float(weight)
        return normalized_weights


class RebalanceTicket(BaseModel):
    symbol: str
    current_weight: float = Field(ge=0)
    target_weight: float = Field(ge=0)
    current_value: float = Field(ge=0)
    target_value: float = Field(ge=0)
    action: Literal["buy", "sell", "hold"]
    estimated_shares_to_trade: float = Field(ge=0)
    estimated_cash_needed: float = Field(ge=0)
    estimated_cash_generated: float = Field(ge=0)


class RebalanceTicketsResponse(BaseModel):
    portfolio_id: str
    tickets: list[RebalanceTicket] = Field(default_factory=list)
    current_portfolio_value: float = Field(ge=0)
    target_portfolio_value: float = Field(ge=0)
    estimated_cash_needed: float = Field(ge=0)
    estimated_cash_generated: float = Field(ge=0)
    leftover_cash: float
    warnings: list[str] = Field(default_factory=list)
    execution_required: bool = False
