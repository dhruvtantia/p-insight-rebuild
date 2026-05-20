from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.modules.common.data_status import DataStatus
from app.modules.dashboard import (
    DashboardActionItem,
    DashboardAllocationItem,
    DashboardBundleResponse,
    DashboardDataQuality,
    DashboardKpis,
    DashboardRiskSummary,
    DashboardTopHolding,
)


def test_dashboard_bundle_response_supports_backend_native_contract() -> None:
    as_of = datetime(2026, 5, 21, 10, 30, tzinfo=UTC)
    data_status = DataStatus.mock_source(provider="mock_india", as_of=as_of)

    response = DashboardBundleResponse(
        portfolio_id="portfolio-1",
        generated_at=as_of,
        kpis=DashboardKpis(
            portfolio_id="portfolio-1",
            base_currency="inr",
            total_portfolio_value=250000,
            total_cost_basis=210000,
            total_unrealized_gain_loss=40000,
            total_unrealized_gain_loss_pct=0.1904,
            daily_change=None,
            daily_change_pct=None,
            holdings_count=3,
            priced_holdings_count=2,
            largest_holding_symbol=" reliance ",
            largest_holding_weight=0.52,
            cash_weight=None,
        ),
        allocations=[
            DashboardAllocationItem(
                dimension="asset_class",
                name="Equity",
                value=250000,
                weight=1,
                symbols=[" reliance ", "tcs"],
            ),
            DashboardAllocationItem(
                dimension="sector",
                name="Information Technology",
                value=120000,
                weight=0.48,
                symbols=["tcs"],
            ),
        ],
        top_holdings=[
            DashboardTopHolding(
                holding_id="holding-1",
                symbol=" reliance ",
                company_name="Reliance Industries Ltd.",
                market_value=130000,
                weight=0.52,
                unrealized_gain_loss=25000,
                unrealized_gain_loss_pct=0.238,
                currency="inr",
            )
        ],
        risk=DashboardRiskSummary(
            concentration_status="moderate",
            largest_holding_symbol="reliance",
            largest_holding_weight=0.52,
            top_5_weight=1,
            volatility=None,
            volatility_status="insufficient_history",
            sharpe_ratio=None,
            sharpe_ratio_status="insufficient_history",
            max_drawdown=None,
            max_drawdown_status="insufficient_history",
            message="Historical risk metrics need more data.",
        ),
        data_quality=DashboardDataQuality(
            holdings_count=3,
            priced_holdings_count=2,
            missing_price_count=1,
            missing_cost_basis_count=1,
            stale_price_count=0,
            warnings=["One holding is missing current price data."],
            data_status=data_status,
        ),
        action_items=[
            DashboardActionItem(
                id="missing-price-data",
                priority="high",
                category="data_quality",
                title="Missing price data",
                message="Refresh or add current prices before reviewing allocation.",
                affected_symbols=[" infy ", "tcs"],
                recommended_action="refresh_prices",
            )
        ],
        data_status=data_status,
    )

    payload = response.model_dump(mode="json")

    assert payload["kpis"]["base_currency"] == "INR"
    assert payload["kpis"]["largest_holding_symbol"] == "RELIANCE"
    assert payload["allocations"][0]["symbols"] == ["RELIANCE", "TCS"]
    assert payload["top_holdings"][0]["symbol"] == "RELIANCE"
    assert payload["top_holdings"][0]["currency"] == "INR"
    assert payload["action_items"][0]["affected_symbols"] == ["INFY", "TCS"]
    assert payload["data_status"]["provider"] == "mock_india"
    assert payload["data_quality"]["data_status"]["is_mock"] is True


def test_dashboard_allocation_items_are_chart_library_independent() -> None:
    item = DashboardAllocationItem(
        dimension="currency",
        name="INR",
        value=100,
        weight=1,
        symbols=["RELIANCE"],
    )

    assert set(item.model_dump()) == {"dimension", "name", "value", "weight", "symbols"}


def test_dashboard_schema_rejects_invalid_statuses_and_weights() -> None:
    with pytest.raises(ValidationError):
        DashboardRiskSummary(
            concentration_status="critical",
            largest_holding_symbol="RELIANCE",
            largest_holding_weight=1.2,
            top_5_weight=1.1,
            volatility=None,
            volatility_status="missing",
            sharpe_ratio=None,
            sharpe_ratio_status="insufficient_history",
            max_drawdown=None,
            max_drawdown_status="insufficient_history",
            message="Invalid risk state.",
        )


def test_dashboard_action_item_rejects_unknown_recommended_action() -> None:
    with pytest.raises(ValidationError):
        DashboardActionItem(
            id="open-custom-url",
            priority="medium",
            category="data_quality",
            title="Open a custom URL",
            message="Frontend routes are not part of this backend contract.",
            recommended_action="open_dashboard_url",
        )
