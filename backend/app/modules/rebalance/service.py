from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ValidationAppError
from app.db.models import Holding, User
from app.modules.portfolios.service import PortfolioService
from app.modules.rebalance.schemas import RebalanceTicket, RebalanceTicketRequest, RebalanceTicketsResponse


TRADE_EPSILON = 0.000001


class RebalanceTicketService:
    def __init__(self, db: Session):
        self.db = db
        self.portfolio_service = PortfolioService(db)

    def estimate_tickets(
        self,
        *,
        portfolio_id: str,
        user: User,
        data: RebalanceTicketRequest,
    ) -> RebalanceTicketsResponse:
        self._validate_request(data)
        portfolio = self.portfolio_service.get_portfolio(portfolio_id=portfolio_id, user=user)
        holdings = self._list_holdings(portfolio_id=portfolio.id)
        holdings_by_symbol = {holding.symbol: holding for holding in holdings}
        current_values = self._current_values(holdings)
        current_portfolio_value = round(sum(current_values.values()), 6)
        net_cash = (data.cash_contribution or 0) - (data.cash_withdrawal or 0)
        target_portfolio_value = round(max(current_portfolio_value + net_cash, 0), 6)
        warnings = ["Rebalance tickets are estimates only. No trades were executed or persisted."]
        if data.cash_withdrawal and data.cash_withdrawal > current_portfolio_value:
            warnings.append("Cash withdrawal exceeds current priced portfolio value; target value was floored at zero.")

        missing_price_symbols = [
            symbol for symbol, holding in holdings_by_symbol.items() if holding.current_price is None
        ]
        for symbol in missing_price_symbols:
            warnings.append(f"Current price is missing for {symbol}; no ticket was generated for that symbol.")

        unknown_symbols = sorted(symbol for symbol in data.target_weights if symbol not in holdings_by_symbol)
        for symbol in unknown_symbols:
            warnings.append(f"{symbol} is not a current holding; no ticket was generated because no latest holding price is available.")

        tickets: list[RebalanceTicket] = []
        for symbol in sorted(set(holdings_by_symbol) | set(data.target_weights)):
            holding = holdings_by_symbol.get(symbol)
            if holding is None or holding.current_price is None:
                continue
            current_value = current_values.get(symbol, 0)
            target_weight = data.target_weights.get(symbol, 0) / 100
            target_value = round(target_portfolio_value * target_weight, 6)
            value_delta = round(target_value - current_value, 6)
            action = self._action(value_delta)
            shares_to_trade = round(abs(value_delta) / float(holding.current_price), 6) if action != "hold" else 0
            tickets.append(
                RebalanceTicket(
                    symbol=symbol,
                    current_weight=round(current_value / current_portfolio_value, 6)
                    if current_portfolio_value > 0
                    else 0,
                    target_weight=round(target_weight, 6),
                    current_value=current_value,
                    target_value=target_value,
                    action=action,
                    estimated_shares_to_trade=shares_to_trade,
                    estimated_cash_needed=round(value_delta, 6) if value_delta > 0 else 0,
                    estimated_cash_generated=round(abs(value_delta), 6) if value_delta < 0 else 0,
                )
            )

        estimated_cash_needed = round(sum(ticket.estimated_cash_needed for ticket in tickets), 6)
        estimated_cash_generated = round(sum(ticket.estimated_cash_generated for ticket in tickets), 6)
        leftover_cash = round((data.cash_contribution or 0) + estimated_cash_generated - estimated_cash_needed - (data.cash_withdrawal or 0), 6)

        return RebalanceTicketsResponse(
            portfolio_id=portfolio.id,
            tickets=tickets,
            current_portfolio_value=current_portfolio_value,
            target_portfolio_value=target_portfolio_value,
            estimated_cash_needed=estimated_cash_needed,
            estimated_cash_generated=estimated_cash_generated,
            leftover_cash=leftover_cash,
            warnings=warnings,
            execution_required=False,
        )

    def _list_holdings(self, *, portfolio_id: str) -> list[Holding]:
        statement = select(Holding).where(Holding.portfolio_id == portfolio_id).order_by(Holding.symbol.asc())
        return list(self.db.scalars(statement).all())

    def _current_values(self, holdings: list[Holding]) -> dict[str, float]:
        return {
            holding.symbol: (
                round(float(holding.quantity) * float(holding.current_price), 6)
                if holding.current_price is not None
                else 0
            )
            for holding in holdings
        }

    def _action(self, value_delta: float):
        if value_delta > TRADE_EPSILON:
            return "buy"
        if value_delta < -TRADE_EPSILON:
            return "sell"
        return "hold"

    def _validate_request(self, data: RebalanceTicketRequest) -> None:
        if any(weight < 0 for weight in data.target_weights.values()):
            raise ValidationAppError("Target weights must be non-negative")
        total_weight = round(sum(data.target_weights.values()), 6)
        if total_weight != 100:
            raise ValidationAppError("Target weights must sum to 100")
        if data.cash_contribution and data.cash_withdrawal:
            raise ValidationAppError("Use either cash_contribution or cash_withdrawal, not both")
