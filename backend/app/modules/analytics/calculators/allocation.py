from collections import defaultdict

from app.modules.analytics.schemas import AllocationAnalytics, AllocationBucket, HoldingAnalytics


def calculate_allocation(holdings: list[HoldingAnalytics]) -> AllocationAnalytics:
    return AllocationAnalytics(
        asset_allocation=_bucket_holdings(holdings, key="asset_class", fallback="Unclassified"),
        sector_allocation=_bucket_holdings(holdings, key="sector", fallback="Unclassified"),
        currency_exposure=_bucket_holdings(holdings, key="currency", fallback="Unclassified"),
    )


def _bucket_holdings(holdings: list[HoldingAnalytics], *, key: str, fallback: str) -> list[AllocationBucket]:
    buckets: dict[str, dict[str, object]] = defaultdict(lambda: {"value": 0.0, "symbols": []})
    total_value = sum(holding.market_value or 0 for holding in holdings)

    for holding in holdings:
        market_value = holding.market_value
        if market_value is None:
            continue
        raw_name = getattr(holding, key)
        name = str(raw_name).strip() if raw_name is not None else ""
        bucket_name = name or fallback
        buckets[bucket_name]["value"] = float(buckets[bucket_name]["value"]) + market_value
        symbols = buckets[bucket_name]["symbols"]
        if isinstance(symbols, list):
            symbols.append(holding.symbol)

    return sorted(
        [
            AllocationBucket(
                name=name,
                value=round(float(data["value"]), 6),
                weight=round(float(data["value"]) / total_value, 6) if total_value > 0 else 0,
                symbols=sorted(set(data["symbols"] if isinstance(data["symbols"], list) else [])),
            )
            for name, data in buckets.items()
        ],
        key=lambda bucket: (-bucket.value, bucket.name),
    )
