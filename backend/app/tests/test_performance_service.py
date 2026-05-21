from collections.abc import Generator
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.models import User
from app.modules.common.data_status import DataStatus
from app.modules.holdings.schemas import HoldingCreate
from app.modules.holdings.service import HoldingService
from app.modules.market_data.history_schemas import (
    HistoricalPricePoint,
    HistoricalPriceResponse,
    HistoricalPriceSeries,
)
from app.modules.market_data.history_service import MarketHistoryService
from app.modules.performance.service import PerformanceService
from app.modules.portfolios.schemas import PortfolioCreate
from app.modules.portfolios.service import PortfolioService


@pytest.fixture()
def db(tmp_path) -> Generator[Session, None, None]:
    engine = create_engine(
        f"sqlite:///{tmp_path}/p_insight_performance_service_test.db",
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

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def user(db: Session) -> User:
    user = User(email="performance@example.com", display_name="Performance User")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


class FakeHistoryService:
    def __init__(self, prices: dict[str, list[tuple[date, float]]]):
        self.prices = prices
        self.contract = MarketHistoryService()

    def validate_period(self, period: str):
        return self.contract.validate_period(period)

    def resolve_start_date(self, *, period, end_date: date) -> date:
        return self.contract.resolve_start_date(period=period, end_date=end_date)

    def build_mock_response(
        self,
        *,
        symbols: list[str],
        period: str,
        end_date: date | None = None,
    ) -> HistoricalPriceResponse:
        normalized_period = self.validate_period(period)
        resolved_end = end_date or date(2026, 5, 21)
        start_date = self.resolve_start_date(period=normalized_period, end_date=resolved_end)
        data_status = DataStatus.mock_source(provider="fake_history", as_of=datetime(2026, 5, 21, tzinfo=UTC))
        series = [
            HistoricalPriceSeries(
                symbol=symbol,
                period=normalized_period,
                start_date=start_date,
                end_date=resolved_end,
                prices=[
                    HistoricalPricePoint(
                        date=price_date,
                        close=close,
                        data_status=data_status,
                    )
                    for price_date, close in self.prices.get(symbol, [])
                ],
                data_status=data_status,
            )
            for symbol in symbols
        ]
        return HistoricalPriceResponse(
            period=normalized_period,
            start_date=start_date,
            end_date=resolved_end,
            generated_at=datetime(2026, 5, 21, tzinfo=UTC),
            series=series,
            data_status=data_status,
        )


def create_portfolio(db: Session, user: User, *, benchmark_symbol: str | None = None) -> str:
    portfolio = PortfolioService(db).create_portfolio(
        user=user,
        data=PortfolioCreate(name="Performance Portfolio", base_currency="INR", benchmark_symbol=benchmark_symbol),
    )
    db.refresh(portfolio)
    return portfolio.id


def create_holding(
    db: Session,
    user: User,
    portfolio_id: str,
    *,
    symbol: str,
    quantity: float,
) -> None:
    HoldingService(db).create_holding(
        portfolio_id=portfolio_id,
        user=user,
        data=HoldingCreate(
            symbol=symbol,
            quantity=quantity,
            average_cost=100,
            current_price=100,
            currency="INR",
        ),
    )


def test_empty_portfolio_returns_empty_synthetic_history(db: Session, user: User) -> None:
    portfolio_id = create_portfolio(db, user)

    response = PerformanceService(db, history_service=FakeHistoryService({})).get_history(
        portfolio_id=portfolio_id,
        user=user,
        period="1M",
        end_date=date(2026, 5, 21),
    )

    assert response.portfolio_id == portfolio_id
    assert response.benchmark_symbol == "NIFTY50"
    assert response.portfolio_value_series == []
    assert response.portfolio_normalized_return_series == []
    assert response.benchmark_normalized_return_series == []
    assert response.missing_price_symbols == []
    assert response.data_status.source == "unavailable"


def test_missing_prices_return_metadata_without_partial_portfolio_series(db: Session, user: User) -> None:
    portfolio_id = create_portfolio(db, user)
    create_holding(db, user, portfolio_id, symbol="RELIANCE", quantity=10)
    create_holding(db, user, portfolio_id, symbol="TCS", quantity=5)
    history_service = FakeHistoryService(
        {
            "RELIANCE": [(date(2026, 5, 20), 100), (date(2026, 5, 21), 110)],
            "NIFTY50": [(date(2026, 5, 20), 1000), (date(2026, 5, 21), 1010)],
        }
    )

    response = PerformanceService(db, history_service=history_service).get_history(
        portfolio_id=portfolio_id,
        user=user,
        period="1M",
        end_date=date(2026, 5, 21),
    )

    assert response.portfolio_value_series == []
    assert response.portfolio_normalized_return_series == []
    assert response.benchmark_normalized_return_series[-1].normalized_return == pytest.approx(0.01)
    assert response.missing_price_symbols == ["TCS"]
    assert "TCS" in (response.data_status.warning or "")


def test_synthetic_series_shape_uses_current_quantities_and_benchmark(db: Session, user: User) -> None:
    portfolio_id = create_portfolio(db, user)
    create_holding(db, user, portfolio_id, symbol="RELIANCE", quantity=10)
    create_holding(db, user, portfolio_id, symbol="TCS", quantity=5)
    history_service = FakeHistoryService(
        {
            "RELIANCE": [(date(2026, 5, 20), 100), (date(2026, 5, 21), 110)],
            "TCS": [(date(2026, 5, 20), 200), (date(2026, 5, 21), 220)],
            "NIFTY50": [(date(2026, 5, 20), 1000), (date(2026, 5, 21), 1050)],
        }
    )

    response = PerformanceService(db, history_service=history_service).get_history(
        portfolio_id=portfolio_id,
        user=user,
        period="1M",
        end_date=date(2026, 5, 21),
    )

    assert [point.date for point in response.portfolio_value_series] == [
        date(2026, 5, 20),
        date(2026, 5, 21),
    ]
    assert [point.value for point in response.portfolio_value_series] == [2000, 2200]
    assert [point.normalized_return for point in response.portfolio_normalized_return_series] == [0, 0.1]
    assert [point.normalized_return for point in response.benchmark_normalized_return_series] == [0, 0.05]
    assert response.missing_price_symbols == []
    assert response.data_status.provider == "fake_history"


def test_assumption_metadata_is_explicitly_not_xirr_or_twr(db: Session, user: User) -> None:
    portfolio_id = create_portfolio(db, user)
    create_holding(db, user, portfolio_id, symbol="RELIANCE", quantity=10)
    history_service = FakeHistoryService(
        {
            "RELIANCE": [(date(2026, 5, 20), 100), (date(2026, 5, 21), 110)],
            "NIFTY50": [(date(2026, 5, 20), 1000), (date(2026, 5, 21), 1050)],
        }
    )

    response = PerformanceService(db, history_service=history_service).get_history(
        portfolio_id=portfolio_id,
        user=user,
        period="1M",
        end_date=date(2026, 5, 21),
    )

    assert response.assumptions.method == "synthetic_current_holdings"
    assert response.assumptions.assumes_current_quantities_held_throughout is True
    assert response.assumptions.not_transaction_aware is True
    assert response.assumptions.not_xirr is True
    assert response.assumptions.not_time_weighted_return is True
