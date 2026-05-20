import pytest

from app.modules.market_data.symbols import normalize_benchmark_symbol, normalize_market_symbol


@pytest.mark.parametrize(
    ("raw_symbol", "normalized_symbol", "exchange", "provider_symbol", "asset_class"),
    [
        ("reliance", "RELIANCE", "NSE", "RELIANCE.NS", "Equity"),
        ("RELIANCE.NS", "RELIANCE", "NSE", "RELIANCE.NS", "Equity"),
        ("NSE:RELIANCE", "RELIANCE", "NSE", "RELIANCE.NS", "Equity"),
        ("BSE:500325", "500325", "BSE", "BSE:500325", "Equity"),
        ("NIFTY 50", "NIFTY50", "NSE", "^NSEI", "Index"),
        ("NIFTY50", "NIFTY50", "NSE", "^NSEI", "Index"),
        ("BANKNIFTY", "BANKNIFTY", "NSE", "^NSEBANK", "Index"),
        ("NIFTYBEES", "NIFTYBEES", "NSE", "NIFTYBEES.NS", "ETF"),
    ],
)
def test_normalize_indian_symbols(
    raw_symbol: str,
    normalized_symbol: str,
    exchange: str,
    provider_symbol: str,
    asset_class: str,
) -> None:
    result = normalize_market_symbol(raw_symbol)

    assert result.raw_symbol == raw_symbol.strip()
    assert result.normalized_symbol == normalized_symbol
    assert result.exchange == exchange
    assert result.provider_symbol == provider_symbol
    assert result.currency == "INR"
    assert result.market == "IN"
    assert result.asset_class == asset_class


def test_normalize_benchmark_symbol_accepts_nifty_style_names() -> None:
    assert normalize_benchmark_symbol("NIFTY 50") == "NIFTY50"
    assert normalize_benchmark_symbol("NIFTY50") == "NIFTY50"
    assert normalize_benchmark_symbol("BANK NIFTY") == "BANKNIFTY"
