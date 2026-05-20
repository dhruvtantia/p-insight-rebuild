from dataclasses import dataclass


INDIA_EQUITY_PROVIDER_SYMBOLS = {
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "INFY": "INFY.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "ICICIBANK": "ICICIBANK.NS",
    "SBIN": "SBIN.NS",
    "ITC": "ITC.NS",
    "LT": "LT.NS",
    "BHARTIARTL": "BHARTIARTL.NS",
    "KOTAKBANK": "KOTAKBANK.NS",
    "AXISBANK": "AXISBANK.NS",
    "MARUTI": "MARUTI.NS",
    "SUNPHARMA": "SUNPHARMA.NS",
    "NIFTYBEES": "NIFTYBEES.NS",
}
INDIA_INDEX_PROVIDER_SYMBOLS = {
    "NIFTY50": "^NSEI",
    "NIFTY 50": "^NSEI",
    "NIFTY": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "BANK NIFTY": "^NSEBANK",
}
INDIA_PROVIDER_TO_NORMALIZED_SYMBOL = {
    **{provider_symbol: symbol for symbol, provider_symbol in INDIA_EQUITY_PROVIDER_SYMBOLS.items()},
    "^NSEI": "NIFTY50",
    "^NSEBANK": "BANKNIFTY",
}
BSE_CODE_PROVIDER_SYMBOLS = {
    "500325": "BSE:500325",
}


@dataclass(frozen=True)
class NormalizedSymbol:
    raw_symbol: str
    normalized_symbol: str
    exchange: str
    provider_symbol: str
    currency: str
    market: str
    asset_class: str


def normalize_market_symbol(symbol: str, *, default_exchange: str = "NSE") -> NormalizedSymbol:
    raw_symbol = symbol.strip()
    cleaned = raw_symbol.upper()
    if not cleaned:
        raise ValueError("Symbol cannot be empty")

    requested_exchange: str | None = None
    if ":" in cleaned:
        prefix, value = cleaned.split(":", 1)
        if prefix in {"NSE", "BSE"} and value.strip():
            requested_exchange = prefix
            cleaned = value.strip()

    exchange = requested_exchange or _exchange_for_symbol(cleaned, default_exchange=default_exchange)
    normalized_symbol = _normalized_india_symbol(cleaned)
    provider_symbol = _provider_symbol(normalized_symbol=normalized_symbol, exchange=exchange)

    return NormalizedSymbol(
        raw_symbol=raw_symbol,
        normalized_symbol=normalized_symbol,
        exchange=exchange,
        provider_symbol=provider_symbol,
        currency="INR",
        market="IN",
        asset_class=_asset_class_for_symbol(normalized_symbol),
    )


def normalize_india_symbol_for_provider(symbol: str) -> str:
    return normalize_market_symbol(symbol).provider_symbol


def normalize_benchmark_symbol(symbol: str | None) -> str | None:
    if symbol is None:
        return None
    cleaned = symbol.strip()
    if not cleaned:
        return None
    return normalize_market_symbol(cleaned).normalized_symbol


def _normalized_india_symbol(symbol: str) -> str:
    if symbol in INDIA_PROVIDER_TO_NORMALIZED_SYMBOL:
        return INDIA_PROVIDER_TO_NORMALIZED_SYMBOL[symbol]
    if symbol in INDIA_INDEX_PROVIDER_SYMBOLS:
        return symbol.replace(" ", "")
    if symbol.endswith(".NS") or symbol.endswith(".BO"):
        return symbol.rsplit(".", 1)[0]
    return symbol.replace(" ", "")


def _provider_symbol(*, normalized_symbol: str, exchange: str) -> str:
    if normalized_symbol in INDIA_INDEX_PROVIDER_SYMBOLS:
        return INDIA_INDEX_PROVIDER_SYMBOLS[normalized_symbol]
    if normalized_symbol in INDIA_EQUITY_PROVIDER_SYMBOLS and exchange == "NSE":
        return INDIA_EQUITY_PROVIDER_SYMBOLS[normalized_symbol]
    if normalized_symbol in BSE_CODE_PROVIDER_SYMBOLS:
        return BSE_CODE_PROVIDER_SYMBOLS[normalized_symbol]
    if exchange == "BSE":
        return f"BSE:{normalized_symbol}"
    return f"{normalized_symbol}.NS"


def _exchange_for_symbol(symbol: str, *, default_exchange: str) -> str:
    if symbol.endswith(".BO") or symbol.isdigit():
        return "BSE"
    if symbol.endswith(".NS") or symbol in INDIA_INDEX_PROVIDER_SYMBOLS:
        return "NSE"
    normalized_exchange = default_exchange.strip().upper()
    return normalized_exchange if normalized_exchange in {"NSE", "BSE"} else "NSE"


def _asset_class_for_symbol(symbol: str) -> str:
    if symbol in {"NIFTY50", "BANKNIFTY"}:
        return "Index"
    if symbol.endswith("BEES"):
        return "ETF"
    return "Equity"
