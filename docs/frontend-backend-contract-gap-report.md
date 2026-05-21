# Frontend Backend Contract Gap Report

Date: 2026-05-22

Scope: documentation-only contract audit. This report verifies whether frontend TypeScript types, service wrappers, and hooks can be created from backend Pydantic/FastAPI contracts without guessing response shapes.

Sources inspected:
- `backend/app/main.py`
- `backend/app/modules/*/router.py`
- `backend/app/modules/*/schemas.py`
- `backend/app/modules/common/data_status.py`
- `frontend/src/services/*`
- `frontend/src/hooks/*`
- `frontend/src/types/*`
- `docs/backend-feature-registry.md`
- `docs/frontend-page-feature-map.md`

## Executive summary

The backend exposes enough Pydantic response contracts to create frontend types and service wrappers safely for all new backend feature modules. The blocker is not missing backend schemas; it is frontend drift and missing wrappers for the newer modules.

Current frontend API coverage is strongest for core portfolio, holdings, upload, legacy analytics, watchlist, advisor, demo, broker placeholder, billing placeholder, and legacy market-data prices/history. Coverage is missing for market overview, dashboard bundle, new historical market data, performance history, risk v2, snapshots, fundamentals, peers, simulator, optimizer, and rebalance tickets.

Frontend types are manually maintained. There is no current OpenAPI-generated TypeScript client, no `openapi-typescript` or Orval config, no checked-in `openapi.json`, and no package script for client generation. FastAPI exposes OpenAPI at runtime, but the repo currently depends on manual schema alignment.

No wrapper implementation is required before creating this report. No type-only addition is required because the backend contracts are already explicit enough to prove the gaps.

## Backend endpoint to frontend service coverage

| Backend endpoint | Backend response model | Current frontend wrapper | Coverage status | Contract-safe next frontend file |
|---|---|---|---|---|
| `GET /api/health` | `dict[str, str]` | None | Backend health/check endpoint; not a product wrapper gap | None unless diagnostics need it |
| `GET /api/status` | `AppStatusResponse` | `statusApi.getAppStatus` | Wrapped, type drift | Update `frontend/src/types/appStatus.ts` |
| `POST /api/portfolios` | `PortfolioResponse` | `portfolioApi.createPortfolio` | Covered | Existing |
| `GET /api/portfolios` | `list[PortfolioResponse]` | `portfolioApi.listPortfolios` | Covered | Existing |
| `GET /api/portfolios/{portfolio_id}` | `PortfolioResponse` | `portfolioApi.getPortfolio` | Covered | Existing |
| `PATCH /api/portfolios/{portfolio_id}` | `PortfolioResponse` | `portfolioApi.updatePortfolio` | Covered | Existing |
| `DELETE /api/portfolios/{portfolio_id}` | 204 | `portfolioApi.deletePortfolio` | Covered | Existing |
| `GET /api/portfolios/{portfolio_id}/holdings` | `list[HoldingResponse]` | `holdingsApi.listHoldings` | Wrapped, type drift | Update `frontend/src/types/holdings.ts` |
| `POST /api/portfolios/{portfolio_id}/holdings` | `HoldingResponse` | `holdingsApi.createHolding` | Wrapped, type drift | Update `frontend/src/types/holdings.ts` |
| `PATCH /api/portfolios/{portfolio_id}/holdings/{holding_id}` | `HoldingResponse` | `holdingsApi.updateHolding` | Wrapped, type drift | Update `frontend/src/types/holdings.ts` |
| `DELETE /api/portfolios/{portfolio_id}/holdings/{holding_id}` | 204 | `holdingsApi.deleteHolding` | Covered | Existing |
| `GET /api/market-data/prices` | `BatchPriceResponse` | `marketDataApi.getBatchPrices` | Wrapped, types live in service and miss `data_status` | Move/update types in `frontend/src/types/marketData.ts` |
| `GET /api/market-data/prices/{symbol}` | `PriceQuote` | `marketDataApi.getPrice` | Wrapped, types live in service and miss `data_status` | Move/update types in `frontend/src/types/marketData.ts` |
| `GET /api/market-data/history/{symbol}` | `PriceHistoryResponse` | `marketDataApi.getPriceHistory` | Covered for legacy endpoint; type misses optional point `data_status` | Move/update types in `frontend/src/types/marketData.ts` |
| `GET /api/market/history` | `HistoricalPriceResponse` | None | Missing wrapper | `marketHistoryApi.ts`, `useMarketHistory` |
| `POST /api/portfolios/{portfolio_id}/prices/refresh` | `PortfolioPriceRefreshResponse` | `marketDataApi.refreshPortfolioPrices` | Wrapped, types live in service and miss `data_status` | Move/update types in `frontend/src/types/marketData.ts` |
| `GET /api/market/overview` | `MarketOverviewResponse` | None | Missing wrapper | `marketOverviewApi.ts`, `useMarketOverview` |
| `GET /api/portfolios/{portfolio_id}/dashboard` | `DashboardBundleResponse` | None | Missing wrapper | `dashboardApi.ts`, `useDashboardBundle` |
| `GET /api/portfolios/{portfolio_id}/analytics/summary` | `PortfolioAnalyticsSummary` | `analyticsApi.getSummary` | Covered | Existing |
| `GET /api/portfolios/{portfolio_id}/analytics/allocation` | `AllocationAnalytics` | `analyticsApi.getAllocation` | Covered | Existing |
| `GET /api/portfolios/{portfolio_id}/analytics/risk` | `RiskAnalytics` | `analyticsApi.getRisk` | Covered legacy analytics | Existing |
| `GET /api/portfolios/{portfolio_id}/analytics/performance` | `PerformanceAnalytics` | `analyticsApi.getPerformance` | Covered legacy analytics | Existing |
| `GET /api/portfolios/{portfolio_id}/analytics/rules` | `list[RuleInsight]` | `analyticsApi.getRules` | Covered | Existing |
| `POST /api/portfolios/{portfolio_id}/analytics/recalculate` | `AnalyticsRecalculateResponse` | `analyticsApi.recalculateAnalytics` | Covered | Existing |
| `GET /api/portfolios/{portfolio_id}/performance/history` | `PortfolioPerformanceHistory` | None | Missing wrapper | `performanceApi.ts`, `usePerformanceHistory` |
| `GET /api/portfolios/{portfolio_id}/risk` | `RiskV2Response` | None | Missing wrapper; do not confuse with legacy analytics risk | `riskApi.ts`, `useRiskV2` |
| `POST /api/portfolios/{portfolio_id}/snapshots` | `SnapshotResponse` | None | Missing wrapper | `snapshotsApi.ts`, `useSnapshots` |
| `GET /api/portfolios/{portfolio_id}/snapshots` | `list[SnapshotSummary]` | None | Missing wrapper | `snapshotsApi.ts`, `useSnapshots` |
| `GET /api/portfolios/{portfolio_id}/snapshots/compare` | `SnapshotCompareResponse` | None | Missing wrapper | `snapshotsApi.ts`, `useSnapshots` |
| `GET /api/assets/{symbol}/fundamentals` | `FundamentalsResponse` | None | Missing wrapper | `fundamentalsApi.ts`, `useAssetFundamentals` |
| `GET /api/portfolios/{portfolio_id}/fundamentals` | `PortfolioFundamentalsResponse` | None | Missing wrapper | `fundamentalsApi.ts`, `usePortfolioFundamentals` |
| `GET /api/portfolios/{portfolio_id}/peers/{symbol}` | `PeerComparisonResponse` | None | Missing wrapper | `peersApi.ts`, `usePeerComparison` |
| `POST /api/portfolios/{portfolio_id}/simulate` | `SimulationResponse` | None | Missing wrapper | `simulatorApi.ts`, `usePortfolioSimulation` |
| `POST /api/portfolios/{portfolio_id}/optimize` | `OptimizerResponse` | None | Missing wrapper | `optimizerApi.ts`, `useOptimizer` |
| `POST /api/portfolios/{portfolio_id}/rebalance/tickets` | `RebalanceTicketsResponse` | None | Missing wrapper | `rebalanceApi.ts`, `useRebalanceTickets` |
| `POST /api/portfolios/{portfolio_id}/uploads` | `UploadJobResponse` | `uploadApi.createUploadJob` | Covered | Existing |
| `GET /api/uploads/{upload_job_id}` | `UploadJobResponse` | `uploadApi.getUploadJob` | Covered | Existing |
| `POST /api/uploads/{upload_job_id}/column-mapping` | `ColumnMappingResponse` | `uploadApi.submitColumnMapping` | Covered | Existing |
| `GET /api/uploads/{upload_job_id}/mapping-suggestions` | `ColumnMappingSuggestionsResponse` | None | Missing wrapper | Extend `uploadApi.ts`, `useUpload` |
| `POST /api/uploads/{upload_job_id}/validate` | `ValidateUploadResponse` | `uploadApi.validateUpload` | Wrapped, type drift on row warnings | Update upload types |
| `POST /api/uploads/{upload_job_id}/confirm` | `ConfirmUploadResponse` | `uploadApi.confirmUpload` | Wrapped, type drift | Update upload types |
| `GET /api/uploads/{upload_job_id}/errors` | `UploadErrorsResponse` | `uploadApi.getUploadErrors` | Wrapped, type drift on row warnings | Update upload types |
| `POST /api/portfolios/{portfolio_id}/ai/summary` | `AIAdvisorResponse` | `aiApi.generatePortfolioSummary` | Covered | Existing |
| `POST /api/portfolios/{portfolio_id}/ai/question` | `AIAdvisorResponse` | `aiApi.askPortfolioQuestion` | Covered | Existing |
| `GET /api/portfolios/{portfolio_id}/ai/conversations` | `list[AIConversationListItem]` | `aiApi.listConversations` | Covered | Existing |
| `GET /api/ai/conversations/{conversation_id}` | `AIConversationDetail` | `aiApi.getConversation` | Covered | Existing |
| `GET /api/watchlist` | `list[WatchlistItemResponse]` | `watchlistApi.listWatchlist` | Covered | Existing |
| `POST /api/watchlist` | `WatchlistItemResponse` | `watchlistApi.createWatchlistItem` | Covered | Existing |
| `DELETE /api/watchlist/{watchlist_item_id}` | 204 | `watchlistApi.deleteWatchlistItem` | Covered | Existing |
| `GET /api/broker-connections` | `list[BrokerConnectionResponse]` | `brokerConnectionsApi.listBrokerConnections` | Covered | Existing |
| `GET /api/broker-connections/providers` | `list[BrokerProviderPlaceholder]` | `brokerConnectionsApi.listBrokerProviders` | Covered | Existing |
| `POST /api/broker-connections/connect-placeholder` | `BrokerConnectionResponse` | `brokerConnectionsApi.createBrokerPlaceholder` | Covered | Existing |
| `DELETE /api/broker-connections/{connection_id}` | 204 | `brokerConnectionsApi.deleteBrokerConnection` | Covered | Existing |
| `GET /api/billing/plan` | `BillingPlanResponse` | `billingApi.getPlan` | Covered | Existing |
| `POST /api/billing/create-checkout-session` | `CheckoutSessionResponse` | `billingApi.createCheckoutSession` | Covered | Existing |
| `POST /api/billing/webhook` | `BillingWebhookResponse` | None | Backend-only webhook; not a frontend wrapper gap | None |
| `POST /api/demo/seed` | `DemoSeedResponse` | `demoApi.seedDemoPortfolio` | Covered | Existing |

## Backend schema to frontend type coverage

| Backend schema area | Current frontend type status | Gap | Contract-safe recommendation |
|---|---|---|---|
| `DataStatus` | No shared frontend type | Missing everywhere new modules expose provenance | Add `frontend/src/types/dataStatus.ts` before integrating any new DataStatus-bearing endpoint. |
| `AppStatusResponse` | `AppStatus` exists | Missing `market_data_is_mock`, `ai_is_mock`, `production_safe`, `warnings` | Update `frontend/src/types/appStatus.ts` from backend response model. |
| Portfolio schemas | `Portfolio`, create/update types exist | No material drift found | Keep existing. |
| Holding schemas | `Holding` exists | Missing `sector_source`, `sector_updated_at`; computed fields are present and okay | Update `frontend/src/types/holdings.ts`. |
| Market data legacy schemas | Types live in `marketDataApi.ts` | Types are not in `frontend/src/types`; optional `data_status` fields missing | Move to `frontend/src/types/marketData.ts` and add `DataStatus | null` fields. |
| Market history schemas | None | Missing `HistoricalPeriod`, `HistoricalPricePoint`, `HistoricalPriceSeries`, `HistoricalPriceResponse` | Add market history types based on `history_schemas.py`. |
| Market overview schemas | None | Missing `MarketStatus`, `MarketIndexCard`, `SectorIndexCard`, `MarketMover`, `MarketOverviewResponse` | Add `frontend/src/types/marketOverview.ts`. |
| Dashboard schemas | None | Missing all dashboard bundle nested types | Add `frontend/src/types/dashboard.ts`. |
| Legacy analytics schemas | `analytics.ts` exists | Appears aligned with current legacy analytics contracts | Keep but distinguish from risk v2/performance history. |
| Performance history schemas | None | Missing assumptions, value series, normalized return series, response | Add `frontend/src/types/performance.ts`. |
| Risk v2 schemas | None | Missing `RiskMetricStatus`, `RiskV2Response`, and metric status map | Add `frontend/src/types/risk.ts`; do not reuse legacy `RiskAnalytics`. |
| Snapshot schemas | None | Missing create, response, summary, compare, holding/value/allocation change types | Add `frontend/src/types/snapshots.ts`. |
| Fundamentals schemas | None | Missing metric, coverage, asset, and portfolio fundamentals types | Add `frontend/src/types/fundamentals.ts`. |
| Peers schemas | None | Missing peer quality, comparison rows, peer response | Add `frontend/src/types/peers.ts`, importing fundamentals types. |
| Simulator schemas | None | Missing request/response allocation, concentration, distribution types | Add `frontend/src/types/simulator.ts`. |
| Optimizer schemas | None | Missing request, assumptions, metric set, optimized weights, frontier, response | Add `frontend/src/types/optimizer.ts`. |
| Rebalance schemas | None | Missing request, ticket, response types | Add `frontend/src/types/rebalance.ts`. |
| Upload schemas | `upload.ts` exists | Missing `ColumnMappingSuggestionsResponse`, `ColumnMappingSuggestion`, row `warnings`, `invalid_count`, `duplicate_count`, `rejected_row_reasons`; current `ConfirmUploadResponse` uses `invalid_rows` but backend also returns `invalid_count` | Update `frontend/src/types/upload.ts` before wiring suggestions or richer import summaries. |
| Advisor schemas | `ai.ts` exists | Backend `mode`, `role`, and context are loose strings/dicts; frontend narrows mode/role and shapes context | Current narrowing is usable for known UI, but generated/manual contract should reflect backend looser schema or backend should tighten schema later. |
| Watchlist schemas | `watchlist.ts` exists | `notes` naming aligns with backend; no material drift found | Keep existing. |
| Broker connection schemas | `brokerConnections.ts` exists | No material drift found | Keep existing. |
| Billing schemas | `billing.ts` exists | Frontend narrows plan ids more than backend `str`; usage is a generic backend `dict` but frontend assumes specific keys | Either keep as app-level expectation or tighten backend schema before generated-client work. |
| Demo schemas | `demo.ts` exists | No drift found | Keep existing. |

## Frontend page calculation audit

| Frontend location | Current calculation/orchestration | Keep in page? | Recommendation |
|---|---|---:|---|
| `DashboardPage` | Sorts and slices top holdings from analytics summary holdings | No, once dashboard bundle is used | Use backend `DashboardBundleResponse.top_holdings`. Page may only map rows to chart/table props. |
| `DashboardPage` | Derives latest price update from holding `updated_at` | Prefer backend/provider status | Use dashboard `data_quality.data_status` or price refresh `data_status` once integrated. |
| `DashboardPage` | Filters missing data rules from legacy analytics rules | Acceptable as temporary legacy composition | Replace with dashboard `data_quality` and `action_items` when bundle is adopted. |
| `DashboardPage` | Formats currency/percent/date and maps chart colors | Yes | Presentation-only logic is safe. |
| `HoldingsPage` | Derives sector filter options from holdings | Yes | This is view-model/filter UI logic. |
| `HoldingsPage` | Filters holdings by search and sector | Yes | This is local table UX, not backend analytics. |
| `HoldingsPage` | Derives latest price update from holding `updated_at` | Prefer backend/provider status | Use explicit price freshness/source fields when available; avoid treating holding update timestamp as provider freshness. |
| `HoldingsPage` | Computes unique sources after refresh result | Yes | Display grouping is acceptable; rely on backend data status for meaning. |
| `UploadPage` | Guesses column mapping from detected column names | No, when suggestions feature is enabled | Backend `ColumnMappingSuggestionsResponse` should own suggestions; local guess can remain only as fallback/manual helper. |
| `UploadPage` | Filters invalid rows from validation result | Yes | View filtering is acceptable. |
| `AnalyticsPage` | Composes charts/tables from backend legacy analytics | Yes | It renders backend-calculated analytics; do not add risk/performance calculations here. |
| `AnalyticsPage` | Builds performance chart data by merging top gainers/losers arrays | Yes | Presentation composition is acceptable. |
| `AIAdvisorPage` | Reads legacy analytics summary for context display | Acceptable temporary display | Advisor explanation context should remain backend-owned; frontend should not build new advisor analytics logic. |
| `WatchlistPage` | Builds symbol array and price lookup map | Yes | View-model mapping is acceptable. |
| `WatchlistPage` | Owns TanStack Query for batch prices directly in page | No | Move API read into `useBatchPrices` or `useWatchlistPrices`; pages should consume hooks only. |

Rule: formatting, filtering, display ordering, chart data mapping, and table row mapping can stay frontend-side. Portfolio metrics, risk/performance calculations, allocation/concentration analytics, advisor reasoning, and upload mapping suggestions should come from backend services.

## Backend/frontend naming mismatch table

| Area | Backend name | Current frontend name | Risk | Recommendation |
|---|---|---|---|---|
| Dashboard invested value | `DashboardKpis.total_invested` | Legacy analytics uses `total_cost_basis`; user copy may say invested value | Medium | New dashboard type should use `total_invested`; UI labels can say invested value. |
| Dashboard current value | `DashboardKpis.current_value` | Legacy analytics uses `total_portfolio_value` | Medium | Do not reuse legacy summary type for dashboard bundle. |
| Dashboard P&L | `DashboardKpis.unrealized_pnl`, `return_percent` | Legacy analytics uses `total_unrealized_gain_loss`, `total_unrealized_gain_loss_pct` | Medium | Keep separate dashboard and legacy analytics types. |
| Risk v2 | `RiskV2Response` at `/api/portfolios/{id}/risk` | `RiskAnalytics` at `/analytics/risk` | High | Create separate `risk.ts` and `riskApi.ts`; do not overload `analyticsApi.getRisk`. |
| New market history | `HistoricalPriceResponse.series[]` | Legacy `PriceHistoryResponse.prices[]` | High | Create separate market history type/service; do not retrofit legacy single-symbol type. |
| Upload confirm invalid counts | `invalid_count` and `invalid_rows` | Frontend only has `invalid_rows` | Medium | Add both fields and document which UI label uses which count. |
| Upload rejected rows | `rejected_row_reasons` | Missing | Medium | Add typed rejected-row reasons before import summary UI. |
| Upload row warnings | `UploadRowResponse.warnings` | Missing | Medium | Add row warnings before validation UI expansion. |
| Holdings sector provenance | `sector_source`, `sector_updated_at` | Missing from `Holding` | Medium | Add fields before sector metadata UI. |
| Market provenance | `data_status` | Missing from market frontend types | High | Add shared `DataStatus` before new market/dashboard/research integrations. |
| Watchlist notes | `WatchlistCreate.notes`, `WatchlistItemResponse.notes` | `WatchlistCreateInput.notes`, `WatchlistItem.notes` | Low | Names are aligned; this resolves older `note`/`notes` uncertainty in docs. |
| Billing plan ids | Backend `BillingPlanOption.id: str` | Frontend `PlanTier` union | Low now, medium for generated client | Either tighten backend literals or loosen frontend if plan ids become dynamic. |

## OpenAPI/client generation findings

Current state:
- No checked-in `openapi.json` was found.
- No `openapi-typescript`, Orval, Swagger client, or generated API client package is configured in `frontend/package.json`.
- No Makefile target or package script exists for OpenAPI/client generation.
- Frontend services use a hand-written `apiRequest<T>` wrapper and hand-written TypeScript types.
- FastAPI will expose OpenAPI at runtime, but the repo does not currently capture or consume it for frontend type generation.

Implications:
- New frontend types can be safely hand-written from backend `schemas.py`, but every manual type must be audited against the Pydantic model.
- Generated-client adoption would require a new documented workflow, including how to start/export the backend OpenAPI schema, where generated files live, and how generated output is reviewed.
- Until generation exists, the minimum safe checklist is: backend router response model, backend request model, matching `frontend/src/types/*` type, matching `frontend/src/services/*` wrapper, matching TanStack Query hook, and feature-disabled error handling where the backend flag can return `feature_disabled`.

## Recommended contract-safe implementation order

1. Add shared contract foundation: `DataStatus`, complete `AppStatus`, complete upload and holdings drift fields, and move market-data types out of `marketDataApi.ts`.
2. Add service/type/hook coverage for low-risk read paths: market overview and dashboard bundle.
3. Add upload mapping suggestions after upload type drift is fixed.
4. Add historical market data, performance history, and risk v2 as separate types/services from legacy analytics.
5. Add snapshots, fundamentals, and peers with mock/static/sparse warnings preserved in types.
6. Add simulator, optimizer, and rebalance types/services only after target-weight UI contracts are agreed.
7. Decide later whether to introduce OpenAPI generation or keep manual type audits as the source of truth.

## Verification results

Verification commands for this report task:

```bash
git diff -- frontend/src backend
cd frontend && npm run build
backend/.venv/bin/pytest backend/app/tests
```

Expected acceptance:
- Only `docs/frontend-backend-contract-gap-report.md` is created or edited for this task.
- No `frontend/src` implementation files are changed.
- No `backend` implementation files are changed.
- Frontend build passes.
- Backend tests pass.

This report distinguishes true frontend wrapper gaps from backend-only endpoints. `POST /api/billing/webhook` is intentionally backend-only and should not get a normal browser service wrapper. `GET /api/health` can stay backend diagnostics-only unless an admin diagnostics page later needs it.
