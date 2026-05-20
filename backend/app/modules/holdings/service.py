from sqlalchemy.orm import Session

from app.db.models import Holding, User
from app.modules.holdings.errors import HoldingNotFoundError
from app.modules.holdings.repository import HoldingRepository
from app.modules.holdings.schemas import HoldingCreate, HoldingUpdate
from app.modules.market_data.symbols import normalize_market_symbol
from app.modules.portfolios.service import PortfolioService


class HoldingService:
    def __init__(self, db: Session):
        self.repository = HoldingRepository(db)
        self.portfolio_service = PortfolioService(db)

    def create_holding(self, *, portfolio_id: str, user: User, data: HoldingCreate) -> Holding:
        portfolio = self.portfolio_service.get_portfolio(portfolio_id=portfolio_id, user=user)
        symbol_metadata = normalize_market_symbol(data.symbol)
        normalized_data = data.model_copy(
            update={
                "symbol": symbol_metadata.normalized_symbol,
                "exchange": data.exchange or symbol_metadata.exchange,
                "asset_class": data.asset_class or symbol_metadata.asset_class,
            }
        )
        return self.repository.create(portfolio=portfolio, data=normalized_data)

    def list_holdings(self, *, portfolio_id: str, user: User) -> list[Holding]:
        portfolio = self.portfolio_service.get_portfolio(portfolio_id=portfolio_id, user=user)
        return self.repository.list_for_portfolio(portfolio=portfolio)

    def get_holding(self, *, portfolio_id: str, holding_id: str, user: User) -> Holding:
        portfolio = self.portfolio_service.get_portfolio(portfolio_id=portfolio_id, user=user)
        holding = self.repository.get_for_portfolio(portfolio=portfolio, holding_id=holding_id)
        if holding is None:
            raise HoldingNotFoundError()
        return holding

    def update_holding(
        self,
        *,
        portfolio_id: str,
        holding_id: str,
        user: User,
        data: HoldingUpdate,
    ) -> Holding:
        holding = self.get_holding(portfolio_id=portfolio_id, holding_id=holding_id, user=user)
        if data.symbol is None:
            return self.repository.update(holding=holding, data=data)

        symbol_metadata = normalize_market_symbol(data.symbol)
        normalized_data = data.model_copy(
            update={
                "symbol": symbol_metadata.normalized_symbol,
                "exchange": data.exchange or symbol_metadata.exchange,
                "asset_class": data.asset_class or symbol_metadata.asset_class,
            }
        )
        return self.repository.update(holding=holding, data=normalized_data)

    def delete_holding(self, *, portfolio_id: str, holding_id: str, user: User) -> None:
        holding = self.get_holding(portfolio_id=portfolio_id, holding_id=holding_id, user=user)
        self.repository.delete(holding=holding)
