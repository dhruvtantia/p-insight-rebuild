# Snapshot Model Review

Date: 2026-05-21

## Decision

Use the existing `PortfolioSnapshot` model and `portfolio_snapshots` table for the first snapshot service. Do not create a second snapshot model or table. No migration is needed for a minimal service that stores a full holdings snapshot and analytics summary inside `snapshot_json`.

## Existing Model Fields

`backend/app/db/models.py` defines:

```python
class PortfolioSnapshot(TimestampMixin, Base):
    __tablename__ = "portfolio_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"), index=True, nullable=False)
    total_value: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    cash_value: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    holdings_value: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    snapshot_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
```

Inherited timestamp fields:

- `created_at`
- `updated_at`

Relationship:

- `portfolio: Mapped[Portfolio] = relationship(back_populates="snapshots")`
- `Portfolio.snapshots` already points back to `PortfolioSnapshot`.

## Migration Status

`portfolio_snapshots` is created in `backend/alembic/versions/0001_initial_models.py` with the same core columns:

- `id`
- `portfolio_id`
- `total_value`
- `cash_value`
- `holdings_value`
- `snapshot_json`
- `as_of`
- `created_at`
- `updated_at`

The migration also creates `ix_portfolio_snapshots_portfolio_id`.

Later migrations are unrelated:

- `0002_upload_column_mapping.py` only changes `upload_jobs`.
- `0003_holding_sector_source.py` only changes `holdings`.

Decision: no migration is needed for a minimal snapshot service using current columns.

## Can It Store Holdings Snapshot JSON?

Yes. `snapshot_json` is a non-null `Text` field, so it can store a serialized JSON payload containing the holdings state at `as_of`.

Recommended holdings payload shape:

```json
{
  "schema_version": 1,
  "snapshot_type": "portfolio_state",
  "holdings": [
    {
      "holding_id": "uuid",
      "symbol": "RELIANCE",
      "company_name": "Reliance Industries",
      "quantity": 10,
      "average_cost": 2500,
      "current_price": 2842.15,
      "currency": "INR",
      "sector": "Energy",
      "asset_class": "Equity",
      "exchange": "NSE"
    }
  ]
}
```

## Can It Store Analytics Summary JSON?

Yes. The same `snapshot_json` payload can include a compact analytics summary, while scalar totals remain duplicated in first-class columns for easy list views and ordering.

Recommended analytics payload section:

```json
{
  "analytics_summary": {
    "total_portfolio_value": 28421.5,
    "total_cost_basis": 25000,
    "total_unrealized_gain_loss": 3421.5,
    "total_unrealized_gain_loss_pct": 0.13686,
    "largest_holding": {
      "symbol": "RELIANCE",
      "market_value": 28421.5,
      "weight": 1
    }
  }
}
```

This does not replace `AnalyticsResult`. `AnalyticsResult` stores recalculated analytics outputs by result type. `PortfolioSnapshot` should store point-in-time portfolio state plus the summary needed to reconstruct a historical snapshot.

## Recommended Minimal Snapshot Service Schema

For the first service, use the existing table as follows:

- `portfolio_id`: portfolio being captured; ownership should be enforced through `PortfolioService.get_portfolio`.
- `as_of`: effective snapshot timestamp. Default to `utc_now()` unless caller/service supplies a specific timestamp.
- `total_value`: current total portfolio value at capture time.
- `holdings_value`: current holdings value at capture time.
- `cash_value`: set to `0` for now if cash is not modeled, or `None` if unknown.
- `snapshot_json`: serialized JSON object with:
  - `schema_version`
  - `snapshot_type`
  - `source`, for example `manual`, `scheduled`, `upload_confirm`, or `price_refresh`
  - `portfolio`, including `id`, `name`, `base_currency`, `benchmark_symbol`
  - `holdings`, including all fields needed to reconstruct the holding rows at capture time
  - `analytics_summary`, limited to summary-level metrics
  - `data_status`, if prices are involved
  - `generated_at`

Minimal service operations can be internal-only at first:

- `create_snapshot(portfolio_id, user, source, as_of=None)`
- `list_snapshots(portfolio_id, user)`
- `get_snapshot(snapshot_id, user)`

Do not add public snapshot APIs until the product contract is explicit.

## Risks of Duplicate Model/Table Creation

Creating another snapshot model or table would be risky because:

- `PortfolioSnapshot` is already registered in SQLAlchemy metadata under `portfolio_snapshots`.
- Alembic already creates `portfolio_snapshots` in the initial migration.
- A second ORM class with the same `__tablename__` can create SQLAlchemy metadata conflicts.
- A second Alembic migration trying to create the same table would fail on deployed databases where `0001_initial_models` has already run.
- A parallel table such as `snapshots` or `portfolio_snapshot_records` would split snapshot semantics and make ownership, retention, and list views harder to reason about.
- Existing docs already mention `Portfolio.snapshots` and `PortfolioSnapshot` as the future historical snapshot entity.

Recommendation: extend usage through service/schema code only. Add a migration later only if a real query requirement appears, such as indexing `as_of`, adding a `snapshot_type` column, or moving from `Text` to PostgreSQL `JSONB`.

## Future Migration Candidates

Not required now, but reasonable later:

- Add an index on `(portfolio_id, as_of)` for historical timeline queries.
- Add `snapshot_type` as a small string column if multiple snapshot categories need filtering.
- Add `source` as a small string column if list views need source filtering.
- Use PostgreSQL `JSONB` for `snapshot_json` only if server-side JSON querying becomes necessary.

Until those requirements exist, the current model is sufficient.
