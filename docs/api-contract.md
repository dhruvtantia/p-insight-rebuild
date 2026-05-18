# API Contract

Implemented endpoints currently use the `/api` prefix. The `/api/v1` prefix remains reserved for future versioned product APIs.

Phase 2 uses a development auth placeholder that creates or returns a deterministic demo user. This will later be replaced by Supabase Auth or Clerk.

## Health

- `GET /api/health`

Purpose: service status and deployment checks.

Response:

```json
{
  "status": "ok",
  "service": "p-insight-backend"
}
```

## Portfolios

- `GET /api/portfolios`
- `POST /api/portfolios`
- `GET /api/portfolios/{portfolio_id}`
- `PATCH /api/portfolios/{portfolio_id}`
- `DELETE /api/portfolios/{portfolio_id}`

Purpose: portfolio lifecycle.

Create request:

```json
{
  "name": "Core Portfolio",
  "base_currency": "USD",
  "benchmark_symbol": "VOO",
  "risk_free_rate": 0.04
}
```

Response:

```json
{
  "id": "portfolio-id",
  "user_id": "demo-user-id",
  "name": "Core Portfolio",
  "base_currency": "USD",
  "benchmark_symbol": "VOO",
  "risk_free_rate": 0.04,
  "created_at": "2026-05-18T00:00:00Z",
  "updated_at": "2026-05-18T00:00:00Z"
}
```

## Holdings

- `GET /api/portfolios/{portfolio_id}/holdings`
- `POST /api/portfolios/{portfolio_id}/holdings`
- `PATCH /api/portfolios/{portfolio_id}/holdings/{holding_id}`
- `DELETE /api/portfolios/{portfolio_id}/holdings/{holding_id}`

Purpose: validated portfolio holdings.

Create request:

```json
{
  "symbol": "AAPL",
  "company_name": "Apple Inc.",
  "quantity": 10,
  "average_cost": 100,
  "current_price": 125,
  "currency": "USD",
  "sector": "Technology",
  "asset_class": "equity",
  "exchange": "NASDAQ"
}
```

Response:

```json
{
  "id": "holding-id",
  "portfolio_id": "portfolio-id",
  "symbol": "AAPL",
  "company_name": "Apple Inc.",
  "quantity": 10,
  "average_cost": 100,
  "current_price": 125,
  "market_value": 1250,
  "unrealized_gain_loss": 250,
  "currency": "USD",
  "sector": "Technology",
  "asset_class": "equity",
  "exchange": "NASDAQ",
  "created_at": "2026-05-18T00:00:00Z",
  "updated_at": "2026-05-18T00:00:00Z"
}
```

Validation:
- `quantity` must be positive.
- `symbol` must not be empty.
- `average_cost` cannot be negative.
- `current_price` cannot be negative.

Derived fields:
- `market_value = quantity * current_price` when `current_price` exists.
- `unrealized_gain_loss = quantity * (current_price - average_cost)` when both price fields exist.

## Uploads

- `POST /api/v1/uploads/holdings/validate`
- `GET /api/v1/uploads/{upload_id}`
- `POST /api/v1/uploads/{upload_id}/apply`

Purpose: validate uploaded rows before writing holdings.

## Market Data

- `GET /api/v1/market-data/quotes`
- `GET /api/v1/market-data/providers`

Purpose: backend-mediated market data access.

## Analytics

- `GET /api/v1/portfolios/{portfolio_id}/analytics`
- `GET /api/v1/portfolios/{portfolio_id}/insights`

Purpose: backend-owned analytics and rule-based insights.

## AI Advisor

- `POST /api/v1/portfolios/{portfolio_id}/advisor/questions`
- `GET /api/v1/portfolios/{portfolio_id}/advisor/context`

Purpose: AI explanations generated only from structured backend portfolio context.

## Watchlist

- `GET /api/v1/watchlist`
- `POST /api/v1/watchlist`
- `DELETE /api/v1/watchlist/{symbol}`

Purpose: symbols the user wants to monitor outside current holdings.

## Broker Placeholder

- `GET /api/v1/brokers/providers`
- `POST /api/v1/brokers/{provider}/connect`
- `POST /api/v1/brokers/{provider}/sync`

Purpose: future broker connection flow. No real broker integration in MVP.

## Billing Placeholder

- `GET /api/v1/billing/plans`
- `GET /api/v1/billing/usage`
- `POST /api/v1/billing/checkout`

Purpose: future freemium and Stripe-backed billing flow. No live billing in MVP.
