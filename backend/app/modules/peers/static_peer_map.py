INDIA_STATIC_PEER_MAP: dict[str, list[str]] = {
    "RELIANCE": ["TCS", "INFY"],
    "TCS": ["INFY"],
    "INFY": ["TCS"],
    "HDFCBANK": ["ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK"],
    "ICICIBANK": ["HDFCBANK", "SBIN", "AXISBANK", "KOTAKBANK"],
    "SBIN": ["HDFCBANK"],
    "ITC": ["HINDUNILVR"],
    "SUNPHARMA": ["DRREDDY"],
}
