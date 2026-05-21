# Frontend Integration Architecture Plan

Date: 2026-05-21

Scope: audit of the current frontend only, with a plan for integrating the new backend modules. This document intentionally does not implement UI, redesign pages, or change backend behavior.

## Build Verification

Command run from `frontend/`:

```bash
npm run build
```

Result: passed.

Notes:
- TypeScript and Vite production build completed successfully.
- Vite reported a chunk-size warning: the generated JS asset is about 835 kB before gzip and exceeds the 500 kB warning threshold. This is not a failing build, but new analytics, charts, and module pages should be added with route-level or component-level code splitting before the bundle grows further.

## Current Frontend Architecture Summary

The frontend is a Vite/React app using React Router, TanStack Query, Tailwind, Recharts, React Hook Form, Zod, and Lucide icons.

Important files inspected:
- `frontend/src/app/routes.tsx`
- `frontend/src/pages/*`
- `frontend/src/components/*`
- `frontend/src/components/layout/*`
- `frontend/src/services/*`
- `frontend/src/hooks/*`
- `frontend/src/types/*`
- `frontend/src/styles.css`
- `frontend/tailwind.config.js`

Current routing is flat under `AppLayout`. Core pages are `DashboardPage`, `HoldingsPage`, `UploadPage`, `AnalyticsPage`, `AIAdvisorPage`, `WatchlistPage`, plus placeholder/admin/settings/billing/broker/auth pages. No route exists yet for market overview, performance history, risk v2, snapshots, fundamentals, peers, simulator, optimizer, or rebalance tickets.

API calls are mostly centralized under `frontend/src/services`. Pages normally consume data through hooks under `frontend/src/hooks`, and those hooks use TanStack Query for caching and mutation invalidation. The main exception is `WatchlistPage`, which imports `getBatchPrices` directly from `services/marketDataApi` and owns a query inline.

Types are manually maintained in `frontend/src/types`, except market data response types, which currently live inside `frontend/src/services/marketDataApi.ts`. Backend response schemas are not generated into the frontend, so alignment depends on manual updates.

Layout is centralized in:
- `AppLayout`: shell, sidebar/header composition, fixed max-width main area, demo data banner on a hard-coded path set.
- `Sidebar`: static nav array and no feature-flag awareness.
- `Header`: static path-to-title map, search field, feedback link, login/signup actions.

Reusable UI is intentionally small:
- `Badge`
- `Button`
- `Card`, `CardHeader`, `CardTitle`
- `DemoDataBanner`
- `Input`
- `LoadingState`, `EmptyState`, `ErrorState`
- `Table`, `Th`, `Td`

## Architecture Findings

### API and Hook Layer

Strengths:
- `apiRequest<T>` centralizes base URL handling, JSON/FormData serialization, error wrapping, and 204 behavior.
- Most modules have a service file and hook file pairing.
- Mutations usually invalidate relevant query keys.
- Query defaults are configured centrally in `frontend/src/app/providers.tsx`.

Risks:
- Backend feature-disabled responses use `error_code = "feature_disabled"` with 404 status, but the frontend has no shared feature-disabled state or type guard yet.
- No shared `DataStatus` frontend type exists, even though new backend modules consistently return `data_status` with `source`, `provider`, `is_mock`, `is_realtime`, `as_of`, `is_stale`, and `warning`.
- Query keys are ad hoc string arrays. Existing modules use slightly different names and invalidation scopes, which will become error-prone as portfolio-scoped modules expand.
- `WatchlistPage` owns a price query directly. Future integrations should move all API reads into hooks so pages remain composition-only.
- `apiRequest` assumes every non-204 response is JSON. That is fine for current APIs but should be revisited if exports/downloads are added.

### Page Composition

Pages likely to become too large:
- `AnalyticsPage`: 563 lines. It owns tabs, charts, tables, metric cards, risk cards, rule cards, formatting helpers, and all empty/error branching.
- `DashboardPage`: 524 lines. It duplicates metric cards, allocation charts, insight rows, formatting helpers, and price-source warnings.
- `HoldingsPage`: 516 lines. It owns filters, form schema, form component, table, formatting helpers, confirmation behavior, and price refresh UI.
- `AIAdvisorPage`: 505 lines. It owns portfolio selection, analytics context, conversation state, chat rendering, history, suggested questions, and provider warning logic.
- `UploadPage`: 495 lines. It owns the full wizard, mapping guess logic, preview tables, validation summary, and import success flow.

Recommended extraction before adding new backend features:
- Shared `PageHeader`
- Shared `MetricCard`
- Shared `DataStatusBadge`
- Shared `SectionCard`/`ChartCard`
- Shared `AllocationChart`
- Shared `HoldingsTable`
- Shared formatter utilities for currency, percent, number, and date-time
- Portfolio selector hook/component
- Feature-disabled state component and API error helper
- Upload mapping components before adding backend mapping suggestions

### Analytics Calculations

The frontend mostly renders backend-calculated analytics rather than recalculating core metrics. However, it still performs presentation-time derived logic:
- `DashboardPage` sorts and slices top holdings from `summary.holdings`.
- `DashboardPage` derives latest price update from holding `updated_at`.
- `HoldingsPage` derives latest price update from holding `updated_at`.
- `HoldingsPage` filters holdings and derives sector options.
- `DashboardPage`, `AnalyticsPage`, and `AIAdvisorPage` duplicate currency/percent/date formatting.

These are acceptable view-model calculations, but anything business-critical should come from backend modules. New modules should prefer backend-provided dashboard bundles, performance history, risk v2, and action items instead of deriving equivalent analytics in page components.

### Type Alignment With Backend Schemas

Aligned:
- Existing analytics types match `backend/app/modules/analytics/schemas.py`.
- Portfolio and holding types appear aligned with current basic response shapes.

Misaligned or incomplete:
- `frontend/src/types/appStatus.ts` omits backend `/api/status` fields: `market_data_is_mock`, `ai_is_mock`, `production_safe`, and `warnings`.
- `frontend/src/types/upload.ts` omits `UploadRow.warnings`.
- `frontend/src/types/upload.ts` `ConfirmUploadResponse` omits `invalid_count`, `duplicate_count`, and `rejected_row_reasons`.
- Market data response types live inside `frontend/src/services/marketDataApi.ts` instead of `frontend/src/types/marketData.ts`.
- No frontend `DataStatus` type exists for new module schemas.
- No frontend types exist for market overview, dashboard bundle, upload mapping suggestions, performance history, risk v2, snapshots, fundamentals, peers, simulator, optimizer, or rebalance tickets.

Recommended rule: every new backend response schema should have a matching frontend type in `frontend/src/types`, and service files should import those types rather than define them inline.

## Layout Findings

### AppLayout

Current behavior:
- Uses a sidebar plus sticky header shell.
- Main content is constrained to `max-w-7xl` with responsive padding.
- Shows `DemoDataBanner` only on a hard-coded path set: `/dashboard`, `/holdings`, `/analytics`, `/advisor`, `/watchlist`.

Readiness:
- Good enough for current dashboard and analytics pages.
- Not yet flexible enough for a market overview page that may need full-width index/mover grids or dense tables.
- Not yet flexible enough for research-heavy pages where tables and charts may need wider layouts.
- Demo/mock warnings need to be data-driven from `DataStatus`, not path-driven from app status only.

Recommended changes later:
- Add route metadata for title, nav visibility, feature flag, and layout width.
- Let pages request `standard`, `wide`, or `full` content width.
- Move mock/stale warning rendering into reusable page-level components fed by response `data_status`.

### Sidebar

Current behavior:
- Static nav list in `Sidebar.tsx`.
- No feature flag or module grouping support.
- Hidden on smaller screens, but the mobile menu button in `Header` does not open a mobile nav.

Readiness:
- Not ready for feature-flagged modules. Adding all planned modules directly would create a long static nav and expose disabled routes.

Recommended changes later:
- Replace static nav with route/module config.
- Add feature flag status once the backend exposes flags to the frontend, or use optimistic hidden-by-default module config until enabled.
- Group modules, for example: Portfolio, Research, Tools, Admin.
- Implement the existing mobile menu button before adding many more nav entries.

### Header/Topbar

Current behavior:
- Static title lookup by path.
- Search input is present but not wired.
- Shows feedback link, login, signup.

Readiness:
- Not ready to show selected portfolio, data source, or market status.
- Portfolio selection is duplicated inside pages.
- Market/mock status only appears as a separate banner in `AppLayout`.

Recommended changes later:
- Add a selected portfolio control or summary once portfolio context is centralized.
- Add market status from `/api/market/overview` when enabled.
- Add compact data status display using `DataStatusBadge`.
- Add route metadata title handling to avoid updating `Header` for every new route.

## New Backend Integration Readiness

Shared assumptions:
- Feature-disabled backend responses currently return 404 with `error_code: "feature_disabled"`. Pages should show `FeatureDisabledState`, not a generic error, when this happens.
- Every response with `data_status` should render mock/stale/unavailable warnings via `DataStatusBadge` or a page-level warning row.
- Initial pages should use existing visual language only. Do not redesign until the shared component library is in place.

### Feature Integration Map

| Backend feature | Backend endpoint(s) | Service file | Hook file | Page/component target | Loading state | Empty state | Error state | Mock/stale warning | Manual QA |
|---|---|---|---|---|---|---|---|---|---|
| Market overview | `GET /api/market/overview` | Create `frontend/src/services/marketOverviewApi.ts` | Create `frontend/src/hooks/useMarketOverview.ts` | Create `MarketOverviewPage` later; add route `/market`; optionally header compact status | `LoadingState` while overview loads | No index/mover rows: `EmptyState` per section | Generic `ErrorState`; `FeatureDisabledState` on feature-disabled 404 | Use top-level `data_status`, `market_status.data_status`, and per-row `data_status` with `DataStatusBadge` | Enable flag, load page, verify market state, indices, sector indices, gainers/losers; disable flag and verify disabled state; force mock provider and verify warning |
| Dashboard bundle | `GET /api/portfolios/{portfolio_id}/dashboard` | Create `frontend/src/services/dashboardApi.ts` | Create `frontend/src/hooks/useDashboardBundle.ts` | Edit `DashboardPage` later to consume bundle; extract dashboard cards first | Page-level loading for selected portfolio and bundle | Empty portfolio when `kpis.holdings_count === 0` or no top holdings | `ErrorState`; disabled state on feature flag | Use bundle `data_status` plus `data_quality.data_status`; show stale price warnings | Compare current dashboard with bundle data; empty portfolio; missing price/cost warnings; disabled flag; mock provider warning |
| Upload mapping suggestions | `GET /api/uploads/{upload_job_id}/mapping-suggestions` | Edit `frontend/src/services/uploadApi.ts` | Edit `frontend/src/hooks/useUpload.ts` | Edit `UploadPage` mapping step later; extract mapping form first | Inline loading in mapping card | No suggestions: keep manual mapping | Inline `ErrorState`; disabled state if flag off | Not data-status based; show suggestions as advisory if mock/stale not relevant | Upload CSV, verify suggestions appear, can apply or ignore, required fields still enforced, disabled flag leaves manual mapping intact |
| Performance history | `GET /api/portfolios/{portfolio_id}/performance/history?period=1Y` | Create `frontend/src/services/performanceApi.ts` | Create `frontend/src/hooks/usePerformanceHistory.ts` | Create `PerformancePage` or `AnalyticsPerformancePanel`; replace dashboard placeholder later | Chart skeleton/loading card | No series or insufficient points: `EmptyState` with assumption text | `ErrorState`; disabled state | Use `data_status` and assumptions warning; show missing symbols | Try periods, verify portfolio and benchmark series, missing price symbols, synthetic-current-holdings assumptions, mock/stale badges |
| Risk v2 | `GET /api/portfolios/{portfolio_id}/risk?period=1Y` | Create `frontend/src/services/riskApi.ts` | Create `frontend/src/hooks/useRiskV2.ts` | Create `RiskPage` or replace `AnalyticsPage` risk tab later | Metric-card loading grid | `observations === 0` or all statuses insufficient: empty/insufficient state | `ErrorState`; disabled state | Use `data_status`; show assumptions | Verify metric statuses, null metrics render as N/A, correlation matrix responsive table, period changes, disabled flag |
| Snapshots | `POST /api/portfolios/{portfolio_id}/snapshots`, `GET /api/portfolios/{portfolio_id}/snapshots`, `GET /api/portfolios/{portfolio_id}/snapshots/compare?from_id=&to_id=` | Create `frontend/src/services/snapshotsApi.ts` | Create `frontend/src/hooks/useSnapshots.ts` | Create `SnapshotsPage` or dashboard snapshot panel later | List loading; create mutation pending; compare loading | No snapshots: create-first empty state; fewer than two snapshots: comparison empty state | `ErrorState`; disabled state | Snapshot schema has no `data_status`; warnings should come from snapshot values if backend adds status later | Create labeled snapshot, list order, compare two snapshots, verify added/removed/quantity/value/allocation changes, disabled flag |
| Fundamentals | `GET /api/assets/{symbol}/fundamentals`, `GET /api/portfolios/{portfolio_id}/fundamentals` | Create `frontend/src/services/fundamentalsApi.ts` | Create `frontend/src/hooks/useFundamentals.ts` | Create `FundamentalsPage` and holding detail panel later | Loading metric table/card | No holdings or no covered symbols: `EmptyState` | `ErrorState`; disabled state | Use response `data_status`; show coverage/missing symbols/warnings | Verify portfolio weighted metrics, missing symbols, individual symbol lookup, mock provider warning, coverage percentages |
| Peers | `GET /api/portfolios/{portfolio_id}/peers/{symbol}` | Create `frontend/src/services/peersApi.ts` | Create `frontend/src/hooks/usePeerComparison.ts` | Create `PeersPage` or symbol research panel later | Loading comparison table | No peers/sparse peers: `EmptyState` or sparse warning | `ErrorState`; disabled state | Use selected/peer company `data_status`; show peer set quality warnings | Select symbol, compare peers, verify rankings/null metrics, sparse peer set, disabled flag |
| Simulator | `POST /api/portfolios/{portfolio_id}/simulate` | Create `frontend/src/services/simulatorApi.ts` | Create `frontend/src/hooks/useSimulator.ts` | Create `SimulatorPage` later; reuse allocation editing components | Mutation pending state on simulate action | No holdings/targets: empty setup state | `ErrorState`; disabled state | No `data_status`; show backend warnings and persisted=false advisory | Submit target weights, added/removed symbols, invalid weights, verify concentration change and warnings, disabled flag |
| Optimizer | `POST /api/portfolios/{portfolio_id}/optimize` | Create `frontend/src/services/optimizerApi.ts` | Create `frontend/src/hooks/useOptimizer.ts` | Create `OptimizerPage` later; optionally feed simulator/rebalance targets | Mutation loading and frontier chart loading | Status `insufficient_history` or `unsupported`: `EmptyState`/status state | `ErrorState`; disabled state | Use `data_status`, assumptions, warnings | Run optimizer, verify min-variance/max-Sharpe/frontier points, insufficient-history handling, period/frontier inputs, mock/stale badge |
| Rebalance tickets | `POST /api/portfolios/{portfolio_id}/rebalance/tickets` | Create `frontend/src/services/rebalanceApi.ts` | Create `frontend/src/hooks/useRebalanceTickets.ts` | Create `RebalancePage` later; likely downstream of optimizer/simulator | Mutation pending state | No tickets or no execution required: hold/no-trade empty state | `ErrorState`; disabled state | No `data_status`; show backend warnings | Submit target weights and cash contribution/withdrawal, verify buy/sell/hold rows, cash totals, warnings, disabled flag |

## Proposed Reusable Component Library

Target directory: `frontend/src/components/ui` for generic UI and `frontend/src/components/portfolio` or `frontend/src/components/analytics` for domain-specific components.

### Generic UI Components

`PageHeader`
- Props: eyebrow, title, description, actions, metadata.
- Replaces repeated page header sections across dashboard, analytics, holdings, upload, advisor, watchlist, settings.

`SectionCard`
- Thin wrapper around `Card` with optional title, description, actions, footer.
- Keeps card headers consistent without forcing nested cards.

`ChartCard`
- Section card variant with stable chart height, loading/empty/error slots, and optional data status footer.
- Used by allocation, performance, risk, optimizer frontier, and dashboard charts.

`EmptyState`
- Already exists, but should support optional action slot.

`ErrorState`
- Already exists, but should support API error details and retry action.

`FeatureDisabledState`
- New component for backend `feature_disabled` 404s.
- Should identify the disabled module without making it look like a failure.

`DataStatusBadge`
- New component for `DataStatus`.
- Should encode mock, stale, live, unavailable, provider, and as-of.
- Should be usable inline in tables and as a page warning.

### Portfolio and Analytics Components

`MetricCard`
- Standard metric presentation with label, value, detail, tone, icon, and data status/tooltip.
- Replaces duplicate `MetricCard` definitions in `DashboardPage` and `AnalyticsPage`.

`AllocationChart`
- Reusable pie/donut allocation chart with legend, empty state, stable colors, and accessible labels.
- Replaces duplicate allocation chart logic in dashboard and analytics.

`HoldingsTable`
- Reusable read-only holdings table with configurable columns and action slot.
- Manual holdings editing can wrap this instead of owning a separate table implementation.

`InsightCard`
- Standard display for backend rule insights, dashboard action items, optimizer warnings, peer warnings, and risk observations.

`DataQualitySummary`
- Domain component for missing prices, missing cost basis, stale prices, and backend warnings.

`PortfolioSelector`
- Centralized selector for pages that need portfolio scope.
- Should eventually connect to route/search state or a shared context.

`PeriodSelector`
- Shared segmented control for performance/risk/optimizer periods.

`TargetWeightsEditor`
- Reusable form/control for simulator, optimizer handoff, and rebalance tickets.

## Recommended Page Redesign Order

1. Shared frontend foundation
   - Add shared types for `DataStatus`, API error helpers, feature-disabled detection, formatters, and query-key helpers.
   - Extract `PageHeader`, `MetricCard`, `DataStatusBadge`, `FeatureDisabledState`, and action-capable `EmptyState`/`ErrorState`.

2. Dashboard
   - Integrate dashboard bundle first because it reduces current duplicated analytics composition and becomes the primary landing surface for portfolio state.
   - Replace page-derived dashboard sections with backend `DashboardBundleResponse`.

3. Upload
   - Extract upload wizard subcomponents, then integrate mapping suggestions.
   - This keeps upload complexity isolated before adding more portfolio analysis modules.

4. Analytics split
   - Break `AnalyticsPage` into overview/allocation/risk/performance/rules panels.
   - Introduce performance history and risk v2 behind tabs or separate routes only after extraction.

5. Research pages
   - Add fundamentals and peers after shared table/card/status components exist.
   - These pages will need dense comparison tables and clear coverage warnings.

6. Scenario tools
   - Add simulator, optimizer, and rebalance tickets after target-weight editing is shared.
   - Optimizer outputs can feed simulator/rebalance flows without duplicating weight controls.

7. Market overview and topbar
   - Add market overview route and header market status once `DataStatusBadge` and route metadata exist.
   - Avoid hard-wiring another one-off title/status path in `Header`.

8. Snapshots
   - Add snapshots after dashboard/performance/risk pages stabilize so comparisons have clear places to link from.

## Problems and Risks

### Functional Risks

- Feature flags are not represented in frontend state. Disabled backend modules will currently look like generic 404/API failures.
- Manual frontend types can drift from backend Pydantic schemas. Drift already exists in app status and upload responses.
- Portfolio selection is page-local in several places, so new modules may accidentally default to the first portfolio instead of respecting user intent.
- Mock/stale warnings are inconsistent. Existing warning logic is path/provider based, while new backend modules return precise `data_status`.
- Some planned modules share inputs and outputs. Simulator, optimizer, and rebalance tickets can easily duplicate target weight forms unless components are extracted first.

### Maintainability Risks

- Large page files already combine data fetching, state, formatting, charting, and domain UI.
- Recharts imports in dashboard and analytics are eagerly bundled, contributing to bundle size.
- Formatter helpers are duplicated across pages.
- Several components use direct Tailwind strings for repeated card/header/table patterns instead of reusable primitives.

### Styling and Layout Risks

- Tables are wrapped in `overflow-hidden`, not horizontal scrolling. Wide holdings, peers, correlation matrices, rebalance tickets, and fundamentals tables are likely to overflow on mobile/tablet.
- `Sidebar` is hidden on mobile, but the header menu button has no open/close behavior.
- Header action area is already busy with feedback/login/signup; adding portfolio, data source, and market status will need a deliberate compact layout.
- The main content `max-w-7xl` is reasonable for current pages but may be tight for correlation matrices, peer comparisons, and optimizer frontier/detail combinations.
- Repeated page headers and card structures have minor inconsistencies in text, spacing, and action placement.

## Manual QA Checklist

General:
- Run `npm run build` from `frontend/`.
- Start backend and frontend in local demo mode.
- Verify every route renders without console errors.
- Verify feature-disabled API responses render `FeatureDisabledState` after it is introduced.
- Verify network-off/backend-off requests render `ErrorState`.
- Verify mock/stale/unavailable data status appears wherever backend returns `data_status`.

Responsive:
- Test desktop, tablet, and mobile widths.
- Verify sidebar/mobile navigation behavior before adding many module routes.
- Verify all tables either fit or scroll horizontally without clipped columns.
- Verify chart cards maintain stable heights and do not collapse during loading.

Portfolio scope:
- Test with zero portfolios.
- Test with one empty portfolio.
- Test with one populated portfolio.
- Test with multiple portfolios and confirm selected portfolio is honored consistently.

Data state:
- Test mock market provider.
- Test stale/unavailable provider states where backend can produce them.
- Test missing price symbols and missing fundamentals coverage.
- Test insufficient history for performance, risk v2, and optimizer.

Upload:
- Upload valid CSV.
- Upload CSV with unmapped columns.
- Upload invalid rows and duplicate symbols.
- Confirm import and verify holdings invalidation.
- Verify mapping suggestions can be ignored and manual mapping still works.

Research/tools:
- Verify fundamentals weighted metrics and missing symbols.
- Verify peer comparison with sparse peers.
- Verify simulator warnings for invalid or unsupported targets.
- Verify optimizer unsupported/insufficient-history states.
- Verify rebalance tickets for buy/sell/hold and cash contribution/withdrawal.

## Exact Next Codex Prompts for the First 5 Frontend Tasks

1. Shared backend status and API error foundation

```text
You are working on P-insight. Work only inside /Users/dhruvtantia/Documents/Codex/p-insight-rebuild.

Do not redesign pages. Do not implement new feature pages yet.

Add frontend foundation for new backend modules:
- Create shared frontend types for DataStatus and API error payloads.
- Move market data response types out of services/marketDataApi.ts into frontend/src/types/marketData.ts.
- Update AppStatus type to match backend /api/status.
- Update upload types to include UploadRow.warnings plus ConfirmUploadResponse invalid_count, duplicate_count, rejected_row_reasons.
- Add a small API error helper that can detect backend error_code === "feature_disabled".

Run npm run build and report the result.
```

2. Reusable UI state/status components

```text
You are working on P-insight. Work only inside /Users/dhruvtantia/Documents/Codex/p-insight-rebuild.

Do not redesign pages and do not add new backend feature pages.

Add reusable frontend UI primitives needed by backend integrations:
- PageHeader
- MetricCard
- DataStatusBadge
- FeatureDisabledState
- Add optional action/retry slots to EmptyState and ErrorState without breaking existing callers.

Use existing styling conventions only. Then replace only obvious duplicate MetricCard/PageHeader usages in DashboardPage and AnalyticsPage if it stays low-risk.

Run npm run build and report the result.
```

3. Dashboard bundle integration preparation

```text
You are working on P-insight. Work only inside /Users/dhruvtantia/Documents/Codex/p-insight-rebuild.

Do not redesign DashboardPage.

Prepare frontend integration for backend dashboard bundle:
- Add types for DashboardBundleResponse and nested dashboard schemas based on backend/app/modules/dashboard/schemas.py.
- Add services/dashboardApi.ts for GET /api/portfolios/{portfolio_id}/dashboard.
- Add hooks/useDashboardBundle.ts with portfolio-scoped query keys and feature-disabled handling.
- Do not switch DashboardPage to the new endpoint yet unless it is a tiny, behavior-preserving wiring behind existing states.

Run npm run build and report the result.
```

4. Upload mapping suggestions integration

```text
You are working on P-insight. Work only inside /Users/dhruvtantia/Documents/Codex/p-insight-rebuild.

Do not redesign UploadPage.

Integrate backend upload mapping suggestions:
- Add ColumnMappingSuggestionsResponse frontend types based on backend/app/modules/uploads/schemas.py.
- Add getMappingSuggestions(uploadJobId) to uploadApi.
- Add a query to useUpload for mapping suggestions enabled only when uploadJobId exists.
- In UploadPage, show suggestions in the existing mapping step using current UI primitives, keeping manual mapping fully available.
- Show FeatureDisabledState or an unobtrusive disabled message if ENABLE_UPLOAD_SUGGESTIONS is off.

Run npm run build and report the result.
```

5. Performance and risk module type/service/hook foundation

```text
You are working on P-insight. Work only inside /Users/dhruvtantia/Documents/Codex/p-insight-rebuild.

Do not add routes or redesign AnalyticsPage yet.

Add frontend foundation for performance history and risk v2:
- Add frontend types for PortfolioPerformanceHistory and RiskV2Response based on backend schemas.
- Add services/performanceApi.ts and hooks/usePerformanceHistory.ts.
- Add services/riskApi.ts and hooks/useRiskV2.ts.
- Include period parameters, stable query keys, DataStatus typing, and feature-disabled handling.
- Do not render these modules in the UI yet.

Run npm run build and report the result.
```
