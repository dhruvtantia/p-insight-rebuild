from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Holding, Portfolio, User
from app.modules.portfolios.schemas import PortfolioCreate, PortfolioUpdate


class PortfolioRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, *, user: User, data: PortfolioCreate) -> Portfolio:
        portfolio = Portfolio(user_id=user.id, **data.model_dump())
        self.db.add(portfolio)
        self.db.commit()
        self.db.refresh(portfolio)
        return portfolio

    def list_for_user(self, *, user: User) -> list[Portfolio]:
        statement = select(Portfolio).where(Portfolio.user_id == user.id).order_by(Portfolio.created_at.desc())
        return list(self.db.scalars(statement).all())

    def get_for_user(self, *, portfolio_id: str, user: User) -> Portfolio | None:
        statement = select(Portfolio).where(Portfolio.id == portfolio_id, Portfolio.user_id == user.id)
        return self.db.scalar(statement)

    def update(self, *, portfolio: Portfolio, data: PortfolioUpdate) -> Portfolio:
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(portfolio, field, value)
        self.db.add(portfolio)
        self.db.commit()
        self.db.refresh(portfolio)
        return portfolio

    def delete(self, *, portfolio: Portfolio) -> None:
        holdings = self.db.scalars(select(Holding).where(Holding.portfolio_id == portfolio.id)).all()
        for holding in holdings:
            self.db.delete(holding)
        self.db.delete(portfolio)
        self.db.commit()
