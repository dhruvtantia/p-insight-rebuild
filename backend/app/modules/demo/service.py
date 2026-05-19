from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Asset, AssetPrice, Holding, Portfolio, User
from app.modules.demo.schemas import DemoSeedResponse
from app.modules.market_data.providers.mock_provider import MockProvider

DEMO_PORTFOLIO_NAME = "Demo Growth Portfolio"

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


class DemoSeedService:
    def __init__(self, db: Session):
        self.db = db
        self.provider = MockProvider()

    def seed_for_user(self, *, user: User) -> DemoSeedResponse:
        portfolio = self._get_or_create_portfolio(user=user)
        symbols: list[str] = []
        for row in DEMO_HOLDINGS:
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
            holdings_count=holdings_count or len(DEMO_HOLDINGS),
            symbols=symbols,
            message="Demo portfolio seeded with mock prices.",
        )

    def _get_or_create_portfolio(self, *, user: User) -> Portfolio:
        portfolio = self.db.scalar(
            select(Portfolio).where(Portfolio.user_id == user.id, Portfolio.name == DEMO_PORTFOLIO_NAME)
        )
        if portfolio is not None:
            return portfolio

        portfolio = Portfolio(
            user_id=user.id,
            name=DEMO_PORTFOLIO_NAME,
            base_currency="USD",
            benchmark_symbol="SPY",
            risk_free_rate=0.04,
        )
        self.db.add(portfolio)
        self.db.flush()
        return portfolio

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
