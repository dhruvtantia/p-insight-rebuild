# Demo Portfolio Upload Notes

## File

- `docs/demo-data/pinsight_demo_india_portfolio_mock.csv`
- Broker-style mock Indian portfolio for manual QA only.
- Contains 14 INR holdings across NSE equities, index ETFs, and commodity ETFs.
- Does not contain real market data.

## Upload Mapping

Use the existing portfolio upload flow and map the CSV columns as follows:

| CSV column | P-insight field |
| --- | --- |
| Ticker | symbol |
| Name | company_name |
| Shares | quantity |
| Average Cost | average_cost |
| Market Value | market_value |
| Currency | currency |
| Sector | sector |
| Asset Class | asset_class |
| Exchange | exchange |

The CSV also includes `Current Price` for broker-style readability. The current upload backend does not support `current_price` as a direct upload mapping field. During validation, P-insight derives holding `current_price` from `Market Value / Shares` when both values are present. The demo CSV keeps `Market Value` consistent with `Shares * Current Price`, so the imported current prices match the CSV values without adding a new upload field.

## Mapping Suggestions Compatibility

The existing mapping suggestion logic recognizes these demo columns:

- `Ticker`
- `Name`
- `Shares`
- `Average Cost`
- `Market Value`
- `Currency`
- `Sector`
- `Asset Class`
- `Exchange`

`Current Price` is intentionally not suggested because it is not in the supported upload field set.

## Commodity ETF Rows

`GOLDBEES` and `SILVERBEES` use `Asset Class` value `Commodity ETF`. The upload path stores `asset_class` as free text, so these rows import without a special schema change.

## Verified Flow

Backend coverage verifies that the exact CSV file:

1. Uploads through `POST /api/portfolios/{portfolio_id}/uploads`.
2. Preserves all 10 source columns in detected columns.
3. Applies the existing supported column mapping.
4. Validates all 14 rows.
5. Confirms import for all 14 holdings.
6. Imports INR/NSE metadata and preserves `Commodity ETF` for `GOLDBEES` and `SILVERBEES`.

