import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import NotFoundError
from app.core.json import safe_json_dict
from app.db.models import AIConversation, AIMessage, User
from app.modules.ai_advisor.context_builder import AIAdvisorContextBuilder
from app.modules.ai_advisor.prompts import build_prompt
from app.modules.ai_advisor.repository import AIAdvisorRepository
from app.modules.ai_advisor.schemas import (
    AIAdvisorResponse,
    AIConversationDetail,
    AIConversationListItem,
    AIMessageResponse,
)
from app.modules.portfolios.service import PortfolioService

BANNED_PHRASES = ("buy this", "sell this", "guaranteed return", "this will outperform")


class ConversationNotFoundError(NotFoundError):
    def __init__(self) -> None:
        super().__init__("AI conversation not found")


class AIAdvisorService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = AIAdvisorRepository(db)
        self.context_builder = AIAdvisorContextBuilder(db)
        self.portfolio_service = PortfolioService(db)

    def create_summary(self, *, portfolio_id: str, user: User) -> AIAdvisorResponse:
        self._check_usage_limit(user=user, mode="summary")
        context = self.context_builder.build_context(portfolio_id=portfolio_id, user=user)
        provider, model = self._provider_metadata()
        response_text = self._safe_response(self._mock_summary_response(context))
        conversation = self._persist_exchange(
            portfolio_id=portfolio_id,
            mode="summary",
            context=context,
            user_content="Summarize this portfolio.",
            assistant_content=response_text,
            provider=provider,
            model=model,
        )
        self.db.commit()
        self.db.refresh(conversation)
        return AIAdvisorResponse(
            conversation_id=conversation.id,
            mode="summary",
            provider=provider,
            model=model,
            response=response_text,
            context=context,
            created_at=conversation.created_at,
        )

    def answer_question(self, *, portfolio_id: str, user: User, question: str) -> AIAdvisorResponse:
        self._check_usage_limit(user=user, mode="question")
        context = self.context_builder.build_context(portfolio_id=portfolio_id, user=user, user_question=question)
        provider, model = self._provider_metadata()
        response_text = self._safe_response(self._mock_question_response(context))
        conversation = self._persist_exchange(
            portfolio_id=portfolio_id,
            mode="question",
            context=context,
            user_content=question,
            assistant_content=response_text,
            provider=provider,
            model=model,
        )
        self.db.commit()
        self.db.refresh(conversation)
        return AIAdvisorResponse(
            conversation_id=conversation.id,
            mode="question",
            provider=provider,
            model=model,
            response=response_text,
            context=context,
            created_at=conversation.created_at,
        )

    def list_conversations(self, *, portfolio_id: str, user: User) -> list[AIConversationListItem]:
        portfolio = self.portfolio_service.get_portfolio(portfolio_id=portfolio_id, user=user)
        conversations = self.repository.list_conversations_for_portfolio(portfolio_id=portfolio.id)
        return [
            AIConversationListItem(
                id=conversation.id,
                portfolio_id=conversation.portfolio_id,
                title=conversation.title,
                mode=self._conversation_context(conversation).get("mode"),
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
            )
            for conversation in conversations
        ]

    def get_conversation(self, *, conversation_id: str, user: User) -> AIConversationDetail:
        conversation = self.repository.get_conversation_for_user(conversation_id=conversation_id, user=user)
        if conversation is None:
            raise ConversationNotFoundError()
        messages = self.repository.list_messages(conversation_id=conversation.id)
        context_payload = self._conversation_context(conversation)
        return AIConversationDetail(
            id=conversation.id,
            portfolio_id=conversation.portfolio_id,
            title=conversation.title,
            mode=context_payload.get("mode"),
            context=context_payload.get("context", {}),
            messages=[self._message_response(message) for message in messages],
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )

    def _persist_exchange(
        self,
        *,
        portfolio_id: str,
        mode: str,
        context: dict,
        user_content: str,
        assistant_content: str,
        provider: str,
        model: str,
    ) -> AIConversation:
        prompt = build_prompt(mode=mode, context=context)
        title = self._conversation_title(mode=mode, context=context, user_content=user_content)
        conversation = self.repository.create_conversation(
            portfolio_id=portfolio_id,
            title=title,
            mode=mode,
            context=context,
        )
        self.repository.add_message(
            conversation_id=conversation.id,
            role="system",
            content=prompt,
            provider=provider,
            model=model,
            metadata={"mode": mode, "generated_at": datetime.now(timezone.utc).isoformat()},
        )
        self.repository.add_message(
            conversation_id=conversation.id,
            role="user",
            content=user_content,
            metadata={"mode": mode},
        )
        self.repository.add_message(
            conversation_id=conversation.id,
            role="assistant",
            content=assistant_content,
            provider=provider,
            model=model,
            metadata={"mode": mode, "mock": provider == "mock"},
        )
        return conversation

    def _mock_summary_response(self, context: dict) -> str:
        summary = context["portfolio_summary"]
        insights = context["rule_based_insights"]
        missing_prices = context["price_freshness"]["missing_price_symbols"]
        total_value = summary["total_portfolio_value"]
        largest = summary["largest_holding"]
        name = summary["name"]

        if summary["holdings_count"] == 0:
            return (
                f"Based on the provided data, {name} has no holdings yet. "
                "This suggests the first review step is adding or uploading holdings so allocation and risk can be evaluated."
            )

        largest_text = (
            f"The largest holding is {largest['symbol']} at {largest['weight'] * 100:.0f}% of portfolio value."
            if largest
            else "No largest holding can be identified because price data is incomplete."
        )
        insight_text = (
            f"One risk to review is {insights[0]['title'].lower()}: {insights[0]['message']}"
            if insights
            else "No rule-based warnings are currently active."
        )
        missing_text = (
            f" Missing current prices for {', '.join(missing_prices)} limit the analysis."
            if missing_prices
            else ""
        )
        return (
            f"Based on the provided data, {name} has total value of {total_value:.2f} "
            f"{summary['base_currency']} across {summary['holdings_count']} holding(s). "
            f"{largest_text} {insight_text}{missing_text} "
            "You may want to compare concentration, sector allocation, and missing data before making decisions."
        )

    def _mock_question_response(self, context: dict) -> str:
        question = context["user_question"]
        summary = context["portfolio_summary"]
        insights = context["rule_based_insights"]
        largest = summary["largest_holding"]

        if summary["holdings_count"] == 0:
            return (
                f"Based on the provided data, there are no holdings to evaluate for: {question}. "
                "You may want to compare holdings after importing portfolio data."
            )

        largest_text = (
            f"{largest['symbol']} is the largest holding at {largest['weight'] * 100:.0f}%."
            if largest
            else "Largest holding is unavailable because current prices are missing."
        )
        insight_text = (
            f"One risk to review is {insights[0]['message']}"
            if insights
            else "This suggests no rule-based warnings are active right now."
        )
        return (
            f"Based on the provided data, regarding '{question}', {largest_text} "
            f"{insight_text} You may want to compare this with your target allocation and cost basis data."
        )

    def _provider_metadata(self) -> tuple[str, str]:
        settings = get_settings()
        if settings.openai_api_key:
            return "mock", "openai-ready-mock"
        if settings.anthropic_api_key:
            return "mock", "anthropic-ready-mock"
        return "mock", "deterministic-advisor-v1"

    def _check_usage_limit(self, *, user: User, mode: str) -> bool:
        return True

    def _safe_response(self, response: str) -> str:
        safe_response = response
        replacements = {
            "buy this": "review this",
            "sell this": "review this",
            "guaranteed return": "expected return assumption",
            "this will outperform": "this may differ from the benchmark",
        }
        for banned_phrase, replacement in replacements.items():
            safe_response = safe_response.replace(banned_phrase, replacement)
            safe_response = safe_response.replace(banned_phrase.title(), replacement)
        return safe_response

    def _conversation_title(self, *, mode: str, context: dict, user_content: str) -> str:
        portfolio_name = context["portfolio_summary"]["name"]
        if mode == "summary":
            return f"Summary for {portfolio_name}"
        return user_content[:80]

    def _conversation_context(self, conversation: AIConversation) -> dict:
        return safe_json_dict(conversation.context_json)

    def _message_response(self, message: AIMessage) -> AIMessageResponse:
        return AIMessageResponse(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            provider=message.provider,
            model=message.model,
            metadata=safe_json_dict(message.metadata_json),
            created_at=message.created_at,
        )
