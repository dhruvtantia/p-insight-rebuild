# Backend Feature Implementation Summary

Date: 2026-05-21

## Verification

- Full backend test suite: `193 passed`.
- App startup verified with `create_app()`.
- Registered `/api` routes were inspected from the FastAPI app instance.
- No frontend files were changed in this review task.
- No real AI calls were added. AI advisor remains deterministic/mock.

## Modules Added

### Performance

Path: `backend/app/modules/performance`

Purpose: synthetic portfolio performance history using current holdings and historical prices.

Notes:

- Uses `MarketHistoryService`.
- Explicitly labels method as `synthetic_current_holdings`.
- Does not call the result XIRR or TWR.

### Risk V2

Paths:

- `backend/app/modules/analytics/calculators/risk_v2`
- `backend/app/modules/risk`

Purpose: isolated risk calculator utilities plus feature-flagged portfolio risk endpoint.

Metrics include volatility, Sharpe, Sortino, drawdown, VaR, beta, tracking error, information ratio, and correlation matrix when available.

### Snapshots

Path: `backend/app/modules/snapshots`

Purpose: create, list, and compare portfolio snapshots using the existing `PortfolioSnapshot` model/table.

Migration status: no migration was needed. See `docs/snapshot-model-review.md`.

### Fundamentals

Path: `backend/app/modules/fundamentals`

Purpose: fundamentals provider contract, mock fundamentals provider, single-asset and portfolio fundamentals.

Notes:

- Mock fundamentals are allowed only in local/test/demo/development.
- Unknown symbols return no fabricated metrics and explicit missing coverage.

### Peers

Path: `backend/app/modules/peers`

Purpose: static India peer comparison using `FundamentalsService`.

Notes:

- Peer map is static and intentionally labeled in warnings.
- Does not duplicate fundamentals logic.

### Simulator

Path: `backend/app/modules/simulator`

Purpose: backend-only allocation scenario simulator.

Notes:

- Does not execute trades.
- Does not persist scenarios.
- Normalizes non-100 target weights with warnings.

### Optimizer

Path: `backend/app/modules/optimizer`

Purpose: deterministic long-only optimizer using historical mock data path.

Notes:

- No SciPy or heavy dependency was added.
- Returns clean `insufficient_history` responses when inputs are not usable.
- Includes assumptions: long-only, no taxes, no transaction costs, no liquidity constraints, historical estimates only, not investment advice.

### Rebalance Tickets

Path: `backend/app/modules/rebalance`

Purpose: convert target weights into estimated buy/sell/hold tickets from current holdings and current prices.

Notes:

- Does not execute trades.
- Does not persist tickets.
- Skips missing-price symbols with warnings.

### AI Advisor Context Expansion

Path: `backend/app/modules/ai_advisor/context_builder.py`

Purpose: optional advisor context blocks when feature services are enabled and available.

Optional blocks:

- `dashboard_summary`
- `performance_history_summary`
- `risk_v2_summary`
- `fundamentals_summary`
- `peer_summary`
- `snapshot_change_summary`

Missing optional services are isolated and do not break advisor responses.

## Endpoints Added

Feature-gated endpoints:

- `GET /api/portfolios/{portfolio_id}/performance/history?period=1Y`
- `GET /api/portfolios/{portfolio_id}/risk?period=1Y`
- `POST /api/portfolios/{portfolio_id}/snapshots`
- `GET /api/portfolios/{portfolio_id}/snapshots`
- `GET /api/portfolios/{portfolio_id}/snapshots/compare?from_id=&to_id=`
- `GET /api/assets/{symbol}/fundamentals`
- `GET /api/portfolios/{portfolio_id}/fundamentals`
- `GET /api/portfolios/{portfolio_id}/peers/{symbol}`
- `POST /api/portfolios/{portfolio_id}/simulate`
- `POST /api/portfolios/{portfolio_id}/optimize`
- `POST /api/portfolios/{portfolio_id}/rebalance/tickets`

Existing endpoints left unchanged:

- `/api/portfolios/{portfolio_id}/analytics/*`
- `/api/portfolios/{portfolio_id}/dashboard`
- `/api/portfolios/{portfolio_id}/ai/*`
- Market data, uploads, watchlist, billing, broker placeholder, health/demo routes.

## Feature Flags

The feature flag registry includes:

- `ENABLE_MARKET_OVERVIEW`
- `ENABLE_DASHBOARD_BUNDLE`
- `ENABLE_UPLOAD_SUGGESTIONS`
- `ENABLE_HISTORICAL_DATA`
- `ENABLE_PERFORMANCE_HISTORY`
- `ENABLE_RISK_V2`
- `ENABLE_SNAPSHOTS`
- `ENABLE_FUNDAMENTALS`
- `ENABLE_PEERS`
- `ENABLE_SIMULATOR`
- `ENABLE_OPTIMIZER`
- `ENABLE_REBALANCE_TICKETS`

New modular endpoints are gated as follows:

| Module | Flag |
| --- | --- |
| Performance history | `ENABLE_PERFORMANCE_HISTORY` |
| Risk v2 | `ENABLE_RISK_V2` |
| Snapshots | `ENABLE_SNAPSHOTS` |
| Fundamentals | `ENABLE_FUNDAMENTALS` |
| Peers | `ENABLE_PEERS` |
| Simulator | `ENABLE_SIMULATOR` |
| Optimizer | `ENABLE_OPTIMIZER` |
| Rebalance tickets | `ENABLE_REBALANCE_TICKETS` |

Feature-disabled behavior returns `404` with `feature_disabled`.

## Router Registration

`backend/app/main.py` registers the modular routers in the FastAPI app. Startup inspection confirmed these new routes are present:

- `/api/assets/{symbol}/fundamentals`
- `/api/portfolios/{portfolio_id}/fundamentals`
- `/api/portfolios/{portfolio_id}/performance/history`
- `/api/portfolios/{portfolio_id}/risk`
- `/api/portfolios/{portfolio_id}/snapshots`
- `/api/portfolios/{portfolio_id}/snapshots/compare`
- `/api/portfolios/{portfolio_id}/peers/{symbol}`
- `/api/portfolios/{portfolio_id}/simulate`
- `/api/portfolios/{portfolio_id}/optimize`
- `/api/portfolios/{portfolio_id}/rebalance/tickets`

## Auth And Ownership Review

Portfolio-scoped modules use `CurrentUser` in routers and enforce ownership through `PortfolioService.get_portfolio(...)` in service code:

- Performance
- Risk v2
- Snapshots
- Portfolio fundamentals
- Peers
- Simulator
- Optimizer
- Rebalance tickets
- Existing analytics/dashboard/holdings/uploads/market-data refresh paths

Non-portfolio single-asset fundamentals endpoint does not require ownership because it is symbol-level public-style market/fundamental data, but it is feature-gated.

## Mock And Demo Dependencies Remaining

### Market Data

- Default provider remains `mock_india`.
- Production mock market data is blocked unless `ALLOW_PRODUCTION_MOCK_MARKET_DATA=true`.
- Mock quotes are labeled through `DataStatus.mock_source`.

### Historical Data

- `MarketHistoryService.build_mock_response(...)` uses deterministic historical prices from `backend/app/modules/demo/fixtures/historical_prices.py`.
- Mock historical data is blocked in production unless production mock market data override is explicitly enabled.
- Historical mock responses are labeled with provider `mock_historical_prices`.

### Fundamentals

- `MockFundamentalsProvider` is deterministic and labeled as `mock_fundamentals`.
- It is blocked outside local/test/demo/development.
- Unknown symbols produce missing coverage, not fabricated fundamentals.

### AI Advisor

- Advisor remains deterministic/mock.
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` only changes provider metadata to `openai-ready-mock` / `anthropic-ready-mock`; it does not trigger real AI calls.
- Direct buy/sell wording is filtered from responses.

### Peers

- Static India peer map is intentionally sparse.
- Peer responses include warnings for static/mock/sparse peer sets.

## Secrets Review

No new frontend secrets were introduced.

Current frontend environment usage remains limited to public/client-safe variables such as:

- `VITE_API_BASE_URL`
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_APP_ENV`
- `VITE_ENABLE_DEMO_MODE`
- telemetry/feedback public keys/URLs

Backend-only secrets remain backend configuration concerns:

- Market data provider keys
- AI provider keys
- Supabase service role key
- Stripe secret/webhook keys
- database URL

## Manual QA Checklist For Frontend Integration

Before wiring each feature in the frontend:

- Confirm the matching backend flag is enabled in the target environment.
- Confirm disabled flags render a frontend “coming soon” or unavailable state rather than treating `404 feature_disabled` as a crash.
- Confirm all mock or static outputs are visually labeled as mock, synthetic, static, or estimates.
- Confirm performance history displays the synthetic assumptions and does not label returns as XIRR or TWR.
- Confirm optimizer and rebalance outputs are labeled as estimates, not trading instructions.
- Confirm rebalance ticket UI does not expose an execution action.
- Confirm advisor UI can show that optional context was used without implying a real AI provider call.
- Confirm empty portfolios and missing price/fundamental coverage states render cleanly.
- Confirm portfolio-scoped calls use the selected portfolio id and handle `404 not_found`.
- Confirm no provider secret or server key is added to frontend env or code.

Suggested smoke requests:

- `GET /api/portfolios/{id}/performance/history?period=1Y`
- `GET /api/portfolios/{id}/risk?period=1Y`
- `POST /api/portfolios/{id}/snapshots`
- `GET /api/portfolios/{id}/snapshots`
- `GET /api/assets/RELIANCE/fundamentals`
- `GET /api/portfolios/{id}/fundamentals`
- `GET /api/portfolios/{id}/peers/RELIANCE`
- `POST /api/portfolios/{id}/simulate`
- `POST /api/portfolios/{id}/optimize`
- `POST /api/portfolios/{id}/rebalance/tickets`

## Recommended Frontend Implementation Order

1. Feature flag handling and shared disabled-state UI.
2. Performance history chart with synthetic assumptions shown clearly.
3. Risk v2 panel using metric status fields.
4. Fundamentals views: asset first, then portfolio aggregate.
5. Peer comparison table with static/mock/sparse warnings.
6. Snapshots: create/list first, then comparison view.
7. Simulator UI for hypothetical allocation scenarios.
8. Optimizer UI with assumptions and insufficient-history handling.
9. Rebalance ticket estimator last, with strong “not execution” labeling.
10. Advisor context indicators after the above data views exist, so optional context can link back to visible panels.

## Current Decision Summary

- Backend is modular and feature-gated.
- Existing `/analytics` behavior remains unchanged.
- Mock data remains isolated and labeled.
- Portfolio ownership is enforced through `PortfolioService.get_portfolio` for portfolio-scoped modules.
- No new migrations are needed for the snapshot implementation.
- No frontend secrets or new frontend behavior were introduced in this review task.
