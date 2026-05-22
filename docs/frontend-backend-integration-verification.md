# Frontend-Backend Integration Verification

Date: 2026-05-22

Scope: verification only. No frontend features, backend features, UI redesign, or broad refactors were added during this pass.

## Command Results

| Check | Result | Notes |
| --- | --- | --- |
| Backend tests | Pass | `cd backend && ./.venv/bin/pytest` -> 193 passed in 10.28s. |
| Frontend build | Pass | `cd frontend && npm run build` completed. Vite emitted only the existing large chunk warning. |
| Route smoke test | Pass with notes | Opened all registered routes in Vite dev server. No 404 or runtime-error page rendered. Header title falls back to `P-insight` on several newer routes. |

## Feature Verification Matrix

| Feature | Backend endpoint | Frontend wrapper | Hook | Page | State/warning coverage | Result |
| --- | --- | --- | --- | --- | --- | --- |
| Market overview | `GET /api/market/overview` | `marketOverviewApi.ts` | `useMarketOverview` | `/market` | Loading, empty, error, disabled. Uses `DataStatusBadge` and status warnings. | Pass |
| Dashboard bundle | `GET /api/portfolios/{portfolio_id}/dashboard` | `dashboardApi.ts` | `useDashboardBundle` | `/dashboard` | Loading, empty, disabled fallback, unavailable fallback, data quality warnings, data status warning. | Pass |
| Upload suggestions | `GET /api/uploads/{upload_job_id}/mapping-suggestions` | `uploadApi.ts` | `useUpload`, `useUploadMappingSuggestions` | `/upload` | Loading, empty, error, feature-disabled copy, fallback local matches. | Pass with note |
| Performance history | `GET /api/portfolios/{portfolio_id}/performance/history?period=` | `performanceApi.ts` | `usePerformanceHistory` | `/analytics` | Loading, disabled, error, empty chart state, `DataStatusBadge`, assumptions notice. | Pass |
| Risk v2 | `GET /api/portfolios/{portfolio_id}/risk?period=` | `riskApi.ts` | `useRiskV2` | `/analytics` | Loading, disabled, error, metric status fallbacks, `DataStatusBadge`, assumptions notice. | Pass |
| Snapshots | `POST/GET /api/portfolios/{portfolio_id}/snapshots`; `GET /compare` | `snapshotsApi.ts` | `useSnapshots`, `useSnapshotComparison` | `/changes` | Loading, empty, error, disabled. Backend comparison values rendered without recomputation. | Pass |
| Fundamentals | `GET /api/assets/{symbol}/fundamentals`; `GET /api/portfolios/{portfolio_id}/fundamentals` | `fundamentalsApi.ts` | `useFundamentals`, `usePortfolioFundamentals`, `useAssetFundamentals` | `/fundamentals` | Loading, empty, error, disabled, coverage warnings, data status warnings. | Pass |
| Peers | `GET /api/portfolios/{portfolio_id}/peers/{symbol}` | `peersApi.ts` | `usePeerComparison` | `/peers` | Loading, empty, error, disabled, static/sparse/mock-data warnings. | Pass |
| Simulator | `POST /api/portfolios/{portfolio_id}/simulate` | `simulatorApi.ts` | `useSimulator` | `/simulate` | Loading, empty, error, disabled, warnings, no-trades/no-persistence disclaimer. | Pass |
| Optimizer | `POST /api/portfolios/{portfolio_id}/optimize` | `optimizerApi.ts` | `useOptimizer` | `/optimize` | Loading, empty, error, disabled, optimizer warnings, data status, not-advice disclaimer. | Pass |
| Rebalance tickets | `POST /api/portfolios/{portfolio_id}/rebalance/tickets` | `rebalanceApi.ts` | `useRebalanceTickets` | `/optimize` | Loading, empty, error, disabled, missing-price warnings, no-execution/no-broker/no-advice disclaimer. | Pass |

Note: upload suggestions use a custom inline feature-disabled state rather than the shared `FeatureDisabledState` component. It is functionally covered.

## Service Wrapper and Hook Coverage

Missing service wrappers: none for the integrated features listed above.

Missing hooks: none for the integrated features listed above.

Endpoint mismatches found: none for the integrated wrappers. Each wrapper path and method matches the corresponding FastAPI route.

Pages with direct `fetch` calls: none. Direct network access is centralized in `frontend/src/services/apiClient.ts`.

Pages using services without a dedicated hook: `WatchlistPage` calls `getBatchPrices` inside `useQuery`. This is outside the listed vertical-slice verification set, but it is the only notable pattern drift from hook-first page integration.

## Frontend Calculation Boundary

No frontend page appears to duplicate backend-owned analytics calculations such as portfolio KPIs, allocation analytics, risk metrics, performance metrics, fundamentals aggregation, peer ranking, snapshot comparisons, optimizer metrics, or rebalance cash/share estimates.

Client-side logic that is acceptable UI preparation:

| Page | Logic | Assessment |
| --- | --- | --- |
| `/analytics` | Merges backend normalized return series by date for chart rendering. | UI transformation only. |
| `/dashboard` | Legacy fallback sorts already-returned holdings and derives latest priced-holding update timestamp. | Display/fallback logic only. |
| `/simulate` | Builds editable target weights from holdings and normalizes UI inputs before backend simulation. | Input preparation only; backend still owns simulation output. |
| `/optimize` | Builds rebalance target-weight inputs from holdings/optimizer outputs and validates 100% before request. | Input preparation only; backend still owns tickets, shares, cash, and leftover cash. |
| `/upload` | Provides local column-name fallback suggestions if backend suggestions are disabled/unavailable. | Manual mapping aid only. |

Pages with too much logic risk: `/simulate`, `/optimize`, and `/upload` are the highest-risk pages if the workflows keep expanding. The current logic is not a blocker, but shared target-weight and mapping helpers would reduce future drift.

## Feature Disabled States

| Feature flag | Frontend behavior | Result |
| --- | --- | --- |
| `ENABLE_MARKET_OVERVIEW` | `/market` renders `FeatureDisabledState`. | Pass |
| `ENABLE_DASHBOARD_BUNDLE` | `/dashboard` renders `FeatureDisabledState` and falls back to legacy analytics dashboard. | Pass |
| `ENABLE_UPLOAD_SUGGESTIONS` | `/upload` renders inline disabled copy and keeps manual mapping available. | Pass |
| `ENABLE_PERFORMANCE_HISTORY` | `/analytics` performance section renders `FeatureDisabledState` and keeps legacy performance analytics visible. | Pass |
| `ENABLE_RISK_V2` | `/analytics` risk section renders `FeatureDisabledState` and keeps legacy concentration analytics visible. | Pass |
| `ENABLE_SNAPSHOTS` | `/changes` renders `FeatureDisabledState`. | Pass |
| `ENABLE_FUNDAMENTALS` | `/fundamentals` renders `FeatureDisabledState`. | Pass |
| `ENABLE_PEERS` | `/peers` renders `FeatureDisabledState`. | Pass |
| `ENABLE_SIMULATOR` | `/simulate` renders `FeatureDisabledState`. | Pass |
| `ENABLE_OPTIMIZER` | `/optimize` optimizer section renders `FeatureDisabledState`. | Pass |
| `ENABLE_REBALANCE_TICKETS` | `/optimize` rebalance section renders `FeatureDisabledState`. | Pass |

## Mock, Stale, and Demo Warnings

Pass overall.

Coverage observed:

- Shared `DataStatusBadge` displays mock/stale/unavailable status and carries backend warning text.
- `/market`, `/dashboard`, `/analytics`, `/fundamentals`, `/peers`, `/advisor`, `/holdings`, and `/watchlist` expose data status, mock source badges, warnings, or demo banners where those pages consume such fields.
- `/simulate`, `/optimize`, and rebalance tickets display backend warnings and explicit hypothetical/no-execution disclaimers.
- App-level `DemoDataBanner` currently appears only on `/market`, `/dashboard`, `/holdings`, `/analytics`, `/advisor`, and `/watchlist`.

Non-blocking gap: newer analysis routes such as `/fundamentals`, `/peers`, `/simulate`, `/optimize`, and `/changes` are not included in the app-level demo banner path allowlist. Most of these pages show backend `data_status` or warning text locally, but the global mock-provider banner is inconsistent.

## Secrets Check

Pass.

No frontend secrets were found. The frontend only references public Vite configuration names and empty placeholders in `frontend/.env.example` / `frontend/README.md`, including `VITE_API_BASE_URL`, public auth/analytics placeholders, and `VITE_BETA_FEEDBACK_URL`. Backend-only keys are not present in frontend source.

## Route Navigation

Pass with non-blocking navigation polish issue.

Registered routes smoke-tested:

`/`, `/onboarding`, `/market`, `/dashboard`, `/changes`, `/holdings`, `/upload`, `/analytics`, `/fundamentals`, `/peers`, `/advisor`, `/simulate`, `/optimize`, `/watchlist`, `/brokers`, `/billing`, `/settings`, `/admin`, `/login`, `/signup`.

All rendered a root and main content area, and none rendered a 404 or runtime-error page.

Observed issue: `Header` title mapping is missing `/changes`, `/fundamentals`, `/peers`, `/simulate`, and `/optimize`, so those routes render the header title as `P-insight` even though the pages themselves render correctly.

## Type Contract Review

No blocking frontend/backend type mismatches were found for request/response fields used by the integrated pages.

Permissive frontend types to tighten later:

- `RiskMetricStatusCode` includes `partial_data` and `missing_benchmark`, while the backend currently returns only `ok`, `insufficient_history`, and `undefined`.
- `SnapshotComparisonResponse.concentration_changes` is typed as nullable in the frontend, while the backend schema returns a non-null `ConcentrationChange`.

These are not runtime blockers because they are more permissive than the backend contract.

## Manual QA Blockers

- Full authenticated end-to-end API flows were not exercised in the browser because this pass did not start and seed the backend application with all feature flags enabled.
- Feature-disabled UI states were verified from page code and backend tests, not by toggling each flag in a running browser session.
- Upload file parsing, confirm import, and mapping suggestions were not manually exercised with a real CSV in this verification pass.
- Rebalance ticket generation was not manually exercised against a live backend portfolio in this verification pass.

## Recommended Fixes

1. Add missing header titles for `/changes`, `/fundamentals`, `/peers`, `/simulate`, and `/optimize`.
2. Add newer analysis routes to the app-level demo-data banner allowlist, or document why per-page `data_status` warnings are sufficient.
3. Replace the custom upload-suggestions disabled panel with shared `FeatureDisabledState` styling if visual consistency matters.
4. Tighten permissive frontend types for `RiskMetricStatusCode` and `SnapshotComparisonResponse.concentration_changes`.
5. Extract shared target-weight input helpers from `/simulate` and `/optimize` if more target-weight workflows are added.
6. Consider a dedicated `useBatchPrices` hook for `WatchlistPage` to keep hook/service layering consistent outside the verified vertical set.
