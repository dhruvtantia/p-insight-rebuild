from sqlalchemy.orm import Session

from app.db.models import User
from app.modules.fundamentals.schemas import FUNDAMENTAL_METRIC_NAMES, FundamentalsResponse
from app.modules.fundamentals.service import FundamentalsService
from app.modules.market_data.symbols import normalize_market_symbol
from app.modules.peers.schemas import MetricComparisonRow, PeerComparisonResponse, PeerSetQuality
from app.modules.peers.static_peer_map import INDIA_STATIC_PEER_MAP
from app.modules.portfolios.service import PortfolioService


LOWER_IS_BETTER_METRICS = {
    "pe_ratio",
    "forward_pe",
    "price_to_book",
    "ev_to_ebitda",
    "peg",
    "debt_to_equity",
}


class PeerComparisonService:
    def __init__(
        self,
        db: Session,
        fundamentals_service: FundamentalsService | None = None,
    ):
        self.db = db
        self.portfolio_service = PortfolioService(db)
        self.fundamentals_service = fundamentals_service or FundamentalsService(db=db)

    def compare(self, *, portfolio_id: str, symbol: str, user: User) -> PeerComparisonResponse:
        portfolio = self.portfolio_service.get_portfolio(portfolio_id=portfolio_id, user=user)
        normalized_symbol = normalize_market_symbol(symbol).normalized_symbol
        peer_symbols = INDIA_STATIC_PEER_MAP.get(normalized_symbol, [])
        selected = self.fundamentals_service.get_fundamentals(symbol=normalized_symbol)
        peers = [
            self.fundamentals_service.get_fundamentals(symbol=peer_symbol)
            for peer_symbol in peer_symbols
        ]
        companies = [selected, *peers]
        comparison_rows = self._comparison_rows(selected=selected, peers=peers)
        return PeerComparisonResponse(
            portfolio_id=portfolio.id,
            symbol=normalized_symbol,
            selected_company=selected,
            peer_companies=peers,
            metric_comparison_table=comparison_rows,
            simple_ranks=self._simple_ranks(companies=companies),
            peer_set_quality=self._peer_set_quality(peers=peers),
            warnings=self._warnings(symbol=normalized_symbol, peers=peers, selected=selected),
        )

    def _comparison_rows(
        self,
        *,
        selected: FundamentalsResponse,
        peers: list[FundamentalsResponse],
    ) -> list[MetricComparisonRow]:
        rows: list[MetricComparisonRow] = []
        for metric_name in FUNDAMENTAL_METRIC_NAMES:
            peer_values = {
                peer.symbol: getattr(peer.metrics, metric_name)
                for peer in peers
            }
            available_peer_values = [value for value in peer_values.values() if value is not None]
            peer_average = (
                round(sum(available_peer_values) / len(available_peer_values), 6)
                if available_peer_values
                else None
            )
            selected_rank = self._rank_for_metric(
                companies=[selected, *peers],
                metric_name=metric_name,
                symbol=selected.symbol,
            )
            rows.append(
                MetricComparisonRow(
                    metric=metric_name,
                    direction=self._direction(metric_name),
                    selected_value=getattr(selected.metrics, metric_name),
                    peer_values=peer_values,
                    peer_average=peer_average,
                    selected_rank=selected_rank,
                )
            )
        return rows

    def _simple_ranks(self, *, companies: list[FundamentalsResponse]) -> dict[str, dict[str, int | None]]:
        return {
            company.symbol: {
                metric_name: self._rank_for_metric(
                    companies=companies,
                    metric_name=metric_name,
                    symbol=company.symbol,
                )
                for metric_name in FUNDAMENTAL_METRIC_NAMES
            }
            for company in companies
        }

    def _rank_for_metric(
        self,
        *,
        companies: list[FundamentalsResponse],
        metric_name: str,
        symbol: str,
    ) -> int | None:
        values = [
            (company.symbol, getattr(company.metrics, metric_name))
            for company in companies
            if getattr(company.metrics, metric_name) is not None
        ]
        if not values:
            return None
        reverse = self._direction(metric_name) == "higher_is_better"
        ranked = sorted(values, key=lambda item: item[1], reverse=reverse)
        for index, (ranked_symbol, _) in enumerate(ranked, start=1):
            if ranked_symbol == symbol:
                return index
        return None

    def _peer_set_quality(self, *, peers: list[FundamentalsResponse]) -> PeerSetQuality:
        covered_peers = [peer for peer in peers if peer.coverage.available_metrics]
        missing_peer_symbols = [peer.symbol for peer in peers if not peer.coverage.available_metrics]
        return PeerSetQuality(
            peer_count=len(peers),
            covered_peer_count=len(covered_peers),
            missing_peer_symbols=missing_peer_symbols,
            coverage_percent=round((len(covered_peers) / len(peers)) * 100, 6) if peers else 0,
            is_sparse=len(peers) < 2,
        )

    def _warnings(
        self,
        *,
        symbol: str,
        selected: FundamentalsResponse,
        peers: list[FundamentalsResponse],
    ) -> list[str]:
        warnings = ["Peer set is static India seed data and should be reviewed before investment use."]
        if selected.data_status.is_mock or any(peer.data_status.is_mock for peer in peers):
            warnings.append("Peer fundamentals include mock data.")
        if not peers:
            warnings.append(f"No static peer set is configured for {symbol}.")
        elif len(peers) < 2:
            warnings.append(f"Peer set for {symbol} is sparse; fewer than two peers are configured.")
        missing = [peer.symbol for peer in peers if not peer.coverage.available_metrics]
        if missing:
            warnings.append(f"Fundamentals coverage is missing for peer(s): {', '.join(missing)}.")
        if not selected.coverage.available_metrics:
            warnings.append(f"Fundamentals coverage is missing for selected symbol {symbol}.")
        return warnings

    def _direction(self, metric_name: str):
        return "lower_is_better" if metric_name in LOWER_IS_BETTER_METRICS else "higher_is_better"
