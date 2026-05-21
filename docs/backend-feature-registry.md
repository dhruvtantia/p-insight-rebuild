# Backend Feature Registry

Date: 2026-05-21

Scope: registry of backend modules currently present in `backend/app/modules`, how they are exposed, their modularity and safety status, and whether they are ready for frontend integration. This document is an audit artifact only. No product behavior was changed.

Sources inspected:
- `backend/app/main.py`
- `backend/app/modules/*`
- `backend/app/core/feature_flags.py`
- `backend/app/core/config.py`
- `backend/app/tests/*`
- `docs/modularity-and-isolation-audit.md`
- `docs/frontend-integration-architecture-plan.md`
- `docs/backend-feature-implementation-summary.md`
- `docs/mock-data-audit.md`

## Verification

Current verification from this registry task:
- Backend tests: passed with `backend/.venv/bin/pytest backend/app/tests`: `193 passed in 7.99s`.
- Frontend build: passed with `npm run build` from `frontend/`.
- Frontend build warning: Vite emitted the existing non-failing chunk-size warning for `dist/assets/index-QHCaoEgh.js` at 834.59 kB before gzip.
- Note: `/Users/dhruvtantia/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m pytest backend/app/tests` and `backend/.venv/bin/python -m pytest backend/app/tests` both failed before collection because `pytest` was not importable as a Python module in those runtimes. The executable `backend/.venv/bin/pytest` is functional and was used for verification.

Previously recorded in the inspected audit docs:
- Backend tests passed: `193 passed`.
- App startup/import passed.
- Frontend build passed with a non-failing Vite chunk-size warning.

## Registry Summary

`backend/app/main.py` registers all routers unconditionally. Feature flags are request-time gates implemented in each feature router through `require_feature_enabled(...)`, returning `404` with `error_code = "feature_disabled"` when disabled.

| Feature | Module exists | Router exposed | Feature flag | DataStatus | Auth/ownership | Modularity | Frontend readiness |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Market overview | Yes | Yes | `ENABLE_MARKET_OVERVIEW` | Yes | Public market endpoint | Modular | Partial |
| Dashboard bundle | Yes | Yes | `ENABLE_DASHBOARD_BUNDLE` | Yes | Portfolio-owned | Modular | Ready |
| Upload suggestions/import summary | Yes | Yes | Suggestions only: `ENABLE_UPLOAD_SUGGESTIONS` | No | Upload job resolves through owned portfolio | Modular within uploads | Ready |
| Sector metadata | Yes | Existing holdings/upload endpoints | None | No | Portfolio-owned | Modular within holdings/uploads | Ready |
| Historical market data | Yes | Yes | New endpoint: `ENABLE_HISTORICAL_DATA` | Yes | Public market endpoint | Modular, with demo fixture dependency | Partial |
| Performance history | Yes | Yes | `ENABLE_PERFORMANCE_HISTORY` | Yes | Portfolio-owned | Modular | Partial |
| Risk v2 | Yes | Yes | `ENABLE_RISK_V2` | Yes | Portfolio-owned through performance service | Modular | Partial |
| Snapshots | Yes | Yes | `ENABLE_SNAPSHOTS` | No | Portfolio-owned | Modular | Ready |
| Fundamentals | Yes | Yes | `ENABLE_FUNDAMENTALS` | Yes | Portfolio endpoint owned; asset endpoint public-style | Modular | Partial |
| Peers | Yes | Yes | `ENABLE_PEERS` | Via nested fundamentals | Portfolio-owned | Modular | Partial |
| Advisor context | Yes | Existing advisor endpoints | Advisor not gated; optional blocks gated by source features | Partial via optional blocks | Portfolio/conversation-owned | Modular enough, broad read dependencies | Partial |
| Simulator | Yes | Yes | `ENABLE_SIMULATOR` | No | Portfolio-owned | Modular | Partial |
| Optimizer | Yes | Yes | `ENABLE_OPTIMIZER` | Yes | Portfolio-owned | Modular | Partial |
| Rebalance tickets | Yes | Yes | `ENABLE_REBALANCE_TICKETS` | No | Portfolio-owned | Modular | Partial |
| Watchlist | Yes | Yes | None | Price source fields only | User-owned | Modular | Ready |

Frontend readiness scale:
- Ready: contract is usable for frontend integration with normal loading/empty/error handling.
- Partial: contract is usable for local/demo integration only, or needs frontend warnings/contract cleanup before broad use.
- Not ready: module exists but should not be integrated yet. None of the covered modules are completely absent, but several are partial because they depend on mock/static/synthetic data.

## Feature Records

### Market Overview

- Feature name: Market overview
- Module path: `backend/app/modules/market_overview`
- Router path: `backend/app/modules/market_overview/router.py`
- Service path: `backend/app/modules/market_overview/service.py`
- Schema path: `backend/app/modules/market_overview/schemas.py`
- Endpoint(s): `GET /api/market/overview`
- Feature flag: `ENABLE_MARKET_OVERVIEW`
- Dependencies: `MarketDataService`, configured market data provider, `DataStatus`
- Mock/demo dependency: Static India index definitions and mock-only mover candidates are used with `mock`/`mock_india` providers. Provider output is labeled.
- DataStatus support: Yes. Top-level overview, market status, index cards, sector index cards, and movers include `DataStatus`.
- Auth/ownership protection: Public market endpoint. No portfolio ownership required.
- Tests present: `test_market_overview_api.py`, `test_market_overview_schemas.py`, `test_market_overview_service.py`
- Known gaps: Demo/static data caveat; real provider support depends on future market provider implementation. No auth requirement by design.
- Frontend readiness: Partial. Ready for demo/local integration with visible mock/stale labels; not production-grade market data.
- Recommended frontend page placement: New `/market` or `MarketOverviewPage`; optional compact market status in the header after shared `DataStatusBadge`.

### Dashboard Bundle

- Feature name: Dashboard bundle
- Module path: `backend/app/modules/dashboard`
- Router path: `backend/app/modules/dashboard/router.py`
- Service path: `backend/app/modules/dashboard/service.py`
- Schema path: `backend/app/modules/dashboard/schemas.py`
- Endpoint(s): `GET /api/portfolios/{portfolio_id}/dashboard`
- Feature flag: `ENABLE_DASHBOARD_BUNDLE`
- Dependencies: `PortfolioService`, `AnalyticsService`, `MarketDataService`, holdings and latest asset prices
- Mock/demo dependency: Uses current stored price source and provider-derived data quality. Mock prices are labeled through `DataStatus`.
- DataStatus support: Yes. Bundle-level `data_status` and `data_quality.data_status`.
- Auth/ownership protection: Yes. Router uses `CurrentUser`; service calls `PortfolioService.get_portfolio(..., user=...)`.
- Tests present: `test_dashboard_api.py`, `test_dashboard_schemas.py`, `test_dashboard_service.py`
- Known gaps: Router is always registered and flag-gated at request time. Dashboard content is only as reliable as underlying price and analytics inputs.
- Frontend readiness: Ready. This is the best first portfolio-scoped integration target.
- Recommended frontend page placement: Existing `DashboardPage`, replacing current frontend-composed dashboard sections after shared UI extraction.

### Upload Suggestions And Import Summary

- Feature name: Upload suggestions/import summary
- Module path: `backend/app/modules/uploads`
- Router path: `backend/app/modules/uploads/router.py`
- Service path: `backend/app/modules/uploads/service.py`
- Schema path: `backend/app/modules/uploads/schemas.py`
- Endpoint(s):
  - `POST /api/portfolios/{portfolio_id}/uploads`
  - `GET /api/uploads/{upload_job_id}`
  - `POST /api/uploads/{upload_job_id}/column-mapping`
  - `GET /api/uploads/{upload_job_id}/mapping-suggestions`
  - `POST /api/uploads/{upload_job_id}/validate`
  - `POST /api/uploads/{upload_job_id}/confirm`
  - `GET /api/uploads/{upload_job_id}/errors`
- Feature flag: `ENABLE_UPLOAD_SUGGESTIONS` gates mapping suggestions only. Upload/import flow is core and ungated.
- Dependencies: `PortfolioService`, `UploadRepository`, `HoldingRepository`, `column_detection`, symbol normalization/metadata
- Mock/demo dependency: None for upload mechanics. Input files may be demo/sample CSVs.
- DataStatus support: No. Upload responses include validation warnings and import summary warnings, not market data status.
- Auth/ownership protection: Yes. Upload jobs are resolved through their portfolio, and the portfolio is checked with `PortfolioService.get_portfolio(..., user=...)`.
- Tests present: `test_upload_column_detection.py`, `test_upload_mapping_suggestions_api.py`, `test_uploads_api.py`
- Known gaps: Suggestions are deterministic heuristics, not auto-applied. Frontend types currently need updates for row warnings, invalid/duplicate counts, and rejected row reasons.
- Frontend readiness: Ready. Suggestions can be added to the existing upload wizard without changing upload behavior.
- Recommended frontend page placement: Existing `UploadPage`, mapping step.

### Sector Metadata

- Feature name: Sector metadata
- Module path: `backend/app/modules/holdings` and `backend/app/modules/uploads`
- Router path: `backend/app/modules/holdings/router.py`, `backend/app/modules/uploads/router.py`
- Service path: `backend/app/modules/holdings/service.py`, `backend/app/modules/uploads/service.py`
- Schema path: `backend/app/modules/holdings/schemas.py`, `backend/app/modules/uploads/schemas.py`
- Endpoint(s):
  - Existing holdings CRUD: `/api/portfolios/{portfolio_id}/holdings`
  - Upload confirm path: `POST /api/uploads/{upload_job_id}/confirm`
- Feature flag: None. This is a metadata extension, not a standalone flagged feature.
- Dependencies: holdings model fields `sector_source`, `sector_updated_at`, `asset_class`; symbol metadata fallback
- Mock/demo dependency: None directly. Upload and manual entry can use sample data.
- DataStatus support: No. Sector metadata has provenance fields instead: `sector_source` and `sector_updated_at`.
- Auth/ownership protection: Yes. Holdings routes use `CurrentUser` and portfolio ownership checks.
- Tests present: `test_portfolios_holdings_api.py`, `test_uploads_api.py`
- Known gaps: No standalone sector taxonomy/provider. Source values are simple strings such as `manual` and `upload`.
- Frontend readiness: Ready.
- Recommended frontend page placement: Existing `HoldingsPage`, upload preview/import summary, analytics allocation views.

### Historical Market Data

- Feature name: Historical market data
- Module path: `backend/app/modules/market_data`
- Router path: `backend/app/modules/market_data/router.py`
- Service path: `backend/app/modules/market_data/history_service.py`, plus legacy `backend/app/modules/market_data/service.py`
- Schema path: `backend/app/modules/market_data/history_schemas.py`, legacy `backend/app/modules/market_data/schemas.py`
- Endpoint(s):
  - New contract: `GET /api/market/history?symbols=RELIANCE,TCS&period=1Y`
  - Legacy endpoint: `GET /api/market-data/history/{symbol}?start=&end=`
- Feature flag: `ENABLE_HISTORICAL_DATA` gates only the new `/api/market/history` endpoint. Legacy `/api/market-data/history/{symbol}` is not gated.
- Dependencies: `MarketHistoryService`, symbol normalization, demo historical fixtures, `DataStatus`
- Mock/demo dependency: `MarketHistoryService.build_mock_response(...)` imports deterministic data from `backend/app/modules/demo/fixtures/historical_prices.py`; production mock history is blocked unless production mock market-data override is explicitly enabled.
- DataStatus support: Yes for the new historical contract. Legacy history points have optional `data_status`.
- Auth/ownership protection: Public market endpoint. No portfolio ownership required.
- Tests present: `test_market_history_api.py`, `test_market_history_contract.py`, `test_mock_historical_prices.py`, `test_market_data.py`
- Known gaps: Real historical provider not implemented. Legacy endpoint bypasses `ENABLE_HISTORICAL_DATA`. Demo fixture dependency weakens isolation.
- Frontend readiness: Partial. Use only with explicit mock/synthetic labeling.
- Recommended frontend page placement: Shared `marketHistoryApi` foundation for performance/risk/research charts; avoid standalone production claims.

### Performance History

- Feature name: Performance history
- Module path: `backend/app/modules/performance`
- Router path: `backend/app/modules/performance/router.py`
- Service path: `backend/app/modules/performance/service.py`
- Schema path: `backend/app/modules/performance/schemas.py`
- Endpoint(s): `GET /api/portfolios/{portfolio_id}/performance/history?period=1Y`
- Feature flag: `ENABLE_PERFORMANCE_HISTORY`
- Dependencies: `PortfolioService`, holdings, `MarketHistoryService`, benchmark symbol, `DataStatus`
- Mock/demo dependency: Uses `MarketHistoryService.build_mock_response(...)`; method is explicitly labeled `synthetic_current_holdings`.
- DataStatus support: Yes. Response has top-level `data_status` and explicit assumptions.
- Auth/ownership protection: Yes. Router uses `CurrentUser`; service calls `PortfolioService.get_portfolio(..., user=...)`.
- Tests present: `test_performance_api.py`, `test_performance_service.py`
- Known gaps: Synthetic current-holdings history, not transaction-aware, not XIRR, not TWR. Real historical provider and transaction history are absent.
- Frontend readiness: Partial. Demo-ready with prominent assumptions and mock/stale labels.
- Recommended frontend page placement: Analytics performance panel or future `PerformancePage`; can replace the dashboard history placeholder only with clear assumptions.

### Risk V2

- Feature name: Risk v2
- Module path: `backend/app/modules/risk`, calculators in `backend/app/modules/analytics/calculators/risk_v2`
- Router path: `backend/app/modules/risk/router.py`
- Service path: `backend/app/modules/risk/service.py`
- Schema path: `backend/app/modules/risk/schemas.py`
- Endpoint(s): `GET /api/portfolios/{portfolio_id}/risk?period=1Y`
- Feature flag: `ENABLE_RISK_V2`
- Dependencies: `PerformanceService`, risk v2 calculator utilities, benchmark returns, `DataStatus`
- Mock/demo dependency: Inherits synthetic/mock historical data from performance history.
- DataStatus support: Yes. Response includes top-level `data_status`, metric statuses, and assumptions.
- Auth/ownership protection: Yes. Ownership is enforced through `PerformanceService.get_history(...)`.
- Tests present: `test_risk_v2_api.py`, `test_risk_v2_calculators.py`
- Known gaps: No direct cross-user API test and no direct service tests with injected performance data. Metrics are only as reliable as synthetic history.
- Frontend readiness: Partial. Demo-ready with metric status and assumptions visible.
- Recommended frontend page placement: Analytics risk panel or future `RiskPage`.

### Snapshots

- Feature name: Snapshots
- Module path: `backend/app/modules/snapshots`
- Router path: `backend/app/modules/snapshots/router.py`
- Service path: `backend/app/modules/snapshots/service.py`
- Schema path: `backend/app/modules/snapshots/schemas.py`
- Endpoint(s):
  - `POST /api/portfolios/{portfolio_id}/snapshots`
  - `GET /api/portfolios/{portfolio_id}/snapshots`
  - `GET /api/portfolios/{portfolio_id}/snapshots/compare?from_id=&to_id=`
- Feature flag: `ENABLE_SNAPSHOTS`
- Dependencies: `PortfolioService`, holdings, analytics allocation/concentration calculators, `PortfolioSnapshot` model
- Mock/demo dependency: None directly. Snapshot content can include mock-priced holdings if the portfolio does.
- DataStatus support: No. Stored snapshot JSON includes `source: "manual"`, but response schemas do not expose `DataStatus`.
- Auth/ownership protection: Yes. Every operation checks the portfolio with `PortfolioService.get_portfolio(..., user=...)`.
- Tests present: `test_snapshots_api.py`
- Known gaps: No explicit cross-user API test. Snapshot response lacks source/data-status fields even though the payload stores a source.
- Frontend readiness: Ready, with contract cleanup recommended before advanced provenance UI.
- Recommended frontend page placement: Future `SnapshotsPage`; dashboard snapshot panel after dashboard/performance/risk surfaces stabilize.

### Fundamentals

- Feature name: Fundamentals
- Module path: `backend/app/modules/fundamentals`
- Router path: `backend/app/modules/fundamentals/router.py`
- Service path: `backend/app/modules/fundamentals/service.py`
- Schema path: `backend/app/modules/fundamentals/schemas.py`
- Endpoint(s):
  - `GET /api/assets/{symbol}/fundamentals`
  - `GET /api/portfolios/{portfolio_id}/fundamentals`
- Feature flag: `ENABLE_FUNDAMENTALS`
- Dependencies: `FundamentalsProvider` interface, `MockFundamentalsProvider`, `PortfolioService`, holdings, `DataStatus`
- Mock/demo dependency: Mock-only provider today. Mock fundamentals are blocked outside local/test/demo/development.
- DataStatus support: Yes. Asset and portfolio fundamentals include `DataStatus`, coverage, missing symbols, and warnings.
- Auth/ownership protection: Portfolio endpoint checks ownership. Single-asset endpoint is public-style symbol data and does not require portfolio ownership.
- Tests present: `test_fundamentals_api.py`, `test_fundamentals_service.py`
- Known gaps: No live fundamentals provider. No explicit cross-user test for portfolio fundamentals.
- Frontend readiness: Partial. Demo-ready with provider/coverage warnings.
- Recommended frontend page placement: Future `FundamentalsPage`; optional holding detail/research panel.

### Peers

- Feature name: Peers
- Module path: `backend/app/modules/peers`
- Router path: `backend/app/modules/peers/router.py`
- Service path: `backend/app/modules/peers/service.py`
- Schema path: `backend/app/modules/peers/schemas.py`
- Endpoint(s): `GET /api/portfolios/{portfolio_id}/peers/{symbol}`
- Feature flag: `ENABLE_PEERS`
- Dependencies: `PortfolioService`, `FundamentalsService`, `static_peer_map`
- Mock/demo dependency: Static India peer map plus mock fundamentals provider. Response warnings call out static/mock/sparse coverage.
- DataStatus support: Partial. Peer response does not have top-level `DataStatus`, but selected and peer companies are `FundamentalsResponse` objects with `data_status`.
- Auth/ownership protection: Yes. Service checks portfolio ownership before comparison.
- Tests present: `test_peers_api.py`
- Known gaps: Static/sparse peer map, no live fundamentals, no explicit cross-user test.
- Frontend readiness: Partial. Demo-ready for symbol research with static/mock labels.
- Recommended frontend page placement: Future `PeersPage` or symbol research panel linked from holdings/fundamentals.

### Advisor Context

- Feature name: Advisor context
- Module path: `backend/app/modules/ai_advisor`
- Router path: `backend/app/modules/ai_advisor/router.py`
- Service path: `backend/app/modules/ai_advisor/service.py`, `backend/app/modules/ai_advisor/context_builder.py`
- Schema path: `backend/app/modules/ai_advisor/schemas.py`
- Endpoint(s):
  - `POST /api/portfolios/{portfolio_id}/ai/summary`
  - `POST /api/portfolios/{portfolio_id}/ai/question`
  - `GET /api/portfolios/{portfolio_id}/ai/conversations`
  - `GET /api/ai/conversations/{conversation_id}`
- Feature flag: Advisor itself is not feature-gated. Optional context blocks depend on `ENABLE_DASHBOARD_BUNDLE`, `ENABLE_PERFORMANCE_HISTORY`, `ENABLE_RISK_V2`, `ENABLE_FUNDAMENTALS`, `ENABLE_PEERS`, and `ENABLE_SNAPSHOTS`.
- Dependencies: `PortfolioService`, `AnalyticsService`, optional `DashboardService`, `PerformanceService`, `RiskV2Service`, `FundamentalsService`, `PeerComparisonService`, `SnapshotService`
- Mock/demo dependency: AI response generation is deterministic/mock. OpenAI/Anthropic keys only change metadata to ready-mock modes.
- DataStatus support: Partial. Optional context can include nested `data_status` from performance/fundamentals; advisor response schema does not expose top-level `DataStatus`.
- Auth/ownership protection: Yes. Portfolio actions check ownership. Conversation detail checks the conversation owner.
- Tests present: `test_ai_advisor.py`, `test_ai_advisor_context.py`
- Known gaps: Real AI calls are not implemented. `_safe_optional_block` catches broad exceptions and can hide optional context failures during development.
- Frontend readiness: Partial. Existing advisor UI can continue; new optional context should be labeled as mock/synthetic/static where applicable.
- Recommended frontend page placement: Existing `AIAdvisorPage`; no new page required.

### Simulator

- Feature name: Simulator
- Module path: `backend/app/modules/simulator`
- Router path: `backend/app/modules/simulator/router.py`
- Service path: `backend/app/modules/simulator/service.py`
- Schema path: `backend/app/modules/simulator/schemas.py`
- Endpoint(s): `POST /api/portfolios/{portfolio_id}/simulate`
- Feature flag: `ENABLE_SIMULATOR`
- Dependencies: `PortfolioService`, current holdings/current prices
- Mock/demo dependency: None directly. Uses whatever current prices are stored on holdings.
- DataStatus support: No. Response includes warnings and `persisted=false`, but no structured data-status or assumptions object.
- Auth/ownership protection: Yes. Service checks portfolio ownership.
- Tests present: `test_simulator_api.py`
- Known gaps: No explicit cross-user test. Warnings are prose-only. No persistence by design.
- Frontend readiness: Partial. Usable as a hypothetical tool after shared target-weight controls and warning display exist.
- Recommended frontend page placement: Future `SimulatorPage`; may share controls with optimizer and rebalance.

### Optimizer

- Feature name: Optimizer
- Module path: `backend/app/modules/optimizer`
- Router path: `backend/app/modules/optimizer/router.py`
- Service path: `backend/app/modules/optimizer/service.py`
- Schema path: `backend/app/modules/optimizer/schemas.py`
- Endpoint(s): `POST /api/portfolios/{portfolio_id}/optimize`
- Feature flag: `ENABLE_OPTIMIZER`
- Dependencies: `PortfolioService`, holdings/current prices, `MarketHistoryService`, optimizer calculations, `DataStatus`
- Mock/demo dependency: Uses deterministic mock historical response. No heavy external optimizer dependency is used.
- DataStatus support: Yes. Response includes `data_status`, structured assumptions, status, and warnings.
- Auth/ownership protection: Yes. Service checks portfolio ownership.
- Tests present: `test_optimizer_api.py`
- Known gaps: No explicit cross-user test or direct service tests. Historical estimates are mock/synthetic and not investment advice.
- Frontend readiness: Partial. Demo-ready with assumptions, status, warnings, and mock/stale labels.
- Recommended frontend page placement: Future `OptimizerPage`; outputs can feed simulator/rebalance target weights later.

### Rebalance Tickets

- Feature name: Rebalance tickets
- Module path: `backend/app/modules/rebalance`
- Router path: `backend/app/modules/rebalance/router.py`
- Service path: `backend/app/modules/rebalance/service.py`
- Schema path: `backend/app/modules/rebalance/schemas.py`
- Endpoint(s): `POST /api/portfolios/{portfolio_id}/rebalance/tickets`
- Feature flag: `ENABLE_REBALANCE_TICKETS`
- Dependencies: `PortfolioService`, current holdings/current prices
- Mock/demo dependency: None directly. Uses current prices that may originate from a mock provider.
- DataStatus support: No. Response includes warnings but no `DataStatus` or structured assumptions.
- Auth/ownership protection: Yes. Service checks portfolio ownership.
- Tests present: `test_rebalance_tickets_api.py`
- Known gaps: No explicit cross-user test. No structured assumptions/disclaimer object. No persistence or execution by design.
- Frontend readiness: Partial. Usable as estimated, non-executing tickets after assumptions/warnings are made prominent.
- Recommended frontend page placement: Future `RebalancePage`, likely downstream of optimizer/simulator target weights.

### Watchlist

- Feature name: Watchlist
- Module path: `backend/app/modules/watchlist`
- Router path: `backend/app/modules/watchlist/router.py`
- Service path: `backend/app/modules/watchlist/service.py`
- Schema path: `backend/app/modules/watchlist/schemas.py`
- Endpoint(s):
  - `GET /api/watchlist`
  - `POST /api/watchlist`
  - `DELETE /api/watchlist/{watchlist_item_id}`
- Feature flag: None.
- Dependencies: `WatchlistItem` model, latest `AssetPrice` rows, symbol normalization
- Mock/demo dependency: Watchlist CRUD has none. Displayed latest prices can come from mock market data.
- DataStatus support: Partial. Response exposes `price_source` and `price_as_of`, but not full `DataStatus`.
- Auth/ownership protection: Yes. Items are scoped to `CurrentUser`.
- Tests present: `test_supporting_mvp_api.py`, plus market price tests in `test_market_data.py`
- Known gaps: Price refresh happens outside watchlist CRUD through market data endpoints; no full data-status object in response.
- Frontend readiness: Ready. Existing `WatchlistPage` already integrates this, though it owns an inline price query that should eventually move into a hook.
- Recommended frontend page placement: Existing `WatchlistPage`.

## Cross-Cutting Findings

### Feature Flags

Configured flags in `backend/app/core/feature_flags.py` and `backend/app/core/config.py`:
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

Known flag gap:
- `/api/market-data/history/{symbol}` remains ungated while the newer `/api/market/history` route is gated by `ENABLE_HISTORICAL_DATA`.

### DataStatus Coverage

Strong coverage:
- Market overview
- Dashboard bundle
- Market data prices/history
- Performance history
- Risk v2
- Fundamentals
- Optimizer

Partial or missing coverage:
- Uploads use warnings/statuses, not `DataStatus`.
- Sector metadata uses `sector_source`/`sector_updated_at`, not `DataStatus`.
- Snapshots do not expose `DataStatus` or `source` in response schemas.
- Peers relies on nested fundamentals `DataStatus`, no top-level status.
- Advisor has nested optional context statuses only.
- Simulator and rebalance use prose warnings only.
- Watchlist exposes price source/as-of but not full `DataStatus`.

### Auth And Ownership

Portfolio-scoped services consistently use `PortfolioService.get_portfolio(..., user=...)` either directly or through a dependency service:
- Dashboard
- Uploads
- Holdings/sector metadata
- Performance
- Risk v2 through performance
- Snapshots
- Portfolio fundamentals
- Peers
- Advisor portfolio actions
- Simulator
- Optimizer
- Rebalance tickets
- Portfolio price refresh

Public-style market/symbol endpoints:
- Market overview
- Market prices/history
- Asset fundamentals

Known auth caveat:
- Production auth remains demo-mode-gated placeholder auth until a real auth provider is implemented. Service ownership boundaries are expressed, but the current local user source is deterministic in demo/local mode.

### Modularity

Most features follow the intended modular-monolith shape:
- `router.py` is thin.
- `service.py` owns orchestration.
- `schemas.py` owns response/request contracts.
- shared market/provenance schema lives in `common/data_status.py`.

Notable coupling:
- `MarketHistoryService` imports deterministic history generation from `app.modules.demo.fixtures.historical_prices`.
- `AIAdvisorContextBuilder` intentionally reads many feature services for optional context; it should remain one-way.

## Recommended Frontend Integration Order

1. Shared frontend foundation: `DataStatus`, API error/feature-disabled helper, updated backend-aligned types.
2. Shared UI primitives: `DataStatusBadge`, `FeatureDisabledState`, `PageHeader`, `MetricCard`, action-capable empty/error states.
3. Dashboard bundle: integrate `GET /api/portfolios/{portfolio_id}/dashboard`.
4. Upload mapping suggestions: extend existing upload wizard.
5. Performance history and risk v2 type/service/hook foundations, with no UI claims beyond demo/synthetic assumptions.
6. Fundamentals and peers research views with coverage/static/mock warnings.
7. Simulator, optimizer, rebalance tickets after shared target-weight controls exist.
8. Market overview and header market status after route metadata and data-status display are in place.
9. Snapshots once dashboard/performance/risk pages have clear navigation anchors.

## Recommended Follow-Up Backend Work

1. Move mock historical price generation out of `backend/app/modules/demo/fixtures` into an explicit mock market-history provider namespace.
2. Decide whether to deprecate, feature-gate, or fold `/api/market-data/history/{symbol}` into `/api/market/history`.
3. Add structured assumptions/disclaimer fields to simulator and rebalance responses.
4. Add explicit cross-user API tests for snapshots, risk v2, portfolio fundamentals, peers, simulator, optimizer, and rebalance.
5. Add direct service tests for simulator, optimizer, rebalance, snapshots, peers, and risk v2.
6. Add snapshot `source` or `DataStatus` to snapshot response schemas if the frontend needs provenance.
7. Implement live historical market data before representing performance/risk/optimizer as production analytics.
8. Implement live fundamentals before representing fundamentals/peers as production investment research.
