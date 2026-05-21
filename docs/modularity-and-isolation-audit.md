# Modularity and Isolation Audit

Date: 2026-05-21

Scope: recently added or expanded backend feature modules under `backend/app/modules`, with frontend-readiness notes only. No product features or frontend files were added.

## Executive summary

The backend is moving in the intended modular-monolith direction. Most audited features live in their own `backend/app/modules/<feature>` folder with explicit `router.py`, `service.py`, and `schemas.py` boundaries. Routers are generally thin, larger calculations live in services or calculators, and portfolio-scoped services consistently call `PortfolioService.get_portfolio(..., user=...)` before reading portfolio data.

The integration risk is not broad coupling. The main risk is data provenance. Several newer analytics surfaces are feature-gated and contract-shaped, but still backed by deterministic mock or synthetic data: market history, performance history, risk v2, optimizer, fundamentals, peers, and AI advisor output. These are suitable for local/demo integration only when the frontend visibly labels mock/static/synthetic assumptions.

Verification status:

- Backend tests passed with bundled Python runtime: `193 passed in 8.61s`.
- Backend app import/startup check passed with bundled Python runtime: `app_import_ok routes=61`.
- Frontend build passed: `npm run build`.
- Repo `backend/.venv` is incomplete: `pytest` and `fastapi` are missing there. The passing backend verification used `/Users/dhruvtantia/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3`.
- Frontend build emitted only the existing Vite chunk-size warning for an 834.59 kB JS chunk.

## Pass/fail table by feature module

| Feature area | Module boundary | Contract quality | Feature flag | Mock/demo isolation | Auth/ownership | Tests | Overall |
|---|---|---|---|---|---|---|---|
| `common/data_status` | PASS: shared schema only | PASS: stable `source/provider/is_mock/is_stale/warning` fields | N/A | PASS | N/A | PASS | PASS |
| `market_overview` | PASS: router/service/schemas | PASS: `DataStatus` throughout | PASS: `ENABLE_MARKET_OVERVIEW` | PARTIAL: static India index definitions and mock-only movers are labeled | N/A: public market endpoint | PASS: schema/service/API | PASS with demo-data caveat |
| `dashboard` | PASS: router/service/schemas | PASS: frontend-friendly bundle and `DataStatus` | PASS: `ENABLE_DASHBOARD_BUNDLE` | PASS: derives status from latest price source | PASS: uses portfolio ownership | PASS: schema/service/API plus cross-user test | PASS |
| Upload mapping suggestions/import summary | PASS: inside `uploads` | PASS: explicit suggestion and import summary schemas | PARTIAL: suggestions gated by `ENABLE_UPLOAD_SUGGESTIONS`; import summary is core upload flow | PASS: no market mock dependency | PASS: upload job resolved through owned portfolio | PASS: upload, mapping, edge cases | PASS |
| Holdings sector metadata | PASS: inside `holdings` plus migration | PASS: `sector_source` and `sector_updated_at` exposed | N/A: metadata extension, not a standalone feature | PASS | PASS | PASS: create/update/upload coverage | PASS |
| Market history | PASS: inside `market_data` | PASS: stable historical schemas with `DataStatus` | PARTIAL: `/api/market/history` gated; legacy `/api/market-data/history/{symbol}` is not gated | PARTIAL: runtime service imports demo fixture for mock history | N/A: public market endpoint | PASS: contract/API/mock safety | PARTIAL |
| Performance | PASS: `performance` module | PASS: explicit assumptions and `DataStatus` | PASS: `ENABLE_PERFORMANCE_HISTORY` | PARTIAL: always uses mock historical response | PASS: uses portfolio ownership | PASS: service/API/ownership/edge cases | PARTIAL |
| Risk v2 | PASS: `risk` module plus calculators | PASS: metric status, assumptions, `DataStatus` | PASS: `ENABLE_RISK_V2` | PARTIAL: depends on synthetic performance history | PASS: ownership inherited through performance service | PARTIAL: API/calculators, no direct cross-user test | PARTIAL |
| Snapshots | PASS: `snapshots` module | PARTIAL: response is explicit but does not expose `source`/`DataStatus` even though payload stores `"source": "manual"` | PASS: `ENABLE_SNAPSHOTS` | PASS: no mock provider dependency | PASS: uses portfolio ownership | PARTIAL: API and empty portfolio, no explicit cross-user test | PASS with contract cleanup |
| Fundamentals | PASS: `fundamentals` module and provider interface | PASS: coverage, missing metrics, `DataStatus` | PASS: `ENABLE_FUNDAMENTALS` | PARTIAL: only mock provider exists; blocked outside local/test/demo/development | PASS for portfolio endpoint; asset endpoint is symbol-level | PASS: service/API/production block | PARTIAL |
| Peers | PASS: `peers` module | PASS: explicit static peer quality and warnings | PASS: `ENABLE_PEERS` | PARTIAL: static India peer map plus mock fundamentals | PASS: validates portfolio ownership before comparison | PARTIAL: API, no explicit cross-user test | PARTIAL |
| AI advisor context expansion | PASS: contained in `ai_advisor/context_builder.py` | PASS for persisted advisor response; optional context is internal dict | PARTIAL: optional blocks use underlying feature flags; advisor itself is not feature-gated | PARTIAL: deterministic mock AI remains the only provider | PASS: portfolio and conversation ownership enforced | PASS: context and mock response tests | PARTIAL |
| Simulator | PASS: `simulator` module | PARTIAL: explicit response, but no structured assumptions or `DataStatus` | PASS: `ENABLE_SIMULATOR` | PASS: no market mock dependency | PASS: uses portfolio ownership | PARTIAL: API only, no explicit cross-user test | PARTIAL |
| Optimizer | PASS: `optimizer` module | PASS: assumptions, `DataStatus`, warnings | PASS: `ENABLE_OPTIMIZER` | PARTIAL: always uses mock historical response | PASS: uses portfolio ownership | PARTIAL: API only, no direct service or cross-user test | PARTIAL |
| Rebalance | PASS: `rebalance` module | PARTIAL: warnings exist, but no structured assumptions/disclaimer or `DataStatus` | PASS: `ENABLE_REBALANCE_TICKETS` | PASS: uses current holdings only | PASS: uses portfolio ownership | PARTIAL: API only, no explicit cross-user test | PARTIAL |

## Critical blockers

1. Historical-data-backed features are not production-data-ready. `/api/market/history`, `/api/portfolios/{id}/performance/history`, `/api/portfolios/{id}/risk`, and `/api/portfolios/{id}/optimize` all rely on deterministic mock historical prices. They must not be integrated as real investment analytics.

2. Real AI is not implemented. `AIAdvisorService` returns deterministic mock responses even when OpenAI or Anthropic keys exist; keys only change model metadata to `openai-ready-mock` or `anthropic-ready-mock`.

3. Production auth is still demo-mode-gated rather than real user authentication. Portfolio ownership checks are correctly expressed through services, but production user isolation still depends on replacing the development auth placeholder.

## Medium-risk issues

| Issue | Impact | Evidence |
|---|---|---|
| `market_data.history_service` imports mock history from `app.modules.demo.fixtures.historical_prices` | Demo data is not fully isolated from production module code paths | `MarketHistoryService.build_mock_response(...)` imports `build_mock_historical_prices` from the demo module |
| Legacy price history endpoint is not covered by `ENABLE_HISTORICAL_DATA` | Frontend could call `/api/market-data/history/{symbol}` while the new historical feature is disabled | Only `/api/market/history` has the flag dependency |
| Router registration is unconditional | Disabled features remain visible in route table and fail at request time, not by route omission | `backend/app/main.py` includes all feature routers |
| Cross-user API tests are incomplete | Ownership is implemented by services, but regressions could slip in | Explicit cross-user tests exist for dashboard, performance, and core portfolios/holdings only |
| Simulator and rebalance outputs rely on prose warnings | Frontend cannot consume a stable assumptions/disclaimer object | `SimulationResponse` and `RebalanceTicketsResponse` have `warnings`, but no assumptions/disclaimer schema |
| Optional advisor context swallows all exceptions | Good for resilience, but can hide broken optional modules during development | `_safe_optional_block` catches `Exception` and returns `None` |
| Fundamentals provider is mock-only | Feature is correctly blocked outside local/test/demo/development, but there is no live provider path yet | `FundamentalsService._build_provider()` always returns `MockFundamentalsProvider` |

## Low-risk cleanup

- Add a small automated import-direction or circular-import smoke check. The current import graph showed no router-to-router imports and `create_app()` imports cleanly.
- Move mock historical price generation out of `demo.fixtures` into a clearly named market-data test/demo provider namespace.
- Add `source` to snapshot response summaries if the frontend needs to distinguish manual, upload, scheduled, or price-refresh snapshots.
- Add direct service tests for simulator, optimizer, rebalance, snapshots, peers, and risk service behavior.
- Add disabled-feature tests under `APP_ENV=production` to prove flags return `feature_disabled` before any mock provider construction or demo auth dependency.

## Mock-data leakage assessment

| File | Mock/static/demo data | Isolation assessment | Leakage risk |
|---|---|---|---|
| `backend/app/modules/market_data/providers/mock_provider.py` | Fixed USD/INR prices, mock profiles, deterministic FX/history points | Labeled with `DataStatus.mock_source`; blocked in production unless `ALLOW_PRODUCTION_MOCK_MARKET_DATA=true` | Medium: safe by default, risky if override is enabled |
| `backend/app/modules/demo/service.py` | Deterministic India demo portfolio and seeded mock prices | Demo router is gated by demo mode | Low to medium |
| `backend/app/modules/demo/fixtures/historical_prices.py` | Deterministic mock historical prices | Used by non-demo `market_data.history_service` | Medium |
| `backend/app/modules/fundamentals/providers/mock_fundamentals.py` | Mock fundamentals for a small symbol set | Blocked outside local/test/demo/development | Low to medium |
| `backend/app/modules/peers/static_peer_map.py` | Static India peer mapping | Feature-gated and response warnings say static | Low |
| `backend/app/modules/market_overview/service.py` | Static index definitions and mock-only mover symbols | Movers only used with mock providers; `DataStatus` included | Low |
| `backend/app/modules/ai_advisor/service.py` | Deterministic mock advisor responses | Production mock AI blocked unless `ALLOW_PRODUCTION_MOCK_AI=true` | Medium |
| `backend/app/modules/analytics/calculators/risk.py` | Legacy placeholder risk metrics | Status is `insufficient_history`; old analytics route remains available | Medium |
| `docs/sample_portfolio.csv` and `docs/sample_india_portfolio.csv` | Sample portfolio rows | Docs/sample path only | Low |
| `frontend/src/pages/UploadPage.tsx` | Example CSV text with RELIANCE/TCS | UI example text only | Low |

Production cannot silently use mock market data or mock AI with default production guardrails. However, explicit production override flags can allow mock market data and mock AI. That is acceptable for an intentional demo deployment, but it should be treated as unsafe for real users.

## Dependency graph summary

Observed direction is mostly healthy:

```text
common/data_status
market_data -> market_overview
market_data history -> performance -> risk
market_data history -> optimizer
portfolios -> holdings/uploads/analytics/dashboard/snapshots/simulator/rebalance
analytics calculators -> dashboard/snapshots
fundamentals -> peers
dashboard/performance/risk/fundamentals/peers/snapshots -> ai_advisor optional context
```

Notable dependency concerns:

- `market_data.history_service -> demo.fixtures.historical_prices` weakens mock/demo isolation.
- `ai_advisor.context_builder` intentionally depends on multiple feature services; it is resilient, but should stay one-way. No audited feature imports advisor.
- No audited router imports another router.
- No frontend types are imported by backend modules.

## Feature flag coverage summary

| Flag | Covered feature | Status |
|---|---|---|
| `ENABLE_MARKET_OVERVIEW` | `/api/market/overview` | Covered |
| `ENABLE_DASHBOARD_BUNDLE` | `/api/portfolios/{id}/dashboard` | Covered |
| `ENABLE_UPLOAD_SUGGESTIONS` | `/api/uploads/{id}/mapping-suggestions` | Covered for suggestions only |
| `ENABLE_HISTORICAL_DATA` | `/api/market/history` | Covered for new endpoint; legacy `/api/market-data/history/{symbol}` not covered |
| `ENABLE_PERFORMANCE_HISTORY` | `/api/portfolios/{id}/performance/history` | Covered |
| `ENABLE_RISK_V2` | `/api/portfolios/{id}/risk` | Covered |
| `ENABLE_SNAPSHOTS` | Snapshot create/list/compare | Covered |
| `ENABLE_FUNDAMENTALS` | Asset and portfolio fundamentals | Covered |
| `ENABLE_PEERS` | Peer comparison | Covered |
| `ENABLE_SIMULATOR` | Portfolio simulation | Covered |
| `ENABLE_OPTIMIZER` | Portfolio optimizer | Covered |
| `ENABLE_REBALANCE_TICKETS` | Rebalance tickets | Covered |

Disabled-feature behavior is tested for most new routes and returns clean `404 feature_disabled` errors. Startup still imports and registers all routers, so feature flags are request-time gates rather than route-registration gates.

## Test coverage gaps

Covered well:

- `common/data_status`
- market overview schema/service/API
- dashboard schema/service/API and one cross-user test
- upload parsing, mapping suggestions, validation, confirm summaries, duplicates, invalid rows
- holdings sector metadata create/update/upload behavior
- market history contract/API/mock production safety
- performance service/API, empty portfolio, missing prices, invalid ownership
- risk calculators and API
- fundamentals service/API and production mock block
- optimizer, simulator, rebalance API paths

Gaps:

- No explicit cross-user API tests for snapshots, risk v2, fundamentals portfolio endpoint, peers, simulator, optimizer, or rebalance.
- Risk v2 has calculator and API tests but no direct `RiskV2Service` unit tests with injected performance data.
- Optimizer, simulator, rebalance, snapshots, and peers are mostly API-tested, not service-tested.
- No production-environment disabled-feature request tests.
- No tests for live market-data/fundamentals providers because those providers are not implemented.
- No automated dependency-direction or circular-import regression test beyond app import smoke coverage.

## Frontend readiness table

| Backend endpoint | Readiness | Future frontend service | Future hook |
|---|---|---|---|
| `GET /api/market/overview` | Ready for demo/local UI with mock labels | `frontend/src/services/marketOverviewApi.ts` | `frontend/src/hooks/useMarketOverview.ts` |
| `GET /api/portfolios/{id}/dashboard` | Ready | `frontend/src/services/dashboardApi.ts` | `frontend/src/hooks/useDashboardBundle.ts` |
| `GET /api/uploads/{id}/mapping-suggestions` | Ready | extend `frontend/src/services/uploadApi.ts` | extend `frontend/src/hooks/useUpload.ts` or add `useUploadMappingSuggestions.ts` |
| `POST /api/uploads/{id}/confirm` import summary | Ready; likely already belongs in upload service | extend `frontend/src/services/uploadApi.ts` | extend `frontend/src/hooks/useUpload.ts` |
| Holdings sector metadata fields | Ready in existing holdings response | extend `frontend/src/services/holdingsApi.ts` types if needed | extend `frontend/src/hooks/useHoldings.ts` |
| `GET /api/market/history` | Contract ready, data mock-only | `frontend/src/services/marketHistoryApi.ts` | `frontend/src/hooks/useMarketHistory.ts` |
| `GET /api/portfolios/{id}/performance/history` | Demo-ready only; synthetic/mock history | `frontend/src/services/performanceApi.ts` | `frontend/src/hooks/usePerformanceHistory.ts` |
| `GET /api/portfolios/{id}/risk` | Demo-ready only; synthetic history | `frontend/src/services/riskApi.ts` | `frontend/src/hooks/useRiskV2.ts` |
| Snapshot create/list/compare | Ready, with possible source field cleanup later | `frontend/src/services/snapshotsApi.ts` | `frontend/src/hooks/useSnapshots.ts` |
| Asset/portfolio fundamentals | Demo-ready only; mock provider | `frontend/src/services/fundamentalsApi.ts` | `frontend/src/hooks/useFundamentals.ts` |
| `GET /api/portfolios/{id}/peers/{symbol}` | Demo-ready only; static peer set and mock fundamentals | `frontend/src/services/peersApi.ts` | `frontend/src/hooks/usePeerComparison.ts` |
| AI advisor optional context | Backend internal; existing advisor service/hook can continue | existing `frontend/src/services/aiApi.ts` | existing `frontend/src/hooks/useAIAdvisor.ts` |
| `POST /api/portfolios/{id}/simulate` | Ready as hypothetical tool, but add assumptions object later | `frontend/src/services/simulatorApi.ts` | `frontend/src/hooks/usePortfolioSimulation.ts` |
| `POST /api/portfolios/{id}/optimize` | Demo-ready only; mock history | `frontend/src/services/optimizerApi.ts` | `frontend/src/hooks/useOptimizer.ts` |
| `POST /api/portfolios/{id}/rebalance/tickets` | Usable after assumptions/disclaimer schema cleanup | `frontend/src/services/rebalanceApi.ts` | `frontend/src/hooks/useRebalanceTickets.ts` |

## Recommended next 10 tasks

1. Move mock historical price generation out of `backend/app/modules/demo/fixtures` into an explicit mock market-history provider namespace.
2. Decide whether `/api/market-data/history/{symbol}` should be deprecated, feature-gated, or folded into the new `/api/market/history` contract.
3. Add structured `assumptions` or `disclaimer` fields to rebalance and simulator responses.
4. Add explicit cross-user API tests for snapshots, risk, fundamentals portfolio endpoint, peers, simulator, optimizer, and rebalance.
5. Add production disabled-feature request tests for every feature flag.
6. Add direct service tests for risk v2, simulator, optimizer, rebalance, snapshots, and peers with injected dependencies where useful.
7. Add snapshot `source` to response summaries if frontend audit/history views need it.
8. Create a live historical market-data provider contract path before exposing performance, risk, or optimizer as real analytics.
9. Create a live fundamentals provider path before exposing fundamentals or peers as real investment data.
10. Keep frontend integration behind feature flags and visible mock/static/synthetic labels until real data providers and production auth are implemented.
