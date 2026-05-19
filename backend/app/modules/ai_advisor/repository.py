import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AIConversation, AIMessage, Portfolio, User


class AIAdvisorRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_conversation(self, *, portfolio_id: str, title: str, mode: str, context: dict) -> AIConversation:
        conversation = AIConversation(
            portfolio_id=portfolio_id,
            title=title,
            context_json=json.dumps({"mode": mode, "context": context}, sort_keys=True),
        )
        self.db.add(conversation)
        self.db.flush()
        return conversation

    def add_message(
        self,
        *,
        conversation_id: str,
        role: str,
        content: str,
        provider: str | None = None,
        model: str | None = None,
        metadata: dict | None = None,
    ) -> AIMessage:
        message = AIMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            provider=provider,
            model=model,
            metadata_json=json.dumps(metadata or {}, sort_keys=True),
        )
        self.db.add(message)
        self.db.flush()
        return message

    def list_conversations_for_portfolio(self, *, portfolio_id: str) -> list[AIConversation]:
        statement = (
            select(AIConversation)
            .where(AIConversation.portfolio_id == portfolio_id)
            .order_by(AIConversation.created_at.desc())
        )
        return list(self.db.scalars(statement).all())

    def get_conversation_for_user(self, *, conversation_id: str, user: User) -> AIConversation | None:
        statement = (
            select(AIConversation)
            .join(Portfolio, Portfolio.id == AIConversation.portfolio_id)
            .where(AIConversation.id == conversation_id, Portfolio.user_id == user.id)
        )
        return self.db.scalar(statement)

    def list_messages(self, *, conversation_id: str) -> list[AIMessage]:
        statement = select(AIMessage).where(AIMessage.conversation_id == conversation_id).order_by(AIMessage.created_at.asc())
        return list(self.db.scalars(statement).all())
