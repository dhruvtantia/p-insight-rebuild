from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AISummaryRequest(BaseModel):
    pass


class AIQuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class AIAdvisorResponse(BaseModel):
    conversation_id: str
    mode: str
    provider: str
    model: str
    response: str
    context: dict
    created_at: datetime


class AIMessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    provider: str | None
    model: str | None
    metadata: dict
    created_at: datetime


class AIConversationListItem(BaseModel):
    id: str
    portfolio_id: str
    title: str | None
    mode: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIConversationDetail(BaseModel):
    id: str
    portfolio_id: str
    title: str | None
    mode: str | None
    context: dict
    messages: list[AIMessageResponse]
    created_at: datetime
    updated_at: datetime
