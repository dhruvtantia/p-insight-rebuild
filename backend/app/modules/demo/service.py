from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Asset, AssetPrice, Holding, Portfolio, User
from app.modules.demo.schemas import DemoSeedResponse
from app.modules.market_data.providers.mock_provider import MockProvider, MockProviderIndia

DEMO_PORTFOLIO_NAME = "Demo Growth Portfolio"
INDIA_DEMO_PORTFOLIO_NAME = "Demo India Portfolio"

DEMO_HOLDINGS = [
    {
        "symbol": "AAPL",
        "company_name": "Apple Inc.",
        "quantity": 12,
        "average_cost": 145.0,
        "currency": "USD",
        "sector": "Technology",
        "asset_class": "Equity",
        "exchange": "NASDAQ",
    },
    {
        "symbol": "MSFT",
        "company_name": "Microsoft Corporation",
        "quantity": 8,
        "average_cost": 310.0,
        "currency": "USD",
        "sector": "Technology",
        "asset_class": "Equity",
        "exchange": "NASDAQ",
    },
    {
        "symbol": "NVDA",
        "company_name": "NVIDIA Corporation",
        "quantity": 18,
        "average_cost": 88.0,
        "currency": "USD",
        "sector": "Technology",
        "asset_class": "Equity",
        "exchange": "NASDAQ",
    },
    {
        "symbol": "SPY",
        "company_name": "SPDR S&P 500 ETF Trust",
        "quantity": 10,
        "average_cost": 430.0,
        "currency": "USD",
        "sector": "ETF",
        "asset_class": "Fund",
        "exchange": "NYSEARCA",
    },
    {
        "symbol": "TSLA",
        "company_name": "Tesla Inc.",
        "quantity": 6,
        "average_cost": 210.0,
        "currency": "USD",
        "sector": "Consumer Discretionary",
        "asset_class": "Equity",
        "exchange": "NASDAQ",
    },
]

INDIA_DEMO_HOLDINGS = [
    {
        "symbol": "RELIANCE",
        "company_name": "Reliance Industries Ltd.",
        "quantity": 8,
        "average_cost": 2420.0,
        "currency": "INR",
        "sector": "Energy",
        "asset_class": "Equity",
        "exchange": "NSE",
    },
    {
        "symbol": "TCS",
        "company_name": "Tata Consultancy Services Ltd.",
        "quantity": 4,
        "average_cost": 3480.0,
        "currency": "INR",
        "sector": "Information Technology",
        "asset_class": "Equity",
        "exchange": "NSE",
    },
    {
        "symbol": "INFY",
        "company_name": "Infosys Ltd.",
        "quantity": 7,
        "average_cost": 1395.0,
        "currency": "INR",
        "sector": "Information Technology",
        "asset_class": "Equity",
        "exchange": "NSE",
    },
    {
        "symbol": "HDFCBANK",
        "company_name": "HDFC Bank Ltd.",
        "quantity": 10,
        "average_cost": 1510.0,
        "currency": "INR",
        "sector": "Financial Services",
        "asset_class": "Equity",
        "exchange": "NSE",
    },
    {
        "symbol": "ICICIBANK",
        "company_name": "ICICI Bank Ltd.",
        "quantity": 12,
        "average_cost": 960.0,
        "currency": "INR",
        "sector": "Financial Services",
        "asset_class": "Equity",
        "exchange": "NSE",
    },
    {
        "symbol": "SBIN",
        "company_name": "State Bank of India",
        "quantity": 15,
        "average_cost": 610.0,
        "currency": "INR",
        "sector": "Financial Services",
        "asset_class": "Equity",
        "exchange": "NSE",
    },
    {
        "symbol": "ITC",
        "company_name": "ITC Ltd.",
        "quantity": 20,
        "average_cost": 390.0,
        "currency": "INR",
        "sector": "Consumer Staples",
        "asset_class": "Equity",
        "exchange": "NSE",
    },
    {
        "symbol": "LT",
        "company_name": "Larsen & Toubro Ltd.",
        "quantity": 3,
        "average_cost": 3020.0,
        "currency": "INR",
        "sector": "Industrials",
        "asset_class": "Equity",
        "exchange": "NSE",
    },
    {
        "symbol": "BHARTIARTL",
        "company_name": "Bharti Airtel Ltd.",
        "quantity": 9,
        "average_cost": 1040.0,
        "currency": "INR",
        "sector": "Communication Services",
        "asset_class": "Equity",
        "exchange": "NSE",
    },
]


class DemoSeedService:
    def __init__(self, db: Session):
        self.db = db
        self.provider_name = get_settings().market_data_provider.strip().lower()
        self.provider = MockProviderIndia() if self.provider_name == "mock_india" else MockProvider()

    def seed_for_user(self, *, user: User) -> DemoSeedResponse:
        portfolio = self._get_or_create_portfolio(user=user)
        demo_holdings = self._demo_holdings()
        symbols: list[str] = []
        for row in demo_holdings:
            quote = self.provider.get_latest_price(row["symbol"])
            holding = self._get_or_create_holding(portfolio=portfolio, row=row)
            holding.current_price = quote.price
            self.db.add(holding)
            asset = self._get_or_create_asset(symbol=quote.symbol, row=row)
            self.db.add(
                AssetPrice(
                    asset_id=asset.id,
                    symbol=quote.symbol,
                    price=quote.price,
                    currency=quote.currency,
                    source=quote.source,
                    as_of=quote.as_of,
                    is_realtime=quote.is_realtime,
                )
            )
            symbols.append(quote.symbol)

        self.db.commit()
        self.db.refresh(portfolio)
        holdings_count = self.db.scalar(
            select(func.count()).select_from(Holding).where(Holding.portfolio_id == portfolio.id)
        )
        return DemoSeedResponse(
            portfolio_id=portfolio.id,
            portfolio_name=portfolio.name,
            holdings_count=holdings_count or len(demo_holdings),
            symbols=symbols,
            message="Demo portfolio seeded with mock prices.",
        )

    def _get_or_create_portfolio(self, *, user: User) -> Portfolio:
        portfolio_name = INDIA_DEMO_PORTFOLIO_NAME if self.provider_name == "mock_india" else DEMO_PORTFOLIO_NAME
        portfolio = self.db.scalar(
            select(Portfolio).where(Portfolio.user_id == user.id, Portfolio.name == portfolio_name)
        )
        if portfolio is not None:
            return portfolio

        portfolio = Portfolio(
            user_id=user.id,
            name=portfolio_name,
            base_currency="INR" if self.provider_name == "mock_india" else "USD",
            benchmark_symbol="NIFTY50" if self.provider_name == "mock_india" else "SPY",
            risk_free_rate=0.065 if self.provider_name == "mock_india" else 0.04,
        )
        self.db.add(portfolio)
        self.db.flush()
        return portfolio

    def _demo_holdings(self) -> list[dict]:
        return INDIA_DEMO_HOLDINGS if self.provider_name == "mock_india" else DEMO_HOLDINGS

    def _get_or_create_holding(self, *, portfolio: Portfolio, row: dict) -> Holding:
        holding = self.db.scalar(
            select(Holding).where(Holding.portfolio_id == portfolio.id, Holding.symbol == row["symbol"])
        )
        if holding is None:
            holding = Holding(portfolio_id=portfolio.id, **row)
        else:
            for key, value in row.items():
                setattr(holding, key, value)
        return holding

    def _get_or_create_asset(self, *, symbol: str, row: dict) -> Asset:
        asset = self.db.scalar(select(Asset).where(Asset.symbol == symbol))
        if asset is None:
            asset = Asset(symbol=symbol)
            self.db.add(asset)
            self.db.flush()
        asset.company_name = row["company_name"]
        asset.currency = row["currency"]
        asset.sector = row["sector"]
        asset.asset_class = row["asset_class"]
        asset.exchange = row["exchange"]
        return asset
