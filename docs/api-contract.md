# Initial API Contract

Phase 0 documents endpoint groups only. Concrete request and response schemas will be added when backend implementation begins.

## Health

- `GET /api/v1/health`
- `GET /api/health`

Purpose: service status and deployment checks.

Phase 1 implements `GET /api/health`. The `/api/v1` prefix remains reserved for future versioned product APIs.

## Portfolios

- `GET /api/v1/portfolios`
- `POST /api/v1/portfolios`
- `GET /api/v1/portfolios/{portfolio_id}`
- `PATCH /api/v1/portfolios/{portfolio_id}`
- `DELETE /api/v1/portfolios/{portfolio_id}`

Purpose: portfolio lifecycle.

## Holdings

- `GET /api/v1/portfolios/{portfolio_id}/holdings`
- `POST /api/v1/portfolios/{portfolio_id}/holdings`
- `PATCH /api/v1/portfolios/{portfolio_id}/holdings/{holding_id}`
- `DELETE /api/v1/portfolios/{portfolio_id}/holdings/{holding_id}`

Purpose: validated portfolio holdings.

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
