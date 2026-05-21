from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Holding, User
from app.modules.portfolios.service import PortfolioService
from app.modules.simulator.schemas import (
    AllocationLine,
    ConcentrationChange,
    EstimatedValueDistribution,
    SimulatedAllocationLine,
    SimulationRequest,
    SimulationResponse,
)


class PortfolioSimulatorService:
    def __init__(self, db: Session):
        self.db = db
        self.portfolio_service = PortfolioService(db)

    def simulate(self, *, portfolio_id: str, user: User, data: SimulationRequest) -> SimulationResponse:
        portfolio = self.portfolio_service.get_portfolio(portfolio_id=portfolio_id, user=user)
        holdings = self._list_holdings(portfolio_id=portfolio.id)
        holding_by_symbol = {holding.symbol: holding for holding in holdings}
        current_values = self._current_values(holdings)
        total_value = round(sum(current_values.values()), 6)
        warnings = self._initial_warnings(
            data=data,
            holding_by_symbol=holding_by_symbol,
            total_value=total_value,
        )
        current_allocation = self._current_allocation(holdings=holdings, current_values=current_values, total_value=total_value)
        simulated_weights = self._simulated_weights(
            data=data,
            current_values=current_values,
            total_value=total_value,
            warnings=warnings,
        )
        simulated_allocation = self._simulated_allocation(
            simulated_weights=simulated_weights,
            current_values=current_values,
            total_value=total_value,
            holding_by_symbol=holding_by_symbol,
            removed_symbols=set(data.removed_symbols),
        )

        return SimulationResponse(
            portfolio_id=portfolio.id,
            current_allocation=current_allocation,
            simulated_allocation=simulated_allocation,
            concentration_change=self._concentration_change(
                current=current_allocation,
                simulated=simulated_allocation,
            ),
            estimated_value_distribution=EstimatedValueDistribution(
                total_value=total_value,
                symbols=simulated_allocation,
            ),
            warnings=warnings,
            persisted=False,
        )

    def _list_holdings(self, *, portfolio_id: str) -> list[Holding]:
        statement = select(Holding).where(Holding.portfolio_id == portfolio_id).order_by(Holding.symbol.asc())
        return list(self.db.scalars(statement).all())

    def _current_values(self, holdings: list[Holding]) -> dict[str, float]:
        values: dict[str, float] = {}
        for holding in holdings:
            if holding.current_price is None:
                values[holding.symbol] = 0
            else:
                values[holding.symbol] = round(float(holding.quantity) * float(holding.current_price), 6)
        return values

    def _current_allocation(
        self,
        *,
        holdings: list[Holding],
        current_values: dict[str, float],
        total_value: float,
    ) -> list[AllocationLine]:
        return [
            AllocationLine(
                symbol=holding.symbol,
                current_value=current_values.get(holding.symbol, 0),
                weight=round(current_values.get(holding.symbol, 0) / total_value, 6) if total_value > 0 else 0,
                sector=holding.sector,
                asset_class=holding.asset_class,
            )
            for holding in holdings
        ]

    def _simulated_weights(
        self,
        *,
        data: SimulationRequest,
        current_values: dict[str, float],
        total_value: float,
        warnings: list[str],
    ) -> dict[str, float]:
        removed_symbols = set(data.removed_symbols)
        if data.target_weights:
            active_target_weights = {
                symbol: weight
                for symbol, weight in data.target_weights.items()
                if symbol not in removed_symbols
            }
            removed_targets = sorted(set(data.target_weights) & removed_symbols)
            if removed_targets:
                warnings.append(
                    f"Target weights for removed symbol(s) were ignored: {', '.join(removed_targets)}."
                )
            total_target_weight = sum(active_target_weights.values())
            if total_target_weight <= 0:
                warnings.append("Target weights sum to zero after removals; simulated allocation is empty.")
                return {}
            if round(total_target_weight, 6) != 100:
                warnings.append(
                    f"Target weights sum to {round(total_target_weight, 6)} instead of 100; weights were normalized for simulation."
                )
            return {
                symbol: round(weight / total_target_weight, 6)
                for symbol, weight in active_target_weights.items()
            }

        active_values = {
            symbol: value
            for symbol, value in current_values.items()
            if symbol not in removed_symbols
        }
        active_total = sum(active_values.values())
        weights = {
            symbol: round(value / active_total, 6)
            for symbol, value in active_values.items()
            if active_total > 0
        }
        for symbol in data.added_symbols:
            weights.setdefault(symbol, 0)
        if total_value <= 0:
            warnings.append("Simulation has no priced portfolio value; estimated distribution is zero.")
        return weights

    def _simulated_allocation(
        self,
        *,
        simulated_weights: dict[str, float],
        current_values: dict[str, float],
        total_value: float,
        holding_by_symbol: dict[str, Holding],
        removed_symbols: set[str],
    ) -> list[SimulatedAllocationLine]:
        lines: list[SimulatedAllocationLine] = []
        for symbol, weight in sorted(simulated_weights.items(), key=lambda item: (-item[1], item[0])):
            holding = holding_by_symbol.get(symbol)
            lines.append(
                SimulatedAllocationLine(
                    symbol=symbol,
                    estimated_value=round(total_value * weight, 6),
                    weight=weight,
                    current_value=current_values.get(symbol),
                    is_added=holding is None,
                    is_removed=False,
                    sector=holding.sector if holding is not None else None,
                    asset_class=holding.asset_class if holding is not None else None,
                )
            )
        for symbol in sorted(removed_symbols & set(holding_by_symbol)):
            holding = holding_by_symbol[symbol]
            lines.append(
                SimulatedAllocationLine(
                    symbol=symbol,
                    estimated_value=0,
                    weight=0,
                    current_value=current_values.get(symbol, 0),
                    is_added=False,
                    is_removed=True,
                    sector=holding.sector,
                    asset_class=holding.asset_class,
                )
            )
        return lines

    def _concentration_change(
        self,
        *,
        current: list[AllocationLine],
        simulated: list[SimulatedAllocationLine],
    ) -> ConcentrationChange:
        current_largest = max(current, key=lambda item: item.weight, default=None)
        simulated_active = [item for item in simulated if not item.is_removed]
        simulated_largest = max(simulated_active, key=lambda item: item.weight, default=None)
        current_weight = current_largest.weight if current_largest is not None else 0
        simulated_weight = simulated_largest.weight if simulated_largest is not None else 0
        current_hhi = self._hhi([item.weight for item in current])
        simulated_hhi = self._hhi([item.weight for item in simulated_active])
        return ConcentrationChange(
            current_largest_symbol=current_largest.symbol if current_largest is not None else None,
            simulated_largest_symbol=simulated_largest.symbol if simulated_largest is not None else None,
            current_largest_weight=current_weight,
            simulated_largest_weight=simulated_weight,
            largest_weight_change=round(simulated_weight - current_weight, 6),
            current_hhi=current_hhi,
            simulated_hhi=simulated_hhi,
            hhi_change=round(simulated_hhi - current_hhi, 6),
        )

    def _hhi(self, weights: list[float]) -> float:
        return round(sum(weight * weight for weight in weights), 6)

    def _initial_warnings(
        self,
        *,
        data: SimulationRequest,
        holding_by_symbol: dict[str, Holding],
        total_value: float,
    ) -> list[str]:
        warnings = ["Simulation is hypothetical only. No trades were executed or persisted."]
        if total_value <= 0:
            warnings.append("Current portfolio has no priced value; estimated values may be zero.")
        unknown_added = sorted(symbol for symbol in data.added_symbols if symbol not in holding_by_symbol)
        if unknown_added:
            warnings.append(
                f"Added symbol(s) are not current holdings and no price was fetched: {', '.join(unknown_added)}."
            )
        missing_removed = sorted(symbol for symbol in data.removed_symbols if symbol not in holding_by_symbol)
        if missing_removed:
            warnings.append(f"Removed symbol(s) are not current holdings: {', '.join(missing_removed)}.")
        missing_prices = sorted(
            symbol for symbol, holding in holding_by_symbol.items() if holding.current_price is None
        )
        if missing_prices:
            warnings.append(f"Current prices are missing for: {', '.join(missing_prices)}.")
        return warnings
