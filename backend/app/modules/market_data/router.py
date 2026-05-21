from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.core.feature_flags import require_feature_enabled
from app.db.session import get_db
from app.modules.market_data.history_schemas import HistoricalPriceResponse
from app.modules.market_data.history_service import MarketHistoryService
from app.modules.market_data.schemas import BatchPriceResponse, PortfolioPriceRefreshResponse, PriceHistoryResponse, PriceQuote
from app.modules.market_data.service import MarketDataService

router = APIRouter(tags=["market-data"])


def get_market_data_service(db: Annotated[Session, Depends(get_db)]) -> MarketDataService:
    return MarketDataService(db)


def get_market_history_service() -> MarketHistoryService:
    return MarketHistoryService()


def require_historical_data_enabled() -> None:
    require_feature_enabled("ENABLE_HISTORICAL_DATA")


MarketDataServiceDep = Annotated[MarketDataService, Depends(get_market_data_service)]
MarketHistoryServiceDep = Annotated[MarketHistoryService, Depends(get_market_history_service)]


@router.get("/api/market-data/prices", response_model=BatchPriceResponse)
def get_batch_prices(
    symbols: Annotated[str, Query(min_length=1)],
    service: MarketDataServiceDep,
):
    return service.get_batch_prices(symbols=_split_symbols(symbols))


@router.get("/api/market-data/prices/{symbol}", response_model=PriceQuote)
def get_latest_price(symbol: str, service: MarketDataServiceDep):
    return service.get_latest_price(symbol=symbol)


@router.get("/api/market-data/history/{symbol}", response_model=PriceHistoryResponse)
def get_price_history(
    symbol: str,
    service: MarketDataServiceDep,
    start: Annotated[str | None, Query(pattern=r"^\d{4}-\d{2}-\d{2}$")] = None,
    end: Annotated[str | None, Query(pattern=r"^\d{4}-\d{2}-\d{2}$")] = None,
):
    return service.get_price_history(symbol=symbol, start=start, end=end)


@router.get("/api/market/history", response_model=HistoricalPriceResponse)
def get_market_history(
    symbols: Annotated[str, Query(min_length=1)],
    period: Annotated[str, Query(min_length=1)],
    _: Annotated[None, Depends(require_historical_data_enabled)],
    service: MarketHistoryServiceDep,
):
    return service.build_mock_response(symbols=_split_symbols(symbols), period=period)


@router.post("/api/portfolios/{portfolio_id}/prices/refresh", response_model=PortfolioPriceRefreshResponse)
def refresh_portfolio_prices(
    portfolio_id: str,
    user: CurrentUser,
    service: MarketDataServiceDep,
):
    return service.refresh_portfolio_prices(portfolio_id=portfolio_id, user=user)


def _split_symbols(symbols: str) -> list[str]:
    return [symbol.strip() for symbol in symbols.split(",") if symbol.strip()]
