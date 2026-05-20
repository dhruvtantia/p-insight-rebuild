from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import ValidationAppError
from app.db.models import Asset, AssetPrice, Holding, User
from app.modules.market_data.providers.base import MarketDataProvider
from app.modules.market_data.providers.fmp_provider import FmpProvider
from app.modules.market_data.providers.india_placeholders import (
    AlphaVantageProvider,
    BrokerMarketDataProvider,
    MarketstackProvider,
    NseBseProvider,
    TwelveDataProvider,
)
from app.modules.market_data.providers.mock_provider import MockProvider, MockProviderIndia
from app.modules.market_data.providers.polygon_provider import PolygonProvider
from app.modules.market_data.schemas import (
    BatchPriceResponse,
    HoldingPriceRefreshItem,
    PortfolioPriceRefreshResponse,
    PriceHistoryResponse,
    PriceQuote,
)
from app.modules.market_data.symbols import normalize_market_symbol
from app.modules.portfolios.service import PortfolioService


class MarketDataService:
    def __init__(self, db: Session, provider: MarketDataProvider | None = None):
        self.db = db
        self.provider = provider or self._build_provider()
        self.portfolio_service = PortfolioService(db)

    def get_latest_price(self, symbol: str) -> PriceQuote:
        quote = self.provider.get_latest_price(self._normalize_symbol(symbol))
        self._cache_price(quote)
        self.db.commit()
        return quote

    def get_batch_prices(self, symbols: list[str]) -> BatchPriceResponse:
        normalized_symbols = self._normalize_symbols(symbols)
        quotes = self.provider.get_batch_prices(normalized_symbols)
        for quote in quotes:
            self._cache_price(quote)
        self.db.commit()
        return BatchPriceResponse(prices=quotes)

    def get_price_history(self, symbol: str, start: str | None = None, end: str | None = None) -> PriceHistoryResponse:
        normalized_symbol = self._normalize_symbol(symbol)
        start_date, end_date = self._resolve_history_window(start=start, end=end)
        prices = self.provider.get_price_history(
            normalized_symbol,
            start=start_date.isoformat(),
            end=end_date.isoformat(),
        )
        return PriceHistoryResponse(
            symbol=normalized_symbol,
            start=start_date.isoformat(),
            end=end_date.isoformat(),
            prices=prices,
        )

    def refresh_portfolio_prices(self, *, portfolio_id: str, user: User) -> PortfolioPriceRefreshResponse:
        portfolio = self.portfolio_service.get_portfolio(portfolio_id=portfolio_id, user=user)
        holdings = self.db.scalars(
            select(Holding).where(Holding.portfolio_id == portfolio.id).order_by(Holding.created_at.asc())
        ).all()
        symbols = self._normalize_symbols([holding.symbol for holding in holdings]) if holdings else []
        quotes = self.provider.get_batch_prices(symbols) if symbols else []
        quote_by_symbol = {quote.symbol: quote for quote in quotes}

        refreshed_holdings: list[HoldingPriceRefreshItem] = []
        for holding in holdings:
            quote = quote_by_symbol.get(self._normalize_symbol(holding.symbol))
            if quote is None:
                continue
            previous_price = float(holding.current_price) if holding.current_price is not None else None
            holding.current_price = quote.price
            self.db.add(holding)
            refreshed_holdings.append(
                HoldingPriceRefreshItem(
                    holding_id=holding.id,
                    symbol=holding.symbol,
                    previous_price=previous_price,
                    current_price=quote.price,
                    currency=quote.currency,
                    source=quote.source,
                    as_of=quote.as_of,
                    is_realtime=quote.is_realtime,
                    data_status=quote.data_status,
                )
            )

        for quote in quotes:
            self._cache_price(quote)

        self.db.commit()
        for holding in holdings:
            self.db.refresh(holding)

        return PortfolioPriceRefreshResponse(
            portfolio_id=portfolio.id,
            refreshed_count=len(refreshed_holdings),
            prices=quotes,
            holdings=refreshed_holdings,
        )

    def _build_provider(self) -> MarketDataProvider:
        settings = get_settings()
        provider_name = settings.resolved_market_data_provider
        if provider_name == "mock":
            self._ensure_mock_market_data_allowed(settings=settings)
            return MockProvider()
        if provider_name == "mock_india":
            self._ensure_mock_market_data_allowed(settings=settings)
            return MockProviderIndia()
        if provider_name in {"twelve_data", "twelvedata"}:
            return TwelveDataProvider(api_key=settings.twelve_data_api_key)
        if provider_name in {"alpha_vantage", "alphavantage"}:
            return AlphaVantageProvider(api_key=settings.alpha_vantage_api_key)
        if provider_name == "marketstack":
            return MarketstackProvider(api_key=settings.marketstack_api_key)
        if provider_name in {"nse_bse", "nse", "bse", "truedata", "true_data"}:
            return NseBseProvider(api_key=settings.market_data_api_key)
        if provider_name in {"broker", "broker_provider"}:
            return BrokerMarketDataProvider(api_key=settings.market_data_api_key)
        if provider_name in {"polygon", "massive"}:
            return PolygonProvider(api_key=settings.polygon_api_key or settings.market_data_api_key)
        if provider_name == "fmp":
            return FmpProvider(api_key=settings.fmp_api_key or settings.market_data_api_key)
        raise ValidationAppError(f"Unsupported market data provider: {settings.market_data_provider}")

    def _ensure_mock_market_data_allowed(self, *, settings) -> None:
        if settings.normalized_app_env == "production" and not settings.production_mock_market_data_allowed:
            raise ValidationAppError(
                "Mock market data is disabled in production. Set ALLOW_PRODUCTION_MOCK_MARKET_DATA=true only for explicit test/demo deployments."
            )

    def _cache_price(self, quote: PriceQuote) -> AssetPrice:
        asset = self._get_or_create_asset(symbol=quote.symbol, currency=quote.currency)
        asset_price = AssetPrice(
            asset_id=asset.id,
            symbol=quote.symbol,
            price=quote.price,
            currency=quote.currency,
            source=quote.source,
            as_of=quote.as_of,
            is_realtime=quote.is_realtime,
        )
        self.db.add(asset_price)
        return asset_price

    def _get_or_create_asset(self, *, symbol: str, currency: str) -> Asset:
        asset = self.db.scalar(select(Asset).where(Asset.symbol == symbol))
        if asset is not None:
            return asset

        asset = Asset(symbol=symbol, currency=currency)
        self.db.add(asset)
        self.db.flush()
        return asset

    def _normalize_symbols(self, symbols: list[str]) -> list[str]:
        deduped_symbols: list[str] = []
        seen: set[str] = set()
        for symbol in symbols:
            normalized_symbol = self._normalize_symbol(symbol)
            if normalized_symbol not in seen:
                seen.add(normalized_symbol)
                deduped_symbols.append(normalized_symbol)
        if not deduped_symbols:
            raise ValidationAppError("At least one symbol is required")
        return deduped_symbols

    def _normalize_symbol(self, symbol: str) -> str:
        try:
            return normalize_market_symbol(symbol).normalized_symbol
        except ValueError as exc:
            raise ValidationAppError("Symbol cannot be empty") from exc

    def _resolve_history_window(self, *, start: str | None, end: str | None) -> tuple[date, date]:
        try:
            end_date = date.fromisoformat(end) if end is not None else datetime.now(UTC).date()
            start_date = date.fromisoformat(start) if start is not None else end_date - timedelta(days=30)
        except ValueError as exc:
            raise ValidationAppError("History dates must use YYYY-MM-DD format") from exc
        if end_date < start_date:
            raise ValidationAppError("History end date must be on or after start date")
        return start_date, end_date
