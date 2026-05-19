from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import AIConversation, Holding, Portfolio, User


class FeatureUsageSnapshotService:
    def __init__(self, db: Session):
        self.db = db

    def snapshot_for_user(self, *, user: User) -> dict:
        portfolio_count = self.db.scalar(select(func.count()).select_from(Portfolio).where(Portfolio.user_id == user.id)) or 0
        holdings_count = (
            self.db.scalar(
                select(func.count())
                .select_from(Holding)
                .join(Portfolio, Portfolio.id == Holding.portfolio_id)
                .where(Portfolio.user_id == user.id)
            )
            or 0
        )
        ai_conversation_count = (
            self.db.scalar(
                select(func.count())
                .select_from(AIConversation)
                .join(Portfolio, Portfolio.id == AIConversation.portfolio_id)
                .where(Portfolio.user_id == user.id)
            )
            or 0
        )
        return {
            "portfolio_count": portfolio_count,
            "holdings_count": holdings_count,
            "ai_conversation_count": ai_conversation_count,
            "enforcement_enabled": False,
        }
