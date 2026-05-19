from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.models import AIConversation, AIMessage
from app.db.session import get_db
from app.main import create_app
from app.modules.ai_advisor.context_builder import AIAdvisorContextBuilder
from app.core.auth import get_development_user


@pytest.fixture()
def client(tmp_path) -> Generator[TestClient, None, None]:
    engine = create_engine(
        f"sqlite:///{tmp_path}/p_insight_ai_advisor_test.db",
        connect_args={"check_same_thread": False},
        future=True,
    )
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    app.state.testing_session_local = TestingSessionLocal

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def create_portfolio(client: TestClient, name: str = "AI Portfolio") -> dict:
    response = client.post(
        "/api/portfolios",
        json={"name": name, "base_currency": "USD", "benchmark_symbol": "SPY"},
    )
    assert response.status_code == 201
    return response.json()


def create_holding(
    client: TestClient,
    portfolio_id: str,
    *,
    symbol: str,
    quantity: float,
    average_cost: float | None,
    current_price: float | None,
    sector: str = "Technology",
    asset_class: str = "Equity",
) -> dict:
    response = client.post(
        f"/api/portfolios/{portfolio_id}/holdings",
        json={
            "symbol": symbol,
            "company_name": f"{symbol} Company",
            "quantity": quantity,
            "average_cost": average_cost,
            "current_price": current_price,
            "currency": "USD",
            "sector": sector,
            "asset_class": asset_class,
        },
    )
    assert response.status_code == 201
    return response.json()


def seed_portfolio(client: TestClient) -> dict:
    portfolio = create_portfolio(client)
    create_holding(
        client,
        portfolio["id"],
        symbol="AAPL",
        quantity=10,
        average_cost=100,
        current_price=200,
    )
    create_holding(
        client,
        portfolio["id"],
        symbol="VOO",
        quantity=5,
        average_cost=300,
        current_price=400,
        sector="ETF",
        asset_class="Fund",
    )
    return portfolio


def test_context_builder_returns_expected_fields(client: TestClient) -> None:
    portfolio = seed_portfolio(client)
    SessionLocal = client.app.state.testing_session_local

    with SessionLocal() as db:
        user = get_development_user(db)
        context = AIAdvisorContextBuilder(db).build_context(
            portfolio_id=portfolio["id"],
            user=user,
            user_question="How diversified is this?",
        )

    assert set(context.keys()) == {
        "portfolio_summary",
        "holdings",
        "risk_metrics",
        "allocation",
        "rule_based_insights",
        "price_freshness",
        "user_question",
    }
    assert context["portfolio_summary"]["name"] == "AI Portfolio"
    assert context["portfolio_summary"]["total_portfolio_value"] == 4000
    assert [holding["symbol"] for holding in context["holdings"]] == ["AAPL", "VOO"]
    assert context["user_question"] == "How diversified is this?"


def test_mock_summary_includes_actual_portfolio_info(client: TestClient) -> None:
    portfolio = seed_portfolio(client)

    response = client.post(f"/api/portfolios/{portfolio['id']}/ai/summary", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "summary"
    assert body["provider"] == "mock"
    assert "AI Portfolio" in body["response"]
    assert "4000.00 USD" in body["response"]
    assert "AAPL" in body["response"]
    assert "buy this" not in body["response"].lower()
    assert "sell this" not in body["response"].lower()


def test_mock_question_response_works(client: TestClient) -> None:
    portfolio = seed_portfolio(client)

    response = client.post(
        f"/api/portfolios/{portfolio['id']}/ai/question",
        json={"question": "What concentration risk should I review?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "question"
    assert "What concentration risk should I review?" in body["response"]
    assert "Based on the provided data" in body["response"]
    assert body["context"]["user_question"] == "What concentration risk should I review?"


def test_conversation_is_saved(client: TestClient) -> None:
    portfolio = seed_portfolio(client)

    response = client.post(
        f"/api/portfolios/{portfolio['id']}/ai/question",
        json={"question": "What data is missing?"},
    )

    assert response.status_code == 200
    conversation_id = response.json()["conversation_id"]

    list_response = client.get(f"/api/portfolios/{portfolio['id']}/ai/conversations")
    detail_response = client.get(f"/api/ai/conversations/{conversation_id}")

    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == conversation_id
    assert detail_response.status_code == 200
    roles = [message["role"] for message in detail_response.json()["messages"]]
    assert roles == ["system", "user", "assistant"]

    SessionLocal = client.app.state.testing_session_local
    with SessionLocal() as db:
        assert db.scalar(select(AIConversation).where(AIConversation.id == conversation_id)) is not None
        messages = db.scalars(select(AIMessage).where(AIMessage.conversation_id == conversation_id)).all()
        assert len(messages) == 3


def test_conversation_detail_handles_invalid_persisted_json(client: TestClient) -> None:
    portfolio = seed_portfolio(client)
    response = client.post(
        f"/api/portfolios/{portfolio['id']}/ai/question",
        json={"question": "What data is missing?"},
    )
    assert response.status_code == 200
    conversation_id = response.json()["conversation_id"]

    SessionLocal = client.app.state.testing_session_local
    with SessionLocal() as db:
        conversation = db.get(AIConversation, conversation_id)
        assert conversation is not None
        conversation.context_json = "{not-json"
        messages = db.scalars(select(AIMessage).where(AIMessage.conversation_id == conversation_id)).all()
        assert messages
        messages[0].metadata_json = "{not-json"
        db.commit()

    detail_response = client.get(f"/api/ai/conversations/{conversation_id}")

    assert detail_response.status_code == 200
    body = detail_response.json()
    assert body["context"] == {}
    assert body["mode"] is None
    assert body["messages"][0]["metadata"] == {}


def test_empty_portfolio_handled_safely(client: TestClient) -> None:
    portfolio = create_portfolio(client, name="Empty AI Portfolio")

    response = client.post(f"/api/portfolios/{portfolio['id']}/ai/summary", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["context"]["portfolio_summary"]["holdings_count"] == 0
    assert body["context"]["holdings"] == []
    assert "no holdings yet" in body["response"].lower()
