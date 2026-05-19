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

- `POST /api/portfolios/{portfolio_id}/uploads`
- `GET /api/uploads/{upload_job_id}`
- `POST /api/uploads/{upload_job_id}/column-mapping`
- `POST /api/uploads/{upload_job_id}/validate`
- `POST /api/uploads/{upload_job_id}/confirm`
- `GET /api/uploads/{upload_job_id}/errors`

Purpose: validate uploaded rows before writing holdings.

Upload request:

```http
POST /api/portfolios/{portfolio_id}/uploads
Content-Type: multipart/form-data

file=<csv-or-xlsx-file>
```

Upload response:

```json
{
  "id": "upload-job-id",
  "portfolio_id": "portfolio-id",
  "filename": "holdings.csv",
  "status": "uploaded",
  "total_rows": 2,
  "valid_rows": 0,
  "invalid_rows": 0,
  "detected_columns": ["Ticker", "Name", "Shares", "Average Cost", "Market Value"],
  "preview_rows": [
    {
      "Ticker": "AAPL",
      "Name": "Apple Inc.",
      "Shares": "10",
      "Average Cost": "100",
      "Market Value": "1250"
    }
  ],
  "created_at": "2026-05-19T00:00:00Z",
  "updated_at": "2026-05-19T00:00:00Z"
}
```

Column mapping request:

```json
{
  "mapping": {
    "symbol": "Ticker",
    "company_name": "Name",
    "quantity": "Shares",
    "average_cost": "Average Cost",
    "market_value": "Market Value",
    "currency": "Currency",
    "sector": "Sector",
    "asset_class": "Asset Class",
    "exchange": "Exchange"
  }
}
```

Supported mapped fields:
- `symbol`
- `company_name`
- `quantity`
- `average_cost`
- `market_value`
- `currency`
- `sector`
- `asset_class`
- `exchange`

Required mapped fields:
- `symbol`
- `quantity`

Validation behavior:
- `symbol` is required.
- `quantity` must be positive.
- `average_cost` cannot be negative when present.
- `market_value` cannot be negative when present.
- `currency` defaults to the portfolio base currency.
- `asset_class` defaults to `Equity`.
- Each row is marked `valid` or `invalid` with row-level validation errors.

Confirm response:

```json
{
  "upload_job_id": "upload-job-id",
  "status": "partial_imported",
  "imported_count": 1,
  "skipped_count": 1,
  "invalid_rows": 1,
  "warnings": [
    "Row 2: AAPL skipped because it already exists in the portfolio or upload batch",
    "Partial import occurred: 1 invalid row(s) were not imported"
  ],
  "created_holding_ids": ["holding-id"]
}
```

Duplicate behavior:
- Existing portfolio symbols are skipped on confirm import.
- Repeated symbols within the same upload are skipped after the first importable occurrence.
- Skipped duplicates are reported as warnings and cause `partial_imported`.

## Market Data

- `GET /api/market-data/prices?symbols=AAPL,MSFT`
- `GET /api/market-data/prices/{symbol}`
- `GET /api/market-data/history/{symbol}?start=2026-01-01&end=2026-01-31`
- `POST /api/portfolios/{portfolio_id}/prices/refresh`

Purpose: backend-only market data access and portfolio holding price refresh.

Latest price response:

```json
{
  "symbol": "AAPL",
  "price": 210.12,
  "currency": "USD",
  "source": "mock",
  "as_of": "2026-01-01T00:00:00Z",
  "is_realtime": false
}
```

Batch price response:

```json
{
  "prices": [
    {
      "symbol": "AAPL",
      "price": 210.12,
      "currency": "USD",
      "source": "mock",
      "as_of": "2026-01-01T00:00:00Z",
      "is_realtime": false
    },
    {
      "symbol": "MSFT",
      "price": 425.44,
      "currency": "USD",
      "source": "mock",
      "as_of": "2026-01-01T00:00:00Z",
      "is_realtime": false
    }
  ]
}
```

History response:

```json
{
  "symbol": "AAPL",
  "start": "2026-01-01",
  "end": "2026-01-03",
  "prices": [
    {
      "symbol": "AAPL",
      "date": "2026-01-01",
      "close": 207.49,
      "currency": "USD",
      "source": "mock"
    }
  ]
}
```

Portfolio refresh response:

```json
{
  "portfolio_id": "portfolio-id",
  "refreshed_count": 2,
  "prices": [
    {
      "symbol": "AAPL",
      "price": 210.12,
      "currency": "USD",
      "source": "mock",
      "as_of": "2026-01-01T00:00:00Z",
      "is_realtime": false
    }
  ],
  "holdings": [
    {
      "holding_id": "holding-id",
      "symbol": "AAPL",
      "previous_price": 125,
      "current_price": 210.12,
      "currency": "USD",
      "source": "mock",
      "as_of": "2026-01-01T00:00:00Z",
      "is_realtime": false
    }
  ]
}
```

Provider behavior:
- Default provider is `mock`.
- Mock prices are deterministic for `AAPL`, `MSFT`, `GOOGL`, `AMZN`, `TSLA`, `NVDA`, `SPY`, `VOO`, and `QQQ`.
- Unknown mock symbols receive a deterministic pseudo-price based on the normalized symbol.
- Latest and refresh calls insert `asset_prices` records.
- Refresh updates `holding.current_price` for all holdings in the portfolio.
- `polygon`/`massive` and `fmp` providers are backend placeholders. They require backend environment keys and return clear provider errors until implemented.

## Analytics

- `GET /api/portfolios/{portfolio_id}/analytics/summary`
- `GET /api/portfolios/{portfolio_id}/analytics/allocation`
- `GET /api/portfolios/{portfolio_id}/analytics/risk`
- `GET /api/portfolios/{portfolio_id}/analytics/performance`
- `GET /api/portfolios/{portfolio_id}/analytics/rules`
- `POST /api/portfolios/{portfolio_id}/analytics/recalculate`

Purpose: backend-owned analytics and rule-based insights.

Summary response:

```json
{
  "portfolio_id": "portfolio-id",
  "base_currency": "USD",
  "total_portfolio_value": 4000,
  "total_cost_basis": 2500,
  "total_unrealized_gain_loss": 1500,
  "total_unrealized_gain_loss_pct": 0.6,
  "largest_holding": {
    "symbol": "AAPL",
    "market_value": 2000,
    "weight": 0.5
  },
  "holdings": [
    {
      "holding_id": "holding-id",
      "symbol": "AAPL",
      "quantity": 10,
      "average_cost": 100,
      "current_price": 200,
      "currency": "USD",
      "sector": "Technology",
      "asset_class": "Equity",
      "market_value": 2000,
      "cost_basis": 1000,
      "unrealized_gain_loss": 1000,
      "unrealized_gain_loss_pct": 1,
      "weight": 0.5
    }
  ]
}
```

Allocation response:

```json
{
  "asset_allocation": [
    {
      "name": "Equity",
      "value": 2000,
      "weight": 0.5,
      "symbols": ["AAPL"]
    }
  ],
  "sector_allocation": [
    {
      "name": "Technology",
      "value": 2000,
      "weight": 0.5,
      "symbols": ["AAPL"]
    }
  ],
  "currency_exposure": [
    {
      "name": "USD",
      "value": 4000,
      "weight": 1,
      "symbols": ["AAPL", "VOO"]
    }
  ]
}
```

Risk response:

```json
{
  "volatility": {
    "value": null,
    "status": "insufficient_history",
    "message": "Historical price data is not available yet."
  },
  "sharpe_ratio": {
    "value": null,
    "status": "insufficient_history",
    "message": "Historical price data is not available yet."
  },
  "max_drawdown": {
    "value": null,
    "status": "insufficient_history",
    "message": "Historical price data is not available yet."
  },
  "concentration": {
    "status": "high",
    "largest_holding": {
      "symbol": "AAPL",
      "market_value": 3000,
      "weight": 0.75
    },
    "top_5_weight": 1,
    "message": "AAPL represents 75% of the portfolio."
  }
}
```

Performance response:

```json
{
  "total_cost_basis": 2500,
  "total_unrealized_gain_loss": 1500,
  "total_unrealized_gain_loss_pct": 0.6,
  "top_gainers": [
    {
      "symbol": "AAPL",
      "unrealized_gain_loss": 1000,
      "unrealized_gain_loss_pct": 1
    }
  ],
  "top_losers": []
}
```

Rules response:

```json
[
  {
    "rule_id": "HIGH_CONCENTRATION",
    "severity": "high",
    "title": "High concentration risk",
    "message": "AAPL represents 32% of your portfolio.",
    "affected_symbols": ["AAPL"]
  }
]
```

Implemented rule IDs:
- `HIGH_CONCENTRATION` when one holding is more than 25% of priced portfolio value.
- `MODERATE_CONCENTRATION` when one holding is more than 15% of priced portfolio value.
- `MISSING_PRICE_DATA` when holdings have no `current_price`.
- `MISSING_COST_BASIS` when holdings have no `average_cost`.
- `SINGLE_ASSET_CLASS` when all holdings have the same `asset_class`.
- `CURRENCY_EXPOSURE` when non-base-currency exposure is more than 20% of priced portfolio value.

Recalculate behavior:
- `POST /api/portfolios/{portfolio_id}/analytics/recalculate` computes the full analytics bundle.
- It stores `summary`, `allocation`, `risk`, `performance`, `rules`, and `analytics_bundle` records in `analytics_results`.
- Empty portfolios and missing prices return zero/empty analytics instead of failing.

## AI Advisor

- `POST /api/portfolios/{portfolio_id}/ai/summary`
- `POST /api/portfolios/{portfolio_id}/ai/question`
- `GET /api/portfolios/{portfolio_id}/ai/conversations`
- `GET /api/ai/conversations/{conversation_id}`

Purpose: AI explanations generated only from structured backend portfolio context.

Context shape:

```json
{
  "portfolio_summary": {
    "id": "portfolio-id",
    "name": "Core Portfolio",
    "base_currency": "USD",
    "benchmark_symbol": "SPY",
    "risk_free_rate": 0.04,
    "total_portfolio_value": 4000,
    "total_cost_basis": 2500,
    "total_unrealized_gain_loss": 1500,
    "total_unrealized_gain_loss_pct": 0.6,
    "largest_holding": {
      "symbol": "AAPL",
      "market_value": 2000,
      "weight": 0.5
    },
    "holdings_count": 2
  },
  "holdings": [],
  "risk_metrics": {},
  "allocation": {},
  "rule_based_insights": [],
  "price_freshness": {
    "priced_symbols": ["AAPL"],
    "missing_price_symbols": [],
    "latest_price_as_of": "2026-01-01T00:00:00Z",
    "latest_price_source": "mock"
  },
  "user_question": ""
}
```

Summary request:

```http
POST /api/portfolios/{portfolio_id}/ai/summary
Content-Type: application/json

{}
```

Question request:

```json
{
  "question": "What concentration risk should I review?"
}
```

AI response:

```json
{
  "conversation_id": "conversation-id",
  "mode": "question",
  "provider": "mock",
  "model": "deterministic-advisor-v1",
  "response": "Based on the provided data, ...",
  "context": {
    "portfolio_summary": {},
    "holdings": [],
    "risk_metrics": {},
    "allocation": {},
    "rule_based_insights": [],
    "price_freshness": {},
    "user_question": "What concentration risk should I review?"
  },
  "created_at": "2026-05-19T00:00:00Z"
}
```

Conversation list response:

```json
[
  {
    "id": "conversation-id",
    "portfolio_id": "portfolio-id",
    "title": "Summary for Core Portfolio",
    "mode": "summary",
    "created_at": "2026-05-19T00:00:00Z",
    "updated_at": "2026-05-19T00:00:00Z"
  }
]
```

Conversation detail response:

```json
{
  "id": "conversation-id",
  "portfolio_id": "portfolio-id",
  "title": "Summary for Core Portfolio",
  "mode": "summary",
  "context": {},
  "messages": [
    {
      "id": "message-id",
      "conversation_id": "conversation-id",
      "role": "user",
      "content": "Summarize this portfolio.",
      "provider": null,
      "model": null,
      "metadata": {
        "mode": "summary"
      },
      "created_at": "2026-05-19T00:00:00Z"
    }
  ],
  "created_at": "2026-05-19T00:00:00Z",
  "updated_at": "2026-05-19T00:00:00Z"
}
```

Provider behavior:
- If no `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` is configured, the backend returns deterministic mock advisor responses.
- If provider keys exist, the code records provider-ready model metadata but still uses the deterministic MVP response path until real provider calls are implemented.
- No frontend AI keys are required or exposed.

Safety language:
- Advisor responses are educational and non-directive.
- Responses avoid phrases such as direct buy/sell instructions, guaranteed returns, or claims that something will outperform.
- Preferred phrasing includes "Based on the provided data", "This suggests", "One risk to review is", and "You may want to compare".

Persistence:
- Each summary or question request creates an `AIConversation`.
- The system prompt, user message, and assistant response are persisted as `AIMessage` records.
- Conversation context stores mode and structured context JSON.

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
