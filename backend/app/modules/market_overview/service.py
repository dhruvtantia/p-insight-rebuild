from dataclasses import dataclass
from datetime import UTC, datetime, time
from hashlib import sha256
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.errors import ExternalProviderError, ValidationAppError
from app.modules.common.data_status import DataStatus
from app.modules.market_data.schemas import CompanyProfile, PriceQuote
from app.modules.market_data.service import MarketDataService
from app.modules.market_overview.schemas import (
    MarketIndexCard,
    MarketMover,
    MarketOverviewResponse,
    MarketStatus,
    SectorIndexCard,
)

INDIA_TIMEZONE = ZoneInfo("Asia/Kolkata")
MARKET_OPEN_TIME = time(9, 15)
MARKET_CLOSE_TIME = time(15, 30)


@dataclass(frozen=True)
class IndexDefinition:
    symbol: str
    name: str
    exchange: str


@dataclass(frozen=True)
class SectorIndexDefinition:
    symbol: str
    name: str
    sector: str
    exchange: str


MAJOR_INDICES = (
    IndexDefinition(symbol="NIFTY50", name="NIFTY 50", exchange="NSE"),
    IndexDefinition(symbol="SENSEX", name="Sensex", exchange="BSE"),
    IndexDefinition(symbol="BANKNIFTY", name="Bank Nifty", exchange="NSE"),
)

SECTOR_INDICES = (
    SectorIndexDefinition(symbol="NIFTYIT", name="NIFTY IT", sector="Information Technology", exchange="NSE"),
    SectorIndexDefinition(symbol="NIFTYBANK", name="NIFTY Bank", sector="Financial Services", exchange="NSE"),
    SectorIndexDefinition(symbol="NIFTYAUTO", name="NIFTY Auto", sector="Consumer Discretionary", exchange="NSE"),
    SectorIndexDefinition(symbol="NIFTYPHARMA", name="NIFTY Pharma", sector="Healthcare", exchange="NSE"),
    SectorIndexDefinition(symbol="NIFTYFMCG", name="NIFTY FMCG", sector="Consumer Staples", exchange="NSE"),
)

# Demo mover candidates are only used when the configured provider is mock/mock_india.
DEMO_MOVER_SYMBOLS = (
    "RELIANCE",
    "TCS",
    "INFY",
    "HDFCBANK",
    "ICICIBANK",
    "SBIN",
    "ITC",
    "LT",
    "BHARTIARTL",
    "AXISBANK",
    "MARUTI",
    "SUNPHARMA",
)


class MarketOverviewService:
    def __init__(self, db: Session, market_data_service: MarketDataService | None = None):
        self.db = db
        self.market_data_service = market_data_service or MarketDataService(db)
        self.provider = self.market_data_service.provider

    def get_overview(self) -> MarketOverviewResponse:
        generated_at = datetime.now(UTC)
        major_indices = self._major_index_cards()
        sector_indices = self._sector_index_cards()
        top_gainers, top_losers = self._movers()
        data_status = self._overview_data_status(
            major_indices=major_indices,
            sector_indices=sector_indices,
            top_gainers=top_gainers,
            top_losers=top_losers,
        )

        return MarketOverviewResponse(
            market_status=self._market_status(as_of=generated_at, data_status=data_status),
            major_indices=major_indices,
            sector_indices=sector_indices,
            top_gainers=top_gainers,
            top_losers=top_losers,
            generated_at=generated_at,
            data_status=data_status,
        )

    def _major_index_cards(self) -> list[MarketIndexCard]:
        cards: list[MarketIndexCard] = []
        for definition in MAJOR_INDICES:
            quote = self._safe_latest_price(definition.symbol)
            if quote is None:
                continue
            cards.append(
                MarketIndexCard(
                    symbol=quote.symbol,
                    name=definition.name,
                    value=quote.price,
                    change=self._deterministic_change(symbol=quote.symbol, price=quote.price) if self._provider_is_mock() else None,
                    change_percent=self._deterministic_change_percent(quote.symbol) if self._provider_is_mock() else None,
                    currency=quote.currency,
                    exchange=definition.exchange,
                    as_of=quote.as_of,
                    data_status=self._quote_data_status(quote),
                )
            )
        return cards

    def _sector_index_cards(self) -> list[SectorIndexCard]:
        cards: list[SectorIndexCard] = []
        for definition in SECTOR_INDICES:
            quote = self._safe_latest_price(definition.symbol)
            if quote is None:
                continue
            cards.append(
                SectorIndexCard(
                    symbol=quote.symbol,
                    name=definition.name,
                    sector=definition.sector,
                    value=quote.price,
                    change=self._deterministic_change(symbol=quote.symbol, price=quote.price) if self._provider_is_mock() else None,
                    change_percent=self._deterministic_change_percent(quote.symbol) if self._provider_is_mock() else None,
                    exchange=definition.exchange,
                    as_of=quote.as_of,
                    data_status=self._quote_data_status(quote),
                )
            )
        return cards

    def _movers(self) -> tuple[list[MarketMover], list[MarketMover]]:
        if not self._provider_is_mock():
            return [], []

        movers: list[MarketMover] = []
        for symbol in DEMO_MOVER_SYMBOLS:
            quote = self._safe_latest_price(symbol)
            if quote is None:
                continue
            profile = self._safe_company_profile(symbol)
            change_percent = self._deterministic_change_percent(symbol)
            movers.append(
                MarketMover(
                    symbol=quote.symbol,
                    company_name=profile.company_name if profile and profile.company_name else quote.symbol,
                    last_price=quote.price,
                    change=round(quote.price * change_percent / 100, 2),
                    change_percent=change_percent,
                    currency=quote.currency,
                    exchange=profile.exchange if profile else "NSE",
                    sector=profile.sector if profile else None,
                    as_of=quote.as_of,
                    data_status=self._quote_data_status(quote),
                )
            )

        sorted_movers = sorted(movers, key=lambda mover: mover.change_percent, reverse=True)
        return sorted_movers[:5], sorted_movers[-5:][::-1]

    def _market_status(self, *, as_of: datetime, data_status: DataStatus) -> MarketStatus:
        local_now = as_of.astimezone(INDIA_TIMEZONE)
        is_weekday = local_now.weekday() < 5
        is_open = is_weekday and MARKET_OPEN_TIME <= local_now.time() <= MARKET_CLOSE_TIME
        return MarketStatus(
            market="India",
            exchange="NSE/BSE",
            state="open" if is_open else "closed",
            as_of=as_of,
            data_status=data_status,
        )

    def _overview_data_status(
        self,
        *,
        major_indices: list[MarketIndexCard],
        sector_indices: list[SectorIndexCard],
        top_gainers: list[MarketMover],
        top_losers: list[MarketMover],
    ) -> DataStatus:
        statuses = [
            item.data_status
            for item in [*major_indices, *sector_indices, *top_gainers, *top_losers]
            if item.data_status is not None
        ]
        if not statuses:
            return DataStatus.unavailable_source(provider=self._provider_name())
        if any(status.is_mock for status in statuses):
            as_of = max((status.as_of for status in statuses if status.as_of is not None), default=None)
            return DataStatus.mock_source(provider=self._provider_name(), as_of=as_of, is_realtime=False)
        if any(status.is_stale for status in statuses):
            as_of = max((status.as_of for status in statuses if status.as_of is not None), default=None)
            return DataStatus.stale_source(provider=self._provider_name(), as_of=as_of)
        as_of = max((status.as_of for status in statuses if status.as_of is not None), default=None)
        return DataStatus.live_source(provider=self._provider_name(), as_of=as_of)

    def _safe_latest_price(self, symbol: str) -> PriceQuote | None:
        try:
            return self.provider.get_latest_price(symbol)
        except (ExternalProviderError, ValidationAppError, ValueError):
            return None

    def _safe_company_profile(self, symbol: str) -> CompanyProfile | None:
        try:
            return self.provider.get_company_profile(symbol)
        except (ExternalProviderError, ValidationAppError, ValueError):
            return None

    def _quote_data_status(self, quote: PriceQuote) -> DataStatus:
        if quote.data_status is not None:
            return quote.data_status
        if quote.source in {"mock", "mock_india"}:
            return DataStatus.mock_source(provider=quote.source, as_of=quote.as_of, is_realtime=quote.is_realtime)
        return DataStatus.live_source(provider=quote.source, as_of=quote.as_of, is_realtime=quote.is_realtime)

    def _provider_is_mock(self) -> bool:
        return self._provider_name() in {"mock", "mock_india"}

    def _provider_name(self) -> str:
        return getattr(self.provider, "source", "unknown")

    def _deterministic_change_percent(self, symbol: str) -> float:
        digest = sha256(f"{self._provider_name()}:{symbol}".encode("utf-8")).hexdigest()
        basis_points = (int(digest[:8], 16) % 701) - 350
        if basis_points == 0:
            basis_points = 25
        return round(basis_points / 100, 2)

    def _deterministic_change(self, *, symbol: str, price: float) -> float:
        return round(price * self._deterministic_change_percent(symbol) / 100, 2)
