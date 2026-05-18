from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Holding, Portfolio
from app.modules.holdings.schemas import HoldingCreate, HoldingUpdate


class HoldingRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, *, portfolio: Portfolio, data: HoldingCreate) -> Holding:
        holding = Holding(portfolio_id=portfolio.id, **data.model_dump())
        self.db.add(holding)
        self.db.commit()
        self.db.refresh(holding)
        return holding

    def list_for_portfolio(self, *, portfolio: Portfolio) -> list[Holding]:
        statement = select(Holding).where(Holding.portfolio_id == portfolio.id).order_by(Holding.created_at.desc())
        return list(self.db.scalars(statement).all())

    def get_for_portfolio(self, *, portfolio: Portfolio, holding_id: str) -> Holding | None:
        statement = select(Holding).where(Holding.id == holding_id, Holding.portfolio_id == portfolio.id)
        return self.db.scalar(statement)

    def update(self, *, holding: Holding, data: HoldingUpdate) -> Holding:
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(holding, field, value)
        self.db.add(holding)
        self.db.commit()
        self.db.refresh(holding)
        return holding

    def delete(self, *, holding: Holding) -> None:
        self.db.delete(holding)
        self.db.commit()
