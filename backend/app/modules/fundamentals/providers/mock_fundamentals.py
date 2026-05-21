from datetime import UTC, datetime

from app.modules.common.data_status import DataStatus
from app.modules.fundamentals.providers.base import FundamentalsProvider
from app.modules.fundamentals.schemas import (
    FUNDAMENTAL_METRIC_NAMES,
    FundamentalMetrics,
    FundamentalsCoverage,
    FundamentalsResponse,
)
from app.modules.market_data.symbols import normalize_market_symbol


MOCK_FUNDAMENTALS_AS_OF = datetime(2026, 1, 1, tzinfo=UTC)


class MockFundamentalsProvider(FundamentalsProvider):
    source = "mock_fundamentals"

    _known_fundamentals: dict[str, dict[str, object]] = {
        "RELIANCE": {
            "company_name": "Reliance Industries Ltd.",
            "currency": "INR",
            "metrics": {
                "pe_ratio": 27.4,
                "forward_pe": 22.8,
                "price_to_book": 2.35,
                "ev_to_ebitda": 13.2,
                "peg": 1.48,
                "roe": 0.087,
                "roa": 0.041,
                "operating_margin": 0.158,
                "net_margin": 0.079,
                "revenue_growth": 0.061,
                "eps_growth": 0.094,
                "dividend_yield": 0.0035,
                "debt_to_equity": 0.42,
                "market_cap": 19_400_000_000_000,
            },
        },
        "TCS": {
            "company_name": "Tata Consultancy Services Ltd.",
            "currency": "INR",
            "metrics": {
                "pe_ratio": 31.8,
                "forward_pe": 27.6,
                "price_to_book": 14.1,
                "ev_to_ebitda": 22.4,
                "peg": 2.05,
                "roe": 0.455,
                "roa": 0.284,
                "operating_margin": 0.262,
                "net_margin": 0.193,
                "revenue_growth": 0.049,
                "eps_growth": 0.072,
                "dividend_yield": 0.012,
                "debt_to_equity": 0.08,
                "market_cap": 14_200_000_000_000,
            },
        },
        "INFY": {
            "company_name": "Infosys Ltd.",
            "currency": "INR",
            "metrics": {
                "pe_ratio": 24.7,
                "forward_pe": 21.3,
                "price_to_book": 7.6,
                "ev_to_ebitda": 16.9,
                "peg": 1.72,
                "roe": 0.311,
                "roa": 0.205,
                "operating_margin": 0.238,
                "net_margin": 0.169,
                "revenue_growth": 0.057,
                "eps_growth": 0.063,
                "dividend_yield": 0.021,
                "debt_to_equity": 0.06,
                "market_cap": 6_300_000_000_000,
            },
        },
    }

    def get_fundamentals(self, symbol: str) -> FundamentalsResponse:
        normalized_symbol = self._normalize_symbol(symbol)
        row = self._known_fundamentals.get(normalized_symbol)
        if row is None:
            metrics = FundamentalMetrics()
            return FundamentalsResponse(
                symbol=normalized_symbol,
                company_name=None,
                currency="INR",
                metrics=metrics,
                coverage=self._coverage(metrics),
                as_of=MOCK_FUNDAMENTALS_AS_OF,
                source=self.source,
                data_status=self._data_status(
                    warning=(
                        "Mock fundamentals are unavailable for this symbol. "
                        "No live fundamentals provider has been connected."
                    )
                ),
            )

        metrics = FundamentalMetrics(**row["metrics"])  # type: ignore[arg-type]
        return FundamentalsResponse(
            symbol=normalized_symbol,
            company_name=row["company_name"] if isinstance(row["company_name"], str) else None,
            currency=row["currency"] if isinstance(row["currency"], str) else "INR",
            metrics=metrics,
            coverage=self._coverage(metrics),
            as_of=MOCK_FUNDAMENTALS_AS_OF,
            source=self.source,
            data_status=self._data_status(),
        )

    def _normalize_symbol(self, symbol: str) -> str:
        return normalize_market_symbol(symbol).normalized_symbol

    def _coverage(self, metrics: FundamentalMetrics) -> FundamentalsCoverage:
        payload = metrics.model_dump()
        available = [name for name in FUNDAMENTAL_METRIC_NAMES if payload.get(name) is not None]
        missing = [name for name in FUNDAMENTAL_METRIC_NAMES if payload.get(name) is None]
        return FundamentalsCoverage(
            provider=self.source,
            available_metrics=available,
            missing_metrics=missing,
            coverage_ratio=round(len(available) / len(FUNDAMENTAL_METRIC_NAMES), 6),
            is_complete=len(missing) == 0,
        )

    def _data_status(self, *, warning: str | None = None) -> DataStatus:
        return DataStatus.mock_source(
            provider=self.source,
            as_of=MOCK_FUNDAMENTALS_AS_OF,
            is_realtime=False,
            warning=warning or "Fundamentals are deterministic mock data for local development and tests only.",
        )
