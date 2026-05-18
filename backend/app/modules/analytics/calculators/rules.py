from app.modules.analytics.schemas import AllocationAnalytics, HoldingAnalytics, RuleInsight


def evaluate_rules(
    *, holdings: list[HoldingAnalytics], allocation: AllocationAnalytics, base_currency: str
) -> list[RuleInsight]:
    rules: list[RuleInsight] = []
    priced_holdings = [holding for holding in holdings if holding.market_value is not None]

    if priced_holdings:
        largest = max(priced_holdings, key=lambda holding: holding.weight)
        if largest.weight > 0.25:
            rules.append(
                RuleInsight(
                    rule_id="HIGH_CONCENTRATION",
                    severity="high",
                    title="High concentration risk",
                    message=f"{largest.symbol} represents {_format_percent(largest.weight)} of your portfolio.",
                    affected_symbols=[largest.symbol],
                )
            )
        elif largest.weight > 0.15:
            rules.append(
                RuleInsight(
                    rule_id="MODERATE_CONCENTRATION",
                    severity="medium",
                    title="Moderate concentration risk",
                    message=f"{largest.symbol} represents {_format_percent(largest.weight)} of your portfolio.",
                    affected_symbols=[largest.symbol],
                )
            )

    missing_price_symbols = sorted(holding.symbol for holding in holdings if holding.current_price is None)
    if missing_price_symbols:
        rules.append(
            RuleInsight(
                rule_id="MISSING_PRICE_DATA",
                severity="medium",
                title="Missing price data",
                message=f"{len(missing_price_symbols)} holding(s) do not have current prices.",
                affected_symbols=missing_price_symbols,
            )
        )

    missing_cost_symbols = sorted(holding.symbol for holding in holdings if holding.average_cost is None)
    if missing_cost_symbols:
        rules.append(
            RuleInsight(
                rule_id="MISSING_COST_BASIS",
                severity="low",
                title="Missing cost basis",
                message=f"{len(missing_cost_symbols)} holding(s) do not have average cost data.",
                affected_symbols=missing_cost_symbols,
            )
        )

    if holdings:
        asset_classes = {(holding.asset_class or "Unclassified").strip() or "Unclassified" for holding in holdings}
        if len(asset_classes) == 1:
            asset_class = next(iter(asset_classes))
            rules.append(
                RuleInsight(
                    rule_id="SINGLE_ASSET_CLASS",
                    severity="medium",
                    title="Single asset class",
                    message=f"All holdings are classified as {asset_class}.",
                    affected_symbols=sorted(holding.symbol for holding in holdings),
                )
            )

    normalized_base = base_currency.upper()
    non_base_buckets = [bucket for bucket in allocation.currency_exposure if bucket.name.upper() != normalized_base]
    non_base_weight = round(sum(bucket.weight for bucket in non_base_buckets), 6)
    if non_base_weight > 0.20:
        affected_symbols = sorted({symbol for bucket in non_base_buckets for symbol in bucket.symbols})
        rules.append(
            RuleInsight(
                rule_id="CURRENCY_EXPOSURE",
                severity="medium",
                title="Currency exposure",
                message=f"Non-{normalized_base} holdings represent {_format_percent(non_base_weight)} of your portfolio.",
                affected_symbols=affected_symbols,
            )
        )

    return rules


def _format_percent(value: float) -> str:
    return f"{value * 100:.0f}%"
