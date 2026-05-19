from typing import Annotated

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.db.session import get_db
from app.modules.ai_advisor.schemas import (
    AIAdvisorResponse,
    AIConversationDetail,
    AIConversationListItem,
    AIQuestionRequest,
    AISummaryRequest,
)
from app.modules.ai_advisor.service import AIAdvisorService

portfolio_router = APIRouter(prefix="/api/portfolios/{portfolio_id}/ai", tags=["ai-advisor"])
conversation_router = APIRouter(prefix="/api/ai", tags=["ai-advisor"])


def get_ai_advisor_service(db: Annotated[Session, Depends(get_db)]) -> AIAdvisorService:
    return AIAdvisorService(db)


AIAdvisorServiceDep = Annotated[AIAdvisorService, Depends(get_ai_advisor_service)]


@portfolio_router.post("/summary", response_model=AIAdvisorResponse)
def create_summary(
    portfolio_id: str,
    user: CurrentUser,
    service: AIAdvisorServiceDep,
    _: AISummaryRequest | None = Body(default=None),
):
    return service.create_summary(portfolio_id=portfolio_id, user=user)


@portfolio_router.post("/question", response_model=AIAdvisorResponse)
def answer_question(
    portfolio_id: str,
    data: AIQuestionRequest,
    user: CurrentUser,
    service: AIAdvisorServiceDep,
):
    return service.answer_question(portfolio_id=portfolio_id, user=user, question=data.question)


@portfolio_router.get("/conversations", response_model=list[AIConversationListItem])
def list_conversations(portfolio_id: str, user: CurrentUser, service: AIAdvisorServiceDep):
    return service.list_conversations(portfolio_id=portfolio_id, user=user)


@conversation_router.get("/conversations/{conversation_id}", response_model=AIConversationDetail)
def get_conversation(conversation_id: str, user: CurrentUser, service: AIAdvisorServiceDep):
    return service.get_conversation(conversation_id=conversation_id, user=user)
