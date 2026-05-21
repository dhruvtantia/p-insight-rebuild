from pydantic import BaseModel, Field, field_validator

from app.modules.market_data.symbols import normalize_market_symbol


class SimulationRequest(BaseModel):
    target_weights: dict[str, float] = Field(default_factory=dict)
    added_symbols: list[str] = Field(default_factory=list)
    removed_symbols: list[str] = Field(default_factory=list)

    @field_validator("target_weights")
    @classmethod
    def normalize_target_weights(cls, value: dict[str, float]) -> dict[str, float]:
        normalized: dict[str, float] = {}
        for symbol, weight in value.items():
            if weight < 0:
                raise ValueError("Target weights must be non-negative")
            normalized_symbol = normalize_market_symbol(symbol).normalized_symbol
            normalized[normalized_symbol] = float(weight)
        return normalized

    @field_validator("added_symbols", "removed_symbols")
    @classmethod
    def normalize_symbols(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for symbol in value:
            normalized_symbol = normalize_market_symbol(symbol).normalized_symbol
            if normalized_symbol not in seen:
                seen.add(normalized_symbol)
                normalized.append(normalized_symbol)
        return normalized


class AllocationLine(BaseModel):
    symbol: str
    current_value: float = Field(ge=0)
    weight: float = Field(ge=0)
    sector: str | None = None
    asset_class: str | None = None


class SimulatedAllocationLine(BaseModel):
    symbol: str
    estimated_value: float = Field(ge=0)
    weight: float = Field(ge=0)
    current_value: float | None = Field(default=None, ge=0)
    is_added: bool = False
    is_removed: bool = False
    sector: str | None = None
    asset_class: str | None = None


class ConcentrationChange(BaseModel):
    current_largest_symbol: str | None = None
    simulated_largest_symbol: str | None = None
    current_largest_weight: float = Field(ge=0)
    simulated_largest_weight: float = Field(ge=0)
    largest_weight_change: float
    current_hhi: float = Field(ge=0)
    simulated_hhi: float = Field(ge=0)
    hhi_change: float


class EstimatedValueDistribution(BaseModel):
    total_value: float = Field(ge=0)
    symbols: list[SimulatedAllocationLine] = Field(default_factory=list)


class SimulationResponse(BaseModel):
    portfolio_id: str
    current_allocation: list[AllocationLine] = Field(default_factory=list)
    simulated_allocation: list[SimulatedAllocationLine] = Field(default_factory=list)
    concentration_change: ConcentrationChange
    estimated_value_distribution: EstimatedValueDistribution
    warnings: list[str] = Field(default_factory=list)
    persisted: bool = False
