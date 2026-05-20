from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.models import User
from app.modules.dashboard.service import DashboardService
from app.modules.holdings.schemas import HoldingCreate
from app.modules.holdings.service import HoldingService
from app.modules.market_data.providers.mock_provider import MockProviderIndia
from app.modules.market_data.service import MarketDataService
from app.modules.portfolios.schemas import PortfolioCreate
from app.modules.portfolios.service import PortfolioService


@pytest.fixture()
def db(tmp_path) -> Generator[Session, None, None]:
    engine = create_engine(
        f"sqlite:///{tmp_path}/p_insight_dashboard_service_test.db",
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
    user = User(email="dashboard@example.com", display_name="Dashboard User")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_portfolio(db: Session, user: User) -> str:
    portfolio = PortfolioService(db).create_portfolio(
        user=user,
        data=PortfolioCreate(name="Dashboard Portfolio", base_currency="INR"),
    )
    db.commit()
    db.refresh(portfolio)
    return portfolio.id


def create_holding(
    db: Session,
    user: User,
    portfolio_id: str,
    *,
    symbol: str,
    quantity: float,
    average_cost: float | None,
    current_price: float | None = None,
    sector: str | None = "Information Technology",
    asset_class: str | None = "Equity",
) -> None:
    HoldingService(db).create_holding(
        portfolio_id=portfolio_id,
        user=user,
        data=HoldingCreate(
            symbol=symbol,
            quantity=quantity,
            average_cost=average_cost,
            current_price=current_price,
            currency="INR",
            sector=sector,
            asset_class=asset_class,
        ),
    )
    db.commit()


def dashboard_service(db: Session) -> DashboardService:
    market_data = MarketDataService(db, provider=MockProviderIndia())
    return DashboardService(db, market_data_service=market_data)


def test_empty_portfolio_returns_clean_empty_dashboard(db: Session, user: User) -> None:
    portfolio_id = create_portfolio(db, user)

    response = dashboard_service(db).get_bundle(portfolio_id=portfolio_id, user=user)

    assert response.portfolio_id == portfolio_id
    assert response.kpis.total_invested == 0
    assert response.kpis.current_value == 0
    assert response.kpis.unrealized_pnl == 0
    assert response.kpis.return_percent is None
    assert response.top_holdings == []
    assert response.sector_allocation == []
    assert response.asset_allocation == []
    assert response.risk.concentration_status == "empty"
    assert response.risk.largest_holding_weight is None
    assert response.risk.top_3_weight == 0
    assert response.risk.hhi == 0
    assert response.data_quality.missing_price_count == 0
    assert response.data_quality.missing_cost_basis_count == 0
    assert response.action_items == []
    assert response.data_status.source == "unavailable"


def test_portfolio_with_holdings_but_missing_prices_reports_data_quality(
    db: Session,
    user: User,
) -> None:
    portfolio_id = create_portfolio(db, user)
    create_holding(db, user, portfolio_id, symbol="RELIANCE", quantity=10, average_cost=2500)
    create_holding(db, user, portfolio_id, symbol="TCS", quantity=5, average_cost=None)

    response = dashboard_service(db).get_bundle(portfolio_id=portfolio_id, user=user)

    assert response.kpis.total_invested == 25000
    assert response.kpis.current_value == 0
    assert response.kpis.unrealized_pnl == 0
    assert response.kpis.return_percent == 0
    assert response.top_holdings == []
    assert response.data_quality.holdings_count == 2
    assert response.data_quality.priced_holdings_count == 0
    assert response.data_quality.missing_price_count == 2
    assert response.data_quality.missing_cost_basis_count == 1
    assert response.data_status.source == "unavailable"
    assert {item.id for item in response.action_items} >= {
        "missing_price_data",
        "missing_cost_basis",
    }


def test_portfolio_with_mock_prices_uses_mock_data_status(db: Session, user: User) -> None:
    portfolio_id = create_portfolio(db, user)
    create_holding(db, user, portfolio_id, symbol="RELIANCE", quantity=10, average_cost=2500)
    create_holding(db, user, portfolio_id, symbol="TCS", quantity=5, average_cost=3000)

    MarketDataService(db, provider=MockProviderIndia()).refresh_portfolio_prices(
        portfolio_id=portfolio_id,
        user=user,
    )

    response = dashboard_service(db).get_bundle(portfolio_id=portfolio_id, user=user)

    assert response.kpis.current_value == pytest.approx(48050.5)
    assert response.kpis.total_invested == 40000
    assert response.kpis.unrealized_pnl == pytest.approx(8050.5)
    assert response.kpis.return_percent == pytest.approx(0.201263)
    assert response.data_quality.missing_price_count == 0
    assert response.data_quality.missing_cost_basis_count == 0
    assert response.data_status.source == "mock"
    assert response.data_status.provider == "mock_india"
    assert response.data_status.is_mock is True
    assert [holding.symbol for holding in response.top_holdings] == ["RELIANCE", "TCS"]
    assert {bucket.name: bucket.value for bucket in response.sector_allocation} == {
        "Information Technology": pytest.approx(48050.5)
    }
    assert {bucket.name: bucket.value for bucket in response.asset_allocation} == {
        "Equity": pytest.approx(48050.5)
    }


def test_concentration_summary_includes_largest_top3_and_hhi(db: Session, user: User) -> None:
    portfolio_id = create_portfolio(db, user)
    create_holding(db, user, portfolio_id, symbol="RELIANCE", quantity=60, average_cost=1, current_price=1)
    create_holding(db, user, portfolio_id, symbol="TCS", quantity=30, average_cost=1, current_price=1)
    create_holding(db, user, portfolio_id, symbol="INFY", quantity=10, average_cost=1, current_price=1)

    response = dashboard_service(db).get_bundle(portfolio_id=portfolio_id, user=user)

    assert response.kpis.current_value == 100
    assert response.kpis.largest_holding_symbol == "RELIANCE"
    assert response.kpis.largest_holding_weight == pytest.approx(0.6)
    assert response.risk.concentration_status == "high"
    assert response.risk.largest_holding_weight == pytest.approx(0.6)
    assert response.risk.top_3_weight == pytest.approx(1.0)
    assert response.risk.hhi == pytest.approx(0.46)
