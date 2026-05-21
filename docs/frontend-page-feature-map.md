# Frontend Page Feature Map

Date: 2026-05-22

Scope: documentation-only page-to-feature ownership map for planning frontend integration. No frontend routes, services, hooks, components, or backend code are implemented by this document.

Sources:
- `docs/frontend-integration-architecture-plan.md`
- `docs/backend-feature-registry.md`
- `docs/modularity-and-isolation-audit.md`
- `docs/mock-data-audit.md`
- `docs/backend-feature-implementation-summary.md`
- `frontend/src/app/routes.tsx`
- `frontend/src/pages/*`
- `frontend/src/services/*`
- `frontend/src/hooks/*`
- `frontend/src/components/*`
- `frontend/src/components/layout/*`

## 1. Executive summary

P-insight should keep one primary frontend home for each backend feature and use secondary placements only for read-only summaries, drill-in links, or contextual hints. This prevents route duplication, feature sprawl, and pages that recalculate backend analytics.

Current routing keeps `/` as `LandingPage` inside `AppLayout`. The least disruptive route plan is to keep `/` as the public/demo landing route and add `/market` later for the logged-in or demo market overview. No current route exists for market, changes/snapshots, fundamentals, peers, simulate, or optimize.

Frontend integration must follow the existing service-plus-hook pattern: API calls belong in `frontend/src/services`, server-state orchestration belongs in TanStack Query hooks under `frontend/src/hooks`, and pages should compose UI state rather than duplicate backend calculations.

Mock, stale, static, synthetic, and placeholder data must remain visible in the UI plan. Performance history is synthetic current-holdings history. It is not XIRR and not time-weighted return. Real AI is later; the current advisor is deterministic/mock and must remain labeled.

## 2. Page-to-feature ownership table

| Page route | Current route? | Page status | Primary owned backend features | Secondary display only | Implementation priority |
|---|---:|---|---|---|---|
| `/` | Yes | MVP landing | Product entry, demo seed CTA | Market/demo status teaser only | Existing |
| `/market` | No | Internal demo first, MVP later | Market overview | Upload/demo CTA, compact data status | 2 |
| `/dashboard` | Yes | MVP | Dashboard bundle | Lightweight deterministic advisor/action hints | 3 |
| `/upload` | Yes | MVP | Upload suggestions/import summary | Sector metadata preview warnings | 4 |
| `/holdings` | Yes | MVP | Sector metadata, holdings CRUD workflow | Price freshness, links to research pages later | 5 |
| `/analytics` | Yes | MVP plus internal-demo panels | Historical market data, performance history, risk v2, existing allocation/rules | Data quality, deterministic hints | 6 |
| `/changes` | No | Internal demo first | Snapshots | Dashboard/analytics summary links | 7 |
| `/fundamentals` | No | Internal demo | Fundamentals | Links from holdings and peers | 8 |
| `/peers` | No | Internal demo | Peers | Selected holding/fundamentals context | 9 |
| `/advisor` | Yes | Internal demo | Advisor context | Dashboard, risk, performance, fundamentals, peers, changes context | 10 |
| `/watchlist` | Yes | MVP for CRUD, later for research workflow | Watchlist | Price source and future research links | 11 |
| `/simulate` | No | Later | Simulator | Current allocation/risk comparison | 12 |
| `/optimize` | No | Later | Optimizer, rebalance tickets | Simulator handoff, assumptions | 13 |
| `/brokers` | Yes | Later | Broker placeholders | Provider cards, interest capture | Later |
| `/billing` | Yes | Later | Billing placeholder | Plan/status display | Later |
| `/settings` | Yes | Later | Settings placeholder | Account/demo environment info | Later |
| `/admin` | Yes | Later | Admin placeholder | Diagnostics later | Later |

## 3. Backend feature to primary page table

This is the canonical ownership table. Each backend feature has exactly one primary frontend home.

| Backend feature | Feature status | Primary page | Secondary locations allowed | Backend endpoint(s) |
|---|---|---|---|---|
| Market overview | Feature-flagged, backend-ready for demo | `/market` | `/`, header later | `GET /api/market/overview` |
| Dashboard bundle | Backend-ready, frontend-missing | `/dashboard` | `/advisor` context | `GET /api/portfolios/{portfolio_id}/dashboard` |
| Upload suggestions/import summary | Current upload flow, suggestions feature-flagged | `/upload` | None, except import count summaries on dashboard later | Upload endpoints plus `GET /api/uploads/{upload_job_id}/mapping-suggestions` |
| Sector metadata | Current/backend-ready | `/holdings` | `/upload`, `/analytics` allocation labels | Holdings CRUD, upload confirm |
| Historical market data | Feature-flagged, mock/synthetic provider path | `/analytics` | Research chart foundation only | `GET /api/market/history`; legacy `GET /api/market-data/history/{symbol}` is not preferred |
| Performance history | Feature-flagged, internal-demo | `/analytics` | `/dashboard` small chart later, `/advisor` context | `GET /api/portfolios/{portfolio_id}/performance/history?period=1Y` |
| Risk v2 | Feature-flagged, internal-demo | `/analytics` | `/dashboard` risk summary, `/advisor` context | `GET /api/portfolios/{portfolio_id}/risk?period=1Y` |
| Snapshots | Feature-flagged, backend-ready | `/changes` | `/dashboard` latest snapshot CTA | Snapshot create/list/compare endpoints |
| Fundamentals | Feature-flagged, mock/provider incomplete | `/fundamentals` | `/holdings`, `/peers`, `/advisor` context | `GET /api/assets/{symbol}/fundamentals`; `GET /api/portfolios/{portfolio_id}/fundamentals` |
| Peers | Feature-flagged, static/mock | `/peers` | `/holdings`, `/fundamentals`, `/advisor` context | `GET /api/portfolios/{portfolio_id}/peers/{symbol}` |
| Advisor context | Current deterministic/mock, expanded context partial | `/advisor` | Dashboard may show deterministic action hints only | Advisor summary/question/conversation endpoints |
| Simulator | Feature-flagged, later | `/simulate` | `/optimize` target handoff later | `POST /api/portfolios/{portfolio_id}/simulate` |
| Optimizer | Feature-flagged, later/internal demo data | `/optimize` | `/simulate` comparison later | `POST /api/portfolios/{portfolio_id}/optimize` |
| Rebalance tickets | Feature-flagged, later | `/optimize` | None until workflow grows enough for `/rebalance` | `POST /api/portfolios/{portfolio_id}/rebalance/tickets` |
| Watchlist | Current | `/watchlist` | `/advisor` or research pages later | `GET /api/watchlist`; `POST /api/watchlist`; `DELETE /api/watchlist/{id}` |
| Broker placeholders | Current placeholder, later | `/brokers` | Settings billing/admin summaries later | Broker connection placeholder endpoints |
| Billing placeholder | Current placeholder, later | `/billing` | Settings/admin summaries later | Billing plan and checkout placeholder endpoints |
| Settings/admin placeholders | Mock/demo only, later | `/settings`, `/admin` | None | Status/config/admin placeholder surfaces |

## 4. Current vs planned route table

| Route | Current behavior | Planned behavior | Route decision |
|---|---|---|---|
| `/` | `LandingPage` inside `AppLayout` | Public/demo landing, upload/demo CTA, high-level mock warning | Keep current route |
| `/login`, `/signup` | Placeholder auth pages | Later real auth | Keep out of feature ownership |
| `/onboarding` | Demo seed and portfolio creation | MVP onboarding support | Keep out of feature ownership |
| `/dashboard` | Current dashboard composed from analytics and holdings hooks | Own dashboard bundle integration | Keep |
| `/holdings` | Current holdings CRUD and price refresh | Own source-of-truth holdings and sector metadata | Keep |
| `/upload` | Current upload wizard | Own upload ingestion and mapping suggestions | Keep |
| `/analytics` | Current allocation/rules/performance placeholders | Own analytics, performance, history, and risk panels | Keep |
| `/advisor` | Current deterministic/mock advisor UI | Own advisor context expansion | Keep |
| `/watchlist` | Current watchlist CRUD plus inline price query | Own watchlist CRUD, move price reads to hook later | Keep |
| `/brokers` | Placeholder broker interest surface | Later provider placeholders only | Keep, de-prioritize |
| `/billing` | Placeholder billing surface | Later billing placeholder or real billing | Keep, de-prioritize |
| `/settings` | Placeholder settings | Later account/preferences | Keep, de-prioritize |
| `/admin` | Placeholder admin scaffold | Later internal diagnostics | Keep, de-prioritize |
| `/market` | Not present | Market overview page | Planned route |
| `/changes` | Not present | Snapshot list/create/compare and portfolio changes | Planned route; do not also add `/snapshots` |
| `/fundamentals` | Not present | Portfolio and stock fundamentals | Planned route |
| `/peers` | Not present | Holding peer comparison | Planned route |
| `/simulate` | Not present | Scenario testing without trades | Planned route, later |
| `/optimize` | Not present | Optimizer and rebalance ticket downstream section | Planned route, later |
| `/rebalance` | Not present | No standalone route for now | Do not add unless workflow becomes large |

## 5. MVP page group

### `/`

| Field | Plan |
|---|---|
| Page route | `/` |
| Page status | MVP landing |
| User purpose | India-first product entry, demo seed, upload CTA, and clear beta/mock positioning. |
| Primary backend features owned by this page | None from the backend feature registry; this page owns product entry only. |
| Secondary backend features displayed on this page | Demo seed CTA; market/demo status teaser later if concise. |
| Backend endpoints consumed | Current: `POST /api/demo/seed` through demo seed flow. Future optional: `GET /api/status`. |
| Existing frontend service files | `frontend/src/services/demoApi.ts`, `frontend/src/services/statusApi.ts`. |
| Future frontend service files needed | None for MVP; do not add market ownership here. |
| Existing frontend hooks | `frontend/src/hooks/useDemoSeed.ts`, `frontend/src/hooks/useAppStatus.ts` available. |
| Future hooks needed | None for MVP. |
| Components needed | Existing `Button`, `Card`, `Badge`, `ErrorState`; future `MockDataBanner` if status is surfaced. |
| Loading state | Demo seed button pending state. |
| Empty state | Not applicable. |
| Error state | Demo seed failure via `ErrorState`. |
| Feature-disabled state | If demo mode is disabled, CTA should explain demo is unavailable without claiming an app failure. |
| Mock/stale/demo data display | Must say demo data and mock AI/market data are not investment-grade. |
| Manual QA checklist | Landing loads; demo seed CTA works in demo mode; disabled demo mode is clear; navigation to upload/dashboard remains intact. |
| Implementation priority | Existing; keep stable. |
| Notes / risks | Do not turn `/` into market ownership. `/market` owns market data. |

### `/dashboard`

| Field | Plan |
|---|---|
| Page route | `/dashboard` |
| Page status | MVP |
| User purpose | Main portfolio overview after upload or demo seed. |
| Primary backend features owned by this page | Dashboard bundle. |
| Secondary backend features displayed on this page | Lightweight deterministic advisor/action hints only when clearly labeled; performance/risk summaries later as read-only snippets. |
| Backend endpoints consumed | Future primary: `GET /api/portfolios/{portfolio_id}/dashboard`. Current support: portfolio list, holdings, analytics summary/allocation/rules, price refresh. |
| Existing frontend service files | `portfolioApi.ts`, `holdingsApi.ts`, `analyticsApi.ts`, `marketDataApi.ts`. |
| Future frontend service files needed | `dashboardApi.ts`. |
| Existing frontend hooks | `usePortfolios`, `useHoldings`, `useAnalytics`, `usePortfolioPrices`. |
| Future hooks needed | `useDashboardBundle`. |
| Components needed | `PageHeader`, `DataStatusBadge`, `DataQualityBanner`, `MetricCard`, `ChartCard`, `AllocationChart`, `HoldingsTable`, `InsightCard`, `LoadingState`, `EmptyState`, `ErrorState`, `FeatureDisabledState`. |
| Loading state | Page-level loading for portfolio selection and dashboard bundle; section loading for refresh mutations. |
| Empty state | No portfolio; empty portfolio; no priced holdings; no action items. |
| Error state | Portfolio load error; dashboard bundle request error; price refresh error. |
| Feature-disabled state | Show `FeatureDisabledState` for `ENABLE_DASHBOARD_BUNDLE=false`; fall back to existing current frontend composition only if explicitly chosen later. |
| Mock/stale/demo data display | Show bundle `data_status`, data quality status, stale price warnings, missing price/cost badges, and current provider source. |
| Manual QA checklist | Portfolio selector chooses correct portfolio; KPIs match backend bundle; top holdings, allocation, concentration, data quality, and action items render; disabled flag is friendly; mock/stale labels are visible. |
| Implementation priority | 3. |
| Notes / risks | Dashboard should not sort into new analytics beyond view-level ordering; backend owns KPI and concentration logic. |

### `/upload`

| Field | Plan |
|---|---|
| Page route | `/upload` |
| Page status | MVP |
| User purpose | Portfolio ingestion workflow for CSV/manual upload. |
| Primary backend features owned by this page | Upload suggestions/import summary. |
| Secondary backend features displayed on this page | Sector metadata warnings/previews during mapping and import. |
| Backend endpoints consumed | `POST /api/portfolios/{portfolio_id}/uploads`, `GET /api/uploads/{upload_job_id}`, `POST /api/uploads/{upload_job_id}/column-mapping`, `GET /api/uploads/{upload_job_id}/mapping-suggestions`, `POST /api/uploads/{upload_job_id}/validate`, `POST /api/uploads/{upload_job_id}/confirm`, `GET /api/uploads/{upload_job_id}/errors`. |
| Existing frontend service files | `uploadApi.ts`, `portfolioApi.ts`. |
| Future frontend service files needed | Extend `uploadApi.ts` for mapping suggestions and full import summary fields. |
| Existing frontend hooks | `useUpload`, `usePortfolios`. |
| Future hooks needed | Extend `useUpload` or add `useUploadMappingSuggestions`. |
| Components needed | `PageHeader`, `FeatureDisabledState`, `DataQualityBanner`, upload step cards, mapping controls, validation summary, rejected rows table, duplicate warnings, ISIN warnings, `LoadingState`, `EmptyState`, `ErrorState`. |
| Loading state | File upload pending, mapping suggestions loading, validation pending, confirm/import pending. |
| Empty state | No portfolio; no preview rows; no rejected rows after validation. |
| Error state | Upload parse error; mapping submit error; validation error; import error. |
| Feature-disabled state | Mapping suggestions disabled should leave manual mapping fully usable. |
| Mock/stale/demo data display | Upload mechanics are real; sample CSV/demo seed labels should remain visible when applicable. |
| Manual QA checklist | Upload sample CSV; manual mapping works without suggestions; suggestions can be applied or ignored; validation shows rejected rows and warnings; confirm summary includes invalid/duplicate/rejected reasons. |
| Implementation priority | 4. |
| Notes / risks | Suggestions are deterministic heuristics and must not be auto-applied silently. |

### `/holdings`

| Field | Plan |
|---|---|
| Page route | `/holdings` |
| Page status | MVP |
| User purpose | Portfolio source-of-truth table and manual corrections. |
| Primary backend features owned by this page | Sector metadata plus existing holdings CRUD workflow. |
| Secondary backend features displayed on this page | Current price display, price freshness/source, missing price/cost badges, links to fundamentals/peers later. |
| Backend endpoints consumed | Holdings CRUD under `/api/portfolios/{portfolio_id}/holdings`; upload confirm for imported sector metadata; `POST /api/portfolios/{portfolio_id}/prices/refresh`. |
| Existing frontend service files | `holdingsApi.ts`, `marketDataApi.ts`, `portfolioApi.ts`. |
| Future frontend service files needed | Extend holding types if sector provenance fields are missing; no new feature service needed. |
| Existing frontend hooks | `useHoldings`, `usePortfolioPrices`, `usePortfolios`. |
| Future hooks needed | Optional `useHoldingResearchLinks` only after research routes exist. |
| Components needed | `PageHeader`, `HoldingsTable`, `DataStatusBadge`, `DataQualityBanner`, sector source badges, missing data badges, `LoadingState`, `EmptyState`, `ErrorState`. |
| Loading state | Portfolio list loading; holdings loading; price refresh pending. |
| Empty state | No portfolio; no holdings; no matching filtered rows. |
| Error state | Portfolio load error; holdings request error; CRUD mutation error; price refresh error. |
| Feature-disabled state | Not applicable for core holdings; research links should hide or show disabled state if target feature is disabled. |
| Mock/stale/demo data display | Price source badges must show mock providers; sector source and sector updated-at must be visible when available. |
| Manual QA checklist | Create, edit, delete holdings; sector override persists; upload-origin sector metadata is visible; refresh prices shows provider and stale/as-of status; missing price/cost badges appear. |
| Implementation priority | 5. |
| Notes / risks | Holdings owns corrections, not analytics conclusions. Do not add peer/fundamental workflows inline. |

### `/watchlist`

| Field | Plan |
|---|---|
| Page route | `/watchlist` |
| Page status | MVP for current CRUD; expanded research workflow later |
| User purpose | Track stocks being researched outside current holdings. |
| Primary backend features owned by this page | Watchlist. |
| Secondary backend features displayed on this page | Current/future price source; later links to fundamentals, peers, simulator, and advisor. |
| Backend endpoints consumed | `GET /api/watchlist`, `POST /api/watchlist`, `DELETE /api/watchlist/{watchlist_item_id}`; current inline batch price query uses `GET /api/market-data/prices`. |
| Existing frontend service files | `watchlistApi.ts`, `marketDataApi.ts`. |
| Future frontend service files needed | None for CRUD; future `researchApi` is not needed unless backend adds a real aggregate. |
| Existing frontend hooks | `useWatchlist`; page currently owns a TanStack Query price read inline. |
| Future hooks needed | `useWatchlistPrices` or `useBatchPrices` to remove inline page API access. |
| Components needed | `PageHeader`, watchlist table, notes editor, `DataStatusBadge`, `LoadingState`, `EmptyState`, `ErrorState`. |
| Loading state | Watchlist loading; price query loading. |
| Empty state | No watchlist symbols. |
| Error state | CRUD errors; price load error should not block CRUD. |
| Feature-disabled state | Not applicable for current CRUD. Later research links should show disabled states when target modules are off. |
| Mock/stale/demo data display | Price source and as-of must be visible; mock providers use warning tone. |
| Manual QA checklist | Add symbol; add notes; delete symbol; batch prices show source/as-of; price failures do not prevent watchlist CRUD. |
| Implementation priority | 11 for expansion; current CRUD exists. |
| Notes / risks | Move page-owned query into a hook before adding richer research features. |

## 6. Internal-demo page group

### `/market`

| Field | Plan |
|---|---|
| Page route | `/market` |
| Page status | Internal demo first; MVP later after market data provider is stable |
| User purpose | India-first market context before or alongside portfolio work. |
| Primary backend features owned by this page | Market overview. |
| Secondary backend features displayed on this page | Upload/demo CTA; source/mock/stale market-data status; optional compact market status for header later. |
| Backend endpoints consumed | `GET /api/market/overview`. |
| Existing frontend service files | `marketDataApi.ts` exists for legacy prices/history, but no market overview service exists. |
| Future frontend service files needed | `marketOverviewApi.ts`. |
| Existing frontend hooks | None specific. |
| Future hooks needed | `useMarketOverview`. |
| Components needed | `PageHeader`, `DataStatusBadge`, `MockDataBanner`, index cards for NIFTY 50/Sensex/Bank Nifty, sector index table, gainers/losers table, `LoadingState`, `EmptyState`, `ErrorState`, `FeatureDisabledState`. |
| Loading state | Page-level overview loading with stable card/table skeletons. |
| Empty state | No index rows, no sector rows, or no mover rows should show section-specific empty states. |
| Error state | Generic overview load failure; provider unavailable warning. |
| Feature-disabled state | `ENABLE_MARKET_OVERVIEW=false` should show feature disabled, not a broken market page. |
| Mock/stale/demo data display | Top-level overview, market status, index cards, sector cards, and movers must show `DataStatus`; mock/static mover warnings must remain visible. |
| Manual QA checklist | Load enabled page; verify market status, indices, sectors, gainers/losers; disable flag; simulate mock provider; verify stale/as-of labels. |
| Implementation priority | 2. |
| Notes / risks | Do not move landing ownership to `/market`. Real MVP status waits for stable provider coverage. |

### `/analytics`

| Field | Plan |
|---|---|
| Page route | `/analytics` |
| Page status | Existing allocation/rules are MVP; performance/risk v2/benchmark/drawdown are Internal demo |
| User purpose | Portfolio analytics and risk/performance review. |
| Primary backend features owned by this page | Historical market data, performance history, risk v2, existing allocation/rules analytics. |
| Secondary backend features displayed on this page | Concentration analytics, metric statuses, data quality, deterministic action hints only if clearly labeled. |
| Backend endpoints consumed | Current: `/api/portfolios/{portfolio_id}/analytics/*`. Future: `GET /api/market/history`, `GET /api/portfolios/{portfolio_id}/performance/history?period=1Y`, `GET /api/portfolios/{portfolio_id}/risk?period=1Y`. |
| Existing frontend service files | `analyticsApi.ts`, `marketDataApi.ts`. |
| Future frontend service files needed | `marketHistoryApi.ts`, `performanceApi.ts`, `riskApi.ts`. |
| Existing frontend hooks | `useAnalytics`, `usePortfolios`. |
| Future hooks needed | `useMarketHistory`, `usePerformanceHistory`, `useRiskV2`. |
| Components needed | `PageHeader`, `PeriodSelector`, `MetricCard`, `ChartCard`, `AllocationChart`, `DataStatusBadge`, metric status fields, assumptions banner, `LoadingState`, `EmptyState`, `ErrorState`, `FeatureDisabledState`. |
| Loading state | Existing analytics loading plus per-tab loading for performance/risk/history. |
| Empty state | No portfolio; no priced holdings; insufficient observations; no benchmark series; no rules. |
| Error state | Analytics load error; performance/risk request error; provider/history unavailable. |
| Feature-disabled state | Feature-disabled panels should remain isolated so allocation/rules still work when performance or risk is off. |
| Mock/stale/demo data display | Synthetic history must be labeled as synthetic current holdings. Explicitly state it is not XIRR and not time-weighted return. Risk v2 must show metric statuses and assumptions. |
| Manual QA checklist | Existing allocation/rules still pass; performance periods render; benchmark vs NIFTY labels are visible; null risk metrics show N/A/status; disabled flags affect only related panels. |
| Implementation priority | 6. |
| Notes / risks | Do not calculate drawdown, volatility, Sharpe, Sortino, beta, or benchmark returns in the page. Backend owns analytics logic. |

### `/changes`

| Field | Plan |
|---|---|
| Page route | `/changes` |
| Page status | Internal demo first; later if not wired |
| User purpose | Portfolio history and comparison across saved snapshots. |
| Primary backend features owned by this page | Snapshots. |
| Secondary backend features displayed on this page | Latest dashboard summary link; analytics allocation context as read-only comparison. |
| Backend endpoints consumed | `POST /api/portfolios/{portfolio_id}/snapshots`, `GET /api/portfolios/{portfolio_id}/snapshots`, `GET /api/portfolios/{portfolio_id}/snapshots/compare?from_id=&to_id=`. |
| Existing frontend service files | None. |
| Future frontend service files needed | `snapshotsApi.ts`. |
| Existing frontend hooks | None. |
| Future hooks needed | `useSnapshots`. |
| Components needed | `PageHeader`, snapshot create form, snapshot list, compare selector, holding changes table, sector allocation changes table, concentration change cards, `LoadingState`, `EmptyState`, `ErrorState`, `FeatureDisabledState`. |
| Loading state | Snapshot list loading; create mutation pending; compare loading. |
| Empty state | No snapshots; only one snapshot so comparison is unavailable; empty portfolio snapshot. |
| Error state | Create/list/compare failures. |
| Feature-disabled state | `ENABLE_SNAPSHOTS=false` should show disabled state and avoid compare controls. |
| Mock/stale/demo data display | Snapshot responses do not expose `DataStatus`; if snapshot values include mock-priced holdings, show a provenance warning based on available source fields or portfolio status. |
| Manual QA checklist | Create named snapshot; list snapshots newest-first; compare two snapshots; verify added/removed/changed holdings, sector allocation changes, concentration changes, and disabled flag. |
| Implementation priority | 7. |
| Notes / risks | Use `/changes`, not both `/changes` and `/snapshots`. Backend/service naming can remain snapshots. |

### `/fundamentals`

| Field | Plan |
|---|---|
| Page route | `/fundamentals` |
| Page status | Internal demo while mock/provider coverage is incomplete |
| User purpose | Portfolio and stock-level fundamental analysis. |
| Primary backend features owned by this page | Fundamentals. |
| Secondary backend features displayed on this page | Links from holdings; peer comparison entry points; advisor context. |
| Backend endpoints consumed | `GET /api/portfolios/{portfolio_id}/fundamentals`, `GET /api/assets/{symbol}/fundamentals`. |
| Existing frontend service files | None. |
| Future frontend service files needed | `fundamentalsApi.ts`. |
| Existing frontend hooks | None. |
| Future hooks needed | `usePortfolioFundamentals`, `useAssetFundamentals` or combined `useFundamentals`. |
| Components needed | `PageHeader`, `DataStatusBadge`, coverage warning, valuation/quality/growth/income/leverage metric tables, symbol lookup, `MetricCard`, `LoadingState`, `EmptyState`, `ErrorState`, `FeatureDisabledState`. |
| Loading state | Portfolio fundamentals loading; symbol fundamentals lookup pending. |
| Empty state | No holdings; no covered symbols; selected symbol has no metrics. |
| Error state | Provider unavailable; portfolio request error; symbol request error. |
| Feature-disabled state | `ENABLE_FUNDAMENTALS=false` should show feature disabled without hiding why peers/advisor context may be sparse. |
| Mock/stale/demo data display | Mock fundamentals provider, coverage percentage, missing symbols, missing metrics, provider/source, and warning text must be visible. |
| Manual QA checklist | Portfolio weighted metrics render; missing symbol coverage is visible; single stock lookup works; unknown symbols do not fabricate metrics; mock provider warning appears. |
| Implementation priority | 8. |
| Notes / risks | Do not imply live fundamentals coverage until a real provider exists. |

### `/peers`

| Field | Plan |
|---|---|
| Page route | `/peers` |
| Page status | Internal demo |
| User purpose | Compare a selected holding against relevant peers. |
| Primary backend features owned by this page | Peers. |
| Secondary backend features displayed on this page | Selected holding context; nested fundamentals metrics; peer-set quality warning. |
| Backend endpoints consumed | `GET /api/portfolios/{portfolio_id}/peers/{symbol}`. |
| Existing frontend service files | None. |
| Future frontend service files needed | `peersApi.ts`. |
| Existing frontend hooks | None. |
| Future hooks needed | `usePeerComparison`. |
| Components needed | `PageHeader`, portfolio/holding selector, peer metric comparison table, rank badges, `DataStatusBadge`, peer-set quality banner, `LoadingState`, `EmptyState`, `ErrorState`, `FeatureDisabledState`. |
| Loading state | Peer comparison loading after symbol selection. |
| Empty state | No portfolio; no holdings; no peers for selected symbol; sparse peer set. |
| Error state | Peer request error; fundamentals provider error surfaced through peer response. |
| Feature-disabled state | `ENABLE_PEERS=false` should show disabled state and link to holdings/fundamentals only if useful. |
| Mock/stale/demo data display | Static peer map warning, mock fundamentals status, sparse peer set warning, and null metric handling must remain visible. |
| Manual QA checklist | Select holding; compare peers; rank table handles null metrics; static/mock warnings visible; disabled flag works. |
| Implementation priority | 9. |
| Notes / risks | Peers should not duplicate fundamentals API aggregation. It consumes peer comparison response. |

### `/advisor`

| Field | Plan |
|---|---|
| Page route | `/advisor` |
| Page status | Internal demo |
| User purpose | Explain portfolio analytics using deterministic/rule-based context first. |
| Primary backend features owned by this page | Advisor context. |
| Secondary backend features displayed on this page | Dashboard, performance, risk, fundamentals, peers, and snapshot/change context when enabled. |
| Backend endpoints consumed | `POST /api/portfolios/{portfolio_id}/ai/summary`, `POST /api/portfolios/{portfolio_id}/ai/question`, `GET /api/portfolios/{portfolio_id}/ai/conversations`, `GET /api/ai/conversations/{conversation_id}`. |
| Existing frontend service files | `aiApi.ts`, `analyticsApi.ts`, `statusApi.ts`. |
| Future frontend service files needed | None for advisor endpoint ownership; future context is backend-composed. |
| Existing frontend hooks | `useAIAdvisor`, `useAnalytics`, `useAppStatus`, `usePortfolios`. |
| Future hooks needed | Optional context status hook only if backend exposes context readiness separately. |
| Components needed | `PageHeader`, conversation list, chat panel, context status badges, `MockDataBanner`, `InsightCard`, `LoadingState`, `EmptyState`, `ErrorState`, `FeatureDisabledState` for optional context blocks if exposed. |
| Loading state | Portfolio loading; conversation history loading; summary/question pending; context loading. |
| Empty state | No portfolio; no conversations; no analytics context. |
| Error state | Advisor request error; conversation load error; missing analytics context. |
| Feature-disabled state | Advisor itself is not feature-gated; optional context blocks should be labeled unavailable rather than failing the whole advisor. |
| Mock/stale/demo data display | Real AI is later. Current deterministic/mock advisor responses must show provider/model mock labels and must not be presented as direct investment advice. |
| Manual QA checklist | Generate summary; ask question; conversation persists; mock provider badge visible; optional disabled backend context does not break response; safety copy remains. |
| Implementation priority | 10. |
| Notes / risks | Do not add frontend-side AI reasoning or analytics calculations. Backend context builder owns context composition. |

## 7. Later page group

### `/simulate`

| Field | Plan |
|---|---|
| Page route | `/simulate` |
| Page status | Later, unless backend and frontend are both stable |
| User purpose | Scenario testing without real trades. |
| Primary backend features owned by this page | Simulator. |
| Secondary backend features displayed on this page | Current vs simulated allocation/risk comparison. |
| Backend endpoints consumed | `POST /api/portfolios/{portfolio_id}/simulate`. |
| Existing frontend service files | None. |
| Future frontend service files needed | `simulatorApi.ts`. |
| Existing frontend hooks | None. |
| Future hooks needed | `usePortfolioSimulation` or `useSimulator`. |
| Components needed | `PageHeader`, `TargetWeightControls`, scenario holding editor, simulated allocation chart, warning banner, no-trades disclaimer, `LoadingState`, `EmptyState`, `ErrorState`, `FeatureDisabledState`. |
| Loading state | Simulation mutation pending. |
| Empty state | No portfolio; no holdings; no target weights. |
| Error state | Invalid weights; missing prices; simulation request error. |
| Feature-disabled state | `ENABLE_SIMULATOR=false` should show disabled state. |
| Mock/stale/demo data display | Response has warnings and `persisted=false`; show no-trades disclaimer and current price source where available. |
| Manual QA checklist | Add/remove holdings in scenario; target weights normalize warnings; compare current vs simulated allocation; missing prices are skipped with warnings; no persistence implied. |
| Implementation priority | 12. |
| Notes / risks | Do not implement before shared target controls exist. |

### `/optimize`

| Field | Plan |
|---|---|
| Page route | `/optimize` |
| Page status | Later |
| User purpose | Portfolio optimization and efficient frontier; downstream rebalance ticket estimates. |
| Primary backend features owned by this page | Optimizer, rebalance tickets. |
| Secondary backend features displayed on this page | Simulator handoff, target allocation comparison. |
| Backend endpoints consumed | `POST /api/portfolios/{portfolio_id}/optimize`; downstream section uses `POST /api/portfolios/{portfolio_id}/rebalance/tickets`. |
| Existing frontend service files | None. |
| Future frontend service files needed | `optimizerApi.ts`, `rebalanceApi.ts`. |
| Existing frontend hooks | None. |
| Future hooks needed | `useOptimizer`, `useRebalanceTickets`. |
| Components needed | `PageHeader`, optimizer assumptions panel, efficient frontier chart, min variance/max Sharpe result cards, `TargetWeightControls`, `RebalanceTicketTable`, warnings, no-trading-execution disclaimer, `LoadingState`, `EmptyState`, `ErrorState`, `FeatureDisabledState`. |
| Loading state | Optimizer mutation pending; rebalance ticket mutation pending. |
| Empty state | Insufficient history; unsupported portfolio; no target weights; no tickets needed. |
| Error state | Optimization request error; invalid targets; missing prices for ticket generation. |
| Feature-disabled state | Separate disabled states for optimizer and rebalance tickets so one disabled module does not break the whole page. |
| Mock/stale/demo data display | Optimizer uses mock/synthetic historical estimates today; show assumptions, warnings, status, and `data_status`. Rebalance tickets are estimates, not execution. |
| Manual QA checklist | Run optimizer; verify min variance/max Sharpe/frontier points; handle insufficient history; generate tickets from targets; verify cash totals, estimated shares, leftover cash, warnings, and no execution disclaimer. |
| Implementation priority | 13 for optimizer, 14 for rebalance tickets. |
| Notes / risks | Do not create `/rebalance` until ticket workflow becomes large enough to own a standalone route. |

### `/brokers`

| Field | Plan |
|---|---|
| Page route | `/brokers` |
| Page status | Later |
| User purpose | Broker connection placeholders and interest capture only. |
| Primary backend features owned by this page | Broker placeholders. |
| Secondary backend features displayed on this page | Provider cards, placeholder connection status. |
| Backend endpoints consumed | Broker connection list/providers/connect-placeholder/delete endpoints. |
| Existing frontend service files | `brokerConnectionsApi.ts`. |
| Future frontend service files needed | Replace or extend only when real broker auth exists. |
| Existing frontend hooks | `useBrokerConnections`. |
| Future hooks needed | Real broker connection lifecycle hooks later. |
| Components needed | `PageHeader`, provider cards, placeholder badge, waitlist/interest action, `LoadingState`, `EmptyState`, `ErrorState`. |
| Loading state | Providers/connections loading; interest mutation pending. |
| Empty state | No broker interest yet. |
| Error state | Provider load error; mark-interest error. |
| Feature-disabled state | If broker placeholders are hidden later, show friendly "manual upload is supported" state. |
| Mock/stale/demo data display | Must say broker sync is placeholder and does not start real broker auth. |
| Manual QA checklist | Providers load; mark interest works; placeholder language visible; no real broker OAuth implied. |
| Implementation priority | Later. |
| Notes / risks | Do not prioritize before upload/manual portfolio flow is stable. |

### `/billing`

| Field | Plan |
|---|---|
| Page route | `/billing` |
| Page status | Later |
| User purpose | Billing placeholder or future subscription management. |
| Primary backend features owned by this page | Billing placeholder. |
| Secondary backend features displayed on this page | Plan/status summary. |
| Backend endpoints consumed | `GET /api/billing/plan`, `POST /api/billing/create-checkout-session`. |
| Existing frontend service files | `billingApi.ts`. |
| Future frontend service files needed | Extend only when real billing provider exists. |
| Existing frontend hooks | `useBilling`. |
| Future hooks needed | Real subscription/checkout hooks later. |
| Components needed | `PageHeader`, plan cards, placeholder badge, checkout disabled/coming-soon state, `LoadingState`, `ErrorState`. |
| Loading state | Plan loading; placeholder checkout pending. |
| Empty state | Not applicable. |
| Error state | Plan load error; checkout placeholder error. |
| Feature-disabled state | If billing is unavailable, show feature-disabled or coming-soon state. |
| Mock/stale/demo data display | Billing is placeholder; no Stripe checkout or payment processing is active. |
| Manual QA checklist | Plan loads; checkout placeholder message is visible; no payment claim appears. |
| Implementation priority | Later. |
| Notes / risks | Do not block portfolio MVP on billing. |

### `/settings`

| Field | Plan |
|---|---|
| Page route | `/settings` |
| Page status | Later |
| User purpose | Account, preferences, data export, and environment settings later. |
| Primary backend features owned by this page | Settings placeholder. |
| Secondary backend features displayed on this page | Demo user and environment/provider status. |
| Backend endpoints consumed | Current/future `GET /api/status`; real profile/preferences later. |
| Existing frontend service files | `statusApi.ts` exists. |
| Future frontend service files needed | `settingsApi.ts` only when backend settings exist. |
| Existing frontend hooks | `useAppStatus` available. |
| Future hooks needed | `useSettings` only when backend settings exist. |
| Components needed | `PageHeader`, status rows, placeholder badges, `FeatureDisabledState`. |
| Loading state | Status/settings loading later. |
| Empty state | No preferences configured later. |
| Error state | Status/settings load error. |
| Feature-disabled state | Disabled preference/export/delete actions should explain unavailable beta behavior. |
| Mock/stale/demo data display | Demo user and placeholder auth must be visible until real auth exists. |
| Manual QA checklist | Placeholder actions are clearly disabled; demo status is visible; no real account management is implied. |
| Implementation priority | Later. |
| Notes / risks | Settings should not become a dumping ground for feature flags or research workflows. |

### `/admin`

| Field | Plan |
|---|---|
| Page route | `/admin` |
| Page status | Later |
| User purpose | Internal diagnostics/admin surfaces only if needed. |
| Primary backend features owned by this page | Admin placeholder. |
| Secondary backend features displayed on this page | Backend status, feature flag diagnostics, provider readiness later. |
| Backend endpoints consumed | Future admin/status endpoints only. |
| Existing frontend service files | `statusApi.ts` available. |
| Future frontend service files needed | `adminApi.ts` only if backend admin endpoints exist. |
| Existing frontend hooks | `useAppStatus` available. |
| Future hooks needed | `useAdminDiagnostics` only when implemented. |
| Components needed | `PageHeader`, diagnostics tables, `LoadingState`, `EmptyState`, `ErrorState`, `FeatureDisabledState`. |
| Loading state | Diagnostics loading later. |
| Empty state | No diagnostics available. |
| Error state | Diagnostics request error. |
| Feature-disabled state | Admin unavailable in non-admin/demo environments. |
| Mock/stale/demo data display | Must clearly separate local/demo diagnostics from production readiness. |
| Manual QA checklist | Admin route does not expose unsupported controls; status labels are clear; non-admin behavior is safe later. |
| Implementation priority | Later. |
| Notes / risks | Do not make admin required for normal app operation. |

## 8. Frontend service/hook gap table

| Capability | Existing service/hook | Future service needed | Future hook needed | Notes |
|---|---|---|---|---|
| App status | `statusApi.ts`, `useAppStatus` | Extend types for missing `/api/status` fields | Existing hook can stay | Needed for provider/mock warnings. |
| Market overview | None | `marketOverviewApi.ts` | `useMarketOverview` | New `/market` owner. |
| Dashboard bundle | Existing dashboard uses holdings/analytics services | `dashboardApi.ts` | `useDashboardBundle` | Replace page-composed dashboard bundle over time. |
| Upload suggestions | `uploadApi.ts`, `useUpload` | Extend `uploadApi.ts` | Extend `useUpload` or add `useUploadMappingSuggestions` | Suggestions are feature-flagged enhancement. |
| Holdings/sector metadata | `holdingsApi.ts`, `useHoldings` | Extend types if missing provenance fields | Existing hook can stay | Holdings owns correction workflow. |
| Market history | Legacy `marketDataApi.ts` | `marketHistoryApi.ts` | `useMarketHistory` | Prefer new `/api/market/history` contract over legacy route. |
| Performance history | None | `performanceApi.ts` | `usePerformanceHistory` | Internal-demo with synthetic labels. |
| Risk v2 | Existing legacy analytics risk via `analyticsApi.ts` | `riskApi.ts` | `useRiskV2` | Keep separate from legacy analytics risk. |
| Snapshots/changes | None | `snapshotsApi.ts` | `useSnapshots` | Route is `/changes`; service can use backend name. |
| Fundamentals | None | `fundamentalsApi.ts` | `useFundamentals` | Include portfolio and asset lookup. |
| Peers | None | `peersApi.ts` | `usePeerComparison` | Must display static/mock warnings. |
| Advisor | `aiApi.ts`, `useAIAdvisor` | None initially | Existing hook can stay | Backend composes optional context. |
| Watchlist | `watchlistApi.ts`, `useWatchlist`; inline price query in page | Optional shared price service remains `marketDataApi.ts` | `useBatchPrices` or `useWatchlistPrices` | Remove inline page query before expansion. |
| Simulator | None | `simulatorApi.ts` | `usePortfolioSimulation` or `useSimulator` | Later. |
| Optimizer | None | `optimizerApi.ts` | `useOptimizer` | Later. |
| Rebalance tickets | None | `rebalanceApi.ts` | `useRebalanceTickets` | Owned as `/optimize` section. |
| Brokers | `brokerConnectionsApi.ts`, `useBrokerConnections` | Real broker services later | Real lifecycle hooks later | Placeholder only. |
| Billing | `billingApi.ts`, `useBilling` | Real billing provider service later | Real checkout/subscription hooks later | Placeholder only. |

## 9. Shared component gap table

These are planned capabilities, not implemented files.

| Component capability | Status | Primary use | Notes |
|---|---|---|---|
| `DataStatusBadge` | Needed | Market, dashboard, analytics, fundamentals, peers, watchlist | Show source, provider, mock, stale, as-of, warning. |
| `FeatureDisabledState` | Needed | All feature-flagged pages/panels | Handle `feature_disabled` 404s without generic error UI. |
| `MetricCard` | Needed | Dashboard, analytics, fundamentals, optimizer | Replace duplicated metric cards. |
| `ChartCard` | Needed | Dashboard, analytics, optimizer | Stable loading/empty/error slots. |
| `SectionCard` | Needed | All pages | Consistent sections without nested cards. |
| `PageHeader` | Needed | All pages | Consistent title, description, actions, metadata. |
| `EmptyState` | Exists, needs action slot | All pages | Add optional action support later. |
| `ErrorState` | Exists, needs retry/detail support | All pages | Should handle API errors and retry actions. |
| `LoadingState` | Exists | All pages | May need section/card variants. |
| `DataQualityBanner` | Needed | Dashboard, holdings, analytics | Summarize missing prices/costs/provider issues. |
| `MockDataBanner` | Existing `DemoDataBanner`, broaden later | Layout/page warnings | Must not be hidden for cleaner UI. |
| `HoldingsTable` | Needed | Holdings, dashboard, simulator | Reusable source-of-truth rows. |
| `AllocationChart` | Needed | Dashboard, analytics, simulator | Avoid duplicate chart code. |
| `InsightCard` | Needed | Dashboard, advisor, analytics | Deterministic insights only. |
| `PeriodSelector` | Needed | Analytics, optimizer | Standard period control. |
| `TargetWeightControls` | Needed | Simulator, optimizer, rebalance tickets | Shared scenario target inputs. |
| `RebalanceTicketTable` | Needed | Optimize page | Estimated tickets, warnings, no execution. |

## 10. Mock/stale/demo display rules

- Never hide mock, stale, static, synthetic, or placeholder warnings for a cleaner UI.
- Use reusable indicators for `DataStatus` wherever backend provides it.
- Market data must show source/provider/as-of and warning state on index cards, movers, price refresh, and watchlist prices.
- Dashboard must show bundle-level and data-quality status, including missing price and cost-basis issues.
- Performance history must be labeled as synthetic current-holdings history. It is not XIRR and not time-weighted return.
- Risk v2 must show metric statuses and assumptions because it inherits synthetic/mock historical data.
- Fundamentals must show mock provider, coverage percentage, missing symbols, and missing metrics.
- Peers must show static peer map, sparse peer set, and nested fundamentals mock/provider warnings.
- Advisor must show deterministic/mock provider/model labels. Real AI is later.
- Simulator and rebalance tickets must show warnings, `persisted=false` behavior where applicable, no-trades/no-execution disclaimers, and current price caveats.
- Broker and billing pages must remain explicit placeholders until real integrations exist.
- Demo seed, sample CSVs, placeholder auth, and demo user status must remain visibly labeled in entry/onboarding/settings surfaces.

## 11. Manual QA checklist by page

| Page | Manual QA checklist |
|---|---|
| `/` | Landing loads; demo seed works in demo mode; demo disabled state is clear; no market ownership is implied. |
| `/market` | Overview loads when enabled; disabled flag shows `FeatureDisabledState`; NIFTY 50/Sensex/Bank Nifty, sectors, gainers, losers, and DataStatus labels render. |
| `/dashboard` | Portfolio selection works; dashboard bundle fields render; missing data/action items show; refresh errors are isolated; mock/stale labels visible. |
| `/upload` | Upload, mapping, suggestions, validation, rejected rows, duplicate warnings, ISIN warnings, and confirm summary work; suggestions disabled leaves manual mapping intact. |
| `/holdings` | CRUD works; sector override/source metadata visible; price refresh source/as-of visible; missing price/cost badges render. |
| `/analytics` | Existing allocation/rules still work; performance/risk panels handle loading, empty, disabled, and error states; synthetic/not-XIRR/not-TWR labels visible. |
| `/changes` | Create snapshot; list snapshots; compare two snapshots; show holding, sector, and concentration changes; disabled flag works. |
| `/fundamentals` | Portfolio weighted metrics, single-symbol lookup, missing coverage, unknown symbols, and mock provider warning render correctly. |
| `/peers` | Select holding; peer comparison renders; null metrics and ranks are safe; static/sparse/mock warnings visible. |
| `/advisor` | Summary/question flows work; conversation history loads; mock provider badge visible; optional context failures do not break response. |
| `/watchlist` | Add/delete item; notes persist; prices show source/as-of; price query failure does not block CRUD. |
| `/simulate` | Target scenarios submit; add/remove holdings; normalized weight warnings display; no persistence/no trade claim is visible. |
| `/optimize` | Optimizer handles success and insufficient history; frontier and assumptions render; rebalance tickets estimate shares/cash/warnings; no execution claim visible. |
| `/brokers` | Placeholder provider cards load; interest capture works; no real broker auth is implied. |
| `/billing` | Placeholder plan loads; checkout placeholder is clear; no payment processing is implied. |
| `/settings` | Placeholder actions are clear; demo user/auth state is visible; unavailable actions do not look broken. |
| `/admin` | Placeholder diagnostics are safe; no unsupported admin controls are exposed. |

## 12. Recommended frontend implementation order

1. `DataStatusBadge` / `FeatureDisabledState` / shared page states.
2. Market overview slice.
3. Dashboard bundle slice.
4. Upload improvements.
5. Holdings sector/data-quality improvements.
6. Analytics performance/risk slice.
7. Snapshots/changes.
8. Fundamentals.
9. Peers.
10. Advisor expansion.
11. Watchlist expansion.
12. Simulator.
13. Optimizer.
14. Rebalance tickets.

## Verification plan

Required checks for this documentation task:

1. Confirm only `docs/frontend-page-feature-map.md` is created or edited.
2. Run `git diff -- frontend/src backend` and confirm no frontend/backend implementation files changed.
3. Run `cd frontend && npm run build`.
4. Run `backend/.venv/bin/pytest backend/app/tests`.
5. Confirm every backend feature from `docs/backend-feature-registry.md` appears in the canonical backend feature to primary page table with exactly one primary page.
