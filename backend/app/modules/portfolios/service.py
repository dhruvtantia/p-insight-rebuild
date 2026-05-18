from sqlalchemy.orm import Session

from app.db.models import Portfolio, User
from app.modules.portfolios.errors import PortfolioNotFoundError
from app.modules.portfolios.repository import PortfolioRepository
from app.modules.portfolios.schemas import PortfolioCreate, PortfolioUpdate


class PortfolioService:
    def __init__(self, db: Session):
        self.repository = PortfolioRepository(db)

    def create_portfolio(self, *, user: User, data: PortfolioCreate) -> Portfolio:
        return self.repository.create(user=user, data=data)

    def list_portfolios(self, *, user: User) -> list[Portfolio]:
        return self.repository.list_for_user(user=user)

    def get_portfolio(self, *, portfolio_id: str, user: User) -> Portfolio:
        portfolio = self.repository.get_for_user(portfolio_id=portfolio_id, user=user)
        if portfolio is None:
            raise PortfolioNotFoundError()
        return portfolio

    def update_portfolio(self, *, portfolio_id: str, user: User, data: PortfolioUpdate) -> Portfolio:
        portfolio = self.get_portfolio(portfolio_id=portfolio_id, user=user)
        return self.repository.update(portfolio=portfolio, data=data)

    def delete_portfolio(self, *, portfolio_id: str, user: User) -> None:
        portfolio = self.get_portfolio(portfolio_id=portfolio_id, user=user)
        self.repository.delete(portfolio=portfolio)
