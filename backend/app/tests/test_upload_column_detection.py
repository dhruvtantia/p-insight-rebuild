from pathlib import Path

from app.modules.uploads.column_detection import (
    ColumnMappingSuggestion,
    suggest_column_mappings,
    suggest_column_mappings_from_rows,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
DEMO_PORTFOLIO_CSV = REPO_ROOT / "docs" / "demo-data" / "pinsight_demo_india_portfolio_mock.csv"


def test_suggest_column_mappings_detects_supported_synonyms() -> None:
    suggestions = suggest_column_mappings(
        [
            "Ticker",
            "Shares",
            "Average Price",
            "Current Value",
            "Security Name",
            "Sector",
            "Asset Class",
            "Exchange",
            "Currency",
        ]
    )

    mapping = {suggestion.target_field: suggestion.source_column for suggestion in suggestions}

    assert mapping == {
        "symbol": "Ticker",
        "quantity": "Shares",
        "average_cost": "Average Price",
        "market_value": "Current Value",
        "company_name": "Security Name",
        "sector": "Sector",
        "asset_class": "Asset Class",
        "exchange": "Exchange",
        "currency": "Currency",
    }
    assert all(isinstance(suggestion, ColumnMappingSuggestion) for suggestion in suggestions)
    assert all(suggestion.confidence == 1 for suggestion in suggestions)
    assert all("Exact column match" in suggestion.reason for suggestion in suggestions)


def test_demo_india_portfolio_columns_match_supported_mapping_suggestions() -> None:
    header = DEMO_PORTFOLIO_CSV.read_text(encoding="utf-8-sig").splitlines()[0]
    columns = header.split(",")
    suggestions = suggest_column_mappings(columns)
    mapping = {suggestion.target_field: suggestion.source_column for suggestion in suggestions}

    assert columns == [
        "Ticker",
        "Name",
        "Shares",
        "Average Cost",
        "Current Price",
        "Market Value",
        "Currency",
        "Sector",
        "Asset Class",
        "Exchange",
    ]
    assert mapping == {
        "symbol": "Ticker",
        "quantity": "Shares",
        "average_cost": "Average Cost",
        "market_value": "Market Value",
        "company_name": "Name",
        "sector": "Sector",
        "asset_class": "Asset Class",
        "exchange": "Exchange",
        "currency": "Currency",
    }
    assert "Current Price" not in mapping.values()


def test_suggest_column_mappings_handles_spacing_case_and_punctuation() -> None:
    suggestions = suggest_column_mappings(
        [
            " stock_symbol ",
            "No. of Units",
            "Avg-Cost",
            "Market Value (INR)",
            "Company",
        ]
    )

    by_field = {suggestion.target_field: suggestion for suggestion in suggestions}

    assert by_field["symbol"].source_column == " stock_symbol "
    assert by_field["symbol"].confidence == 0.85
    assert by_field["quantity"].source_column == "No. of Units"
    assert by_field["average_cost"].source_column == "Avg-Cost"
    assert by_field["market_value"].source_column == "Market Value (INR)"
    assert by_field["company_name"].source_column == "Company"
    assert "contains synonym" in by_field["market_value"].reason


def test_suggest_column_mappings_is_deterministic_and_does_not_auto_apply() -> None:
    columns = ["Symbol", "Ticker", "Quantity", "Qty", "Random Notes"]

    first = suggest_column_mappings(columns)
    second = suggest_column_mappings(columns)

    assert first == second
    assert [suggestion.target_field for suggestion in first] == ["symbol", "quantity"]
    assert [suggestion.source_column for suggestion in first] == ["Ticker", "Qty"]


def test_suggest_column_mappings_from_rows_preserves_first_seen_columns() -> None:
    suggestions = suggest_column_mappings_from_rows(
        [
            {"Instrument": "RELIANCE", "Qty": 10},
            {"Instrument": "TCS", "Qty": 5, "Buy Price": 3000},
        ]
    )

    mapping = {suggestion.target_field: suggestion.source_column for suggestion in suggestions}

    assert mapping == {
        "symbol": "Instrument",
        "quantity": "Qty",
        "average_cost": "Buy Price",
    }


def test_suggest_column_mappings_ignores_unknown_columns() -> None:
    suggestions = suggest_column_mappings(["Notes", "Portfolio Strategy", "Uploaded At"])

    assert suggestions == []
