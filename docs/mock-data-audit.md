# Mock Data Audit

Date: 2026-05-21

This audit searched backend and frontend code for: `mock`, `mock_india`, `demo`, `placeholder`, `fake`, `deterministic`, `seed_demo`, `sample`, `simulated`, `insufficient_history`, `provider-ready-mock`, `openai-ready-mock`, and `anthropic-ready-mock`.

No behavior or frontend UI changes were made.

## Executive Summary

P-insight is still materially dependent on mock, demo, or placeholder data for the parts of the product that require external systems.

- Runtime code and frontend code: 51 of 159 backend/app and frontend/src files contain one of the searched terms, about 32% by file count.
- Core CRUD/upload workflows are real local application workflows, but all authenticated user flows currently depend on the deterministic demo user until production auth exists.
- Market-priced workflows currently depend on deterministic market data by default. Local defaults use `mock_india`; hosted Render config still sets `MARKET_DATA_PROVIDER=mock`.
- AI advisor output is 100% deterministic mock text. OpenAI/Anthropic keys only change model metadata to `openai-ready-mock` or `anthropic-ready-mock`.
- Analytics summary, allocation, performance, concentration, and rules are calculated from holdings, but historical risk metrics are placeholders with `insufficient_history`.
- Broker connections and billing are placeholder surfaces. They collect/display state but do not perform real broker auth, broker sync, checkout, subscription management, or webhook processing.
- Frontend warning coverage exists for mock market-data providers on `/dashboard`, `/holdings`, `/analytics`, `/advisor`, and `/watchlist`, plus mock-source badges and mock-AI badges.

Overall mock-data proportion by capability: high. Six major capability areas are mock or placeholder dependent: market data, AI advisor, historical risk analytics, demo auth/seed, broker connections, and billing. Portfolio/holdings/upload/watchlist storage are real, but they inherit mock auth and mock prices when refreshed.

## Beta Position

Can stay for beta if clearly labeled and gated:

- Deterministic market data, only for internal/demo beta and never for investment-grade claims.
- Demo seed data, only behind demo/local mode.
- Mock AI responses, only with visible warning and no investment-advice positioning.
- Broker and billing placeholders, only as "coming soon" or waitlist/interest capture.
- Sample CSV templates and test fixtures.

Must be replaced before production:

- Demo auth with real user authentication and authorization.
- Default production market data provider with a real provider integration.
- Mock AI response generator with real provider calls or an explicit non-AI rule-based advisor mode.
- Historical risk placeholders with time-series price data and returns calculations.
- Billing placeholders with Stripe or the chosen billing provider.
- Broker placeholders with real broker OAuth/API flows, or remove broker-sync claims from production.

## Audit Inventory

### Market Data

| File path | Type of mock data | Required for | Can stay for beta? | Must replace later | Risk |
| --- | --- | --- | --- | --- | --- |
| `backend/app/modules/market_data/providers/mock_provider.py` | Deterministic USD and INR quotes, deterministic FX rates, mock company profiles, fixed `as_of=2026-01-01`, non-realtime source labels `mock` and `mock_india`. | Tests and local demo. Also current default runtime market data. | Yes for tests/local demo only, with warnings. | Real market data provider implementations, delayed/realtime source metadata, real company profiles, real FX. Keep a fixture provider only for tests. | High |
| `backend/app/modules/market_data/service.py` | Provider builder selects `MockProvider` or `MockProviderIndia`; all unsupported real providers route to stubs. | Runtime market data abstraction and tests. | Yes for beta only if deployment is explicitly demo/mock. | Production provider selection, provider health/readiness checks, real provider fallback rules. | High |
| `backend/app/modules/market_data/providers/india_placeholders.py` | Placeholder classes for Twelve Data, Alpha Vantage, Marketstack, future NSE/BSE/TrueData, and future broker data. They only check API keys and raise not-implemented errors. | Future provider extension points. | No for production data paths; yes as documented stubs. | Implement quote, batch, history, profile, and FX methods against the chosen India provider. | High |
| `backend/app/modules/market_data/providers/polygon_provider.py` | Polygon/Massive provider stub; raises not implemented after API-key check. | Future non-India provider extension. | No for production data paths. | Real Polygon/Massive implementation or remove provider option. | Medium |
| `backend/app/modules/market_data/providers/fmp_provider.py` | FMP provider stub; raises not implemented after API-key check. | Future non-India provider extension. | No for production data paths. | Real FMP implementation or remove provider option. | Medium |
| `backend/app/core/config.py` | Defaults `market_data_provider` and `indian_market_data_provider` to `mock_india`. | Local demo/test defaults. | Yes for local development. | Production-safe provider defaults and validation that production does not silently run on mock unless explicitly configured as demo. | High |
| `backend/.env.example` | Documents local `MARKET_DATA_PROVIDER=mock_india` and `INDIAN_MARKET_DATA_PROVIDER=mock_india`. | Local setup. | Yes, if labeled as local/demo. | Separate production example with real provider variables. | Low |
| `render.yaml` | Hosted backend config sets `MARKET_DATA_PROVIDER=mock`. | Deployment placeholder. | Only for a mock/demo deployment. | Real provider config before any production/beta users treat prices as real. | High |
| `backend/app/modules/health/router.py` | `/api/status` exposes `market_data_provider` and `ai_provider_mode` so the frontend can warn on mock providers. | Warning banners and diagnostics. | Yes. | Broader provider capability/readiness status after real providers exist. | Low |

### AI Advisor

| File path | Type of mock data | Required for | Can stay for beta? | Must replace later | Risk |
| --- | --- | --- | --- | --- | --- |
| `backend/app/modules/ai_advisor/service.py` | Deterministic `_mock_summary_response` and `_mock_question_response`; provider always returns `mock`; model metadata is `deterministic-advisor-v1`, `openai-ready-mock`, or `anthropic-ready-mock`. | Local demo, tests, advisor persistence workflow. | Yes only with visible "mock AI" labeling. | Real provider calls, prompt execution, safety/evaluation layer, error handling, provider metadata, usage limits. | High |
| `backend/app/core/config.py` | `ai_provider_mode` computed field always returns `mock`. | Frontend and status reporting. | Yes for current beta mock mode. | Real provider mode derived from configured provider and readiness. | High |
| `frontend/src/pages/AIAdvisorPage.tsx` | UI says responses use mock fallback and badges mock assistant responses. | Frontend warning banner/labeling. | Yes while mock AI exists. | Real provider labels and fallback/error states after backend AI integration. | Medium |
| `frontend/src/types/appStatus.ts` | Includes `ai_provider_mode` status field. | Frontend warning/labeling. | Yes. | May expand to richer provider status. | Low |

### Analytics And Risk

| File path | Type of mock data | Required for | Can stay for beta? | Must replace later | Risk |
| --- | --- | --- | --- | --- | --- |
| `backend/app/modules/analytics/calculators/risk.py` | Volatility, Sharpe ratio, and max drawdown return `value=null`, `status=insufficient_history`, and a placeholder message. Concentration risk is real. | Current analytics response shape and tests. | Yes if clearly labeled as unavailable. | Historical price ingestion, return series, benchmark/risk-free handling, volatility/Sharpe/drawdown calculations. | Medium |
| `backend/app/modules/analytics/schemas.py` | Risk metric status allows `insufficient_history`. | API contract for placeholder risk metrics. | Yes. | Keep status if still useful, but populate real metrics when history exists. | Low |
| `frontend/src/types/analytics.ts` | Mirrors `insufficient_history` risk status. | Frontend API typing. | Yes. | Keep or expand status once real historical analytics ship. | Low |
| `frontend/src/pages/DashboardPage.tsx` | Daily change and cash percentage are `N/A`; portfolio-history card is a visual placeholder; refreshed source badges warn on mock data. | UI placeholder and warning surface. | Yes for beta if expectations stay clear. | Real daily return, cash tracking, portfolio value history, and provider source metadata. | Medium |

### Demo Seed And Demo Auth

| File path | Type of mock data | Required for | Can stay for beta? | Must replace later | Risk |
| --- | --- | --- | --- | --- | --- |
| `backend/app/core/auth.py` | Deterministic development user `demo@p-insight.local`; creates the user on first authenticated request when demo mode is enabled. | Local demo and most backend tests. | Yes only in local/demo mode. | Supabase Auth, Clerk, or chosen production auth with per-user isolation. | High |
| `backend/app/core/config.py` | `demo_mode_enabled` is true when `APP_ENV=local` or `ENABLE_DEMO_MODE=true`. | Local demo gating. | Yes. | Production auth gate must not depend on demo mode. | High |
| `backend/app/modules/demo/service.py` | Deterministic India demo portfolio and 10 fixed holdings; seeds mock India prices through `MockProviderIndia`. | Local demo and demo tests. | Yes behind demo gating. | Optional sample-data importer that uses real prices or fixture-only data clearly separated from production users. | Medium |
| `backend/app/modules/demo/router.py` | `/api/demo/seed` endpoint gated by `require_demo_mode`. | Local demo seed. | Yes. | Keep only for demo environments or move behind admin/test tooling. | Medium |
| `backend/app/modules/demo/schemas.py` | Demo seed response contract. | Local demo API. | Yes. | Remove or keep in demo-only API surface. | Low |
| `backend/app/seed_demo.py` | CLI entry point for demo seeding. | Local demo. | Yes. | Replace with explicit fixture/demo script that cannot affect production. | Low |
| `backend/app/main.py` | Includes demo router in application. | Local demo route exposure. | Yes if router remains gated. | Environment-specific route registration or stricter production gating. | Medium |
| `Makefile` | `seed-demo` target runs `python -m app.seed_demo`. | Local demo convenience. | Yes. | Keep as local fixture command only. | Low |
| `README.md`, `backend/README.md`, `frontend/README.md` | Document demo seed and placeholder auth/demo mode. | Developer setup docs. | Yes. | Split local-demo docs from production deployment docs. | Low |
| `frontend/src/lib/env.ts` | Frontend demo mode is true for `VITE_APP_ENV=local` or `VITE_ENABLE_DEMO_MODE=true`. | Demo CTAs and placeholder controls. | Yes. | Production auth state should come from real auth/session provider. | Medium |
| `frontend/src/services/demoApi.ts`, `frontend/src/hooks/useDemoSeed.ts`, `frontend/src/types/demo.ts` | Frontend wiring for demo seed endpoint. | Local demo CTA. | Yes. | Remove from production bundle or hide behind explicit demo environment. | Low |
| `frontend/src/pages/LandingPage.tsx` | Demo seed CTA, "mock AI-powered explanations", and static "Mock shell" preview metrics. | Local demo/onboarding. | Yes for demo beta if labeled. | Real marketing copy and data-backed preview once production data exists. | Medium |
| `frontend/src/pages/OnboardingPage.tsx` | Copy says deterministic demo user; demo seed CTA. | Local demo onboarding. | Yes. | Real authenticated user onboarding. | Medium |
| `frontend/src/pages/AuthPages.tsx` | Placeholder login/signup form; no real session creation. | UI placeholder. | No for production user access. | Real auth forms/session handling. | High |
| `frontend/src/pages/SettingsPage.tsx` | Displays demo user and disabled account/preference/export/delete placeholders. | UI placeholder. | Partially; profile/demo user cannot represent real beta users. | Real profile, preferences, export, and account-deletion flows. | High |

### Frontend Warning Banners And Mock Labels

| File path | Type of mock data | Required for | Can stay for beta? | Must replace later | Risk |
| --- | --- | --- | --- | --- | --- |
| `frontend/src/components/layout/AppLayout.tsx` | Shows `DemoDataBanner` on `/dashboard`, `/holdings`, `/analytics`, `/advisor`, and `/watchlist` when provider is `mock` or `mock_india`. | Frontend warning banner. | Yes; should stay while any mock prices exist. | Replace with provider-specific data-quality banners after real providers exist. | Low |
| `frontend/src/components/ui/DemoDataBanner.tsx` | Warns that prices are simulated and unsuitable for investment decisions. | Frontend warning banner. | Yes. | Replace or narrow once real provider status is reliable. | Low |
| `frontend/src/components/ui/index.ts` | Re-exports `DemoDataBanner`. | UI plumbing. | Yes. | No replacement required unless component is removed. | Low |
| `frontend/src/pages/HoldingsPage.tsx` | Source badges highlight mock provider sources after refresh; input placeholders are examples only. | Warning labels and form examples. | Yes. | Real source metadata; placeholders can stay as UX examples. | Low |
| `frontend/src/pages/WatchlistPage.tsx` | Source badges highlight mock provider sources; form placeholders include sample symbols/names. | Warning labels and form examples. | Yes. | Real source metadata; placeholders can stay as UX examples. | Low |
| `frontend/src/components/layout/Header.tsx`, `frontend/src/components/ui/Input.tsx` | Generic UI placeholders/search placeholder styling. | UI examples only, not mock data dependency. | Yes. | No mock-data replacement required. | Low |
| `frontend/src/pages/PageScaffold.tsx`, `frontend/src/pages/AdminPage.tsx` | Generic "MVP placeholder" scaffold for deferred pages. | UI placeholder. | Yes if route remains non-critical. | Real admin diagnostics or remove page. | Low |

### Broker And Billing Placeholders

| File path | Type of mock data | Required for | Can stay for beta? | Must replace later | Risk |
| --- | --- | --- | --- | --- | --- |
| `backend/app/modules/broker_connections/service.py` | Static provider placeholders for Plaid, Zerodha, IBKR, Alpaca; creates `waitlist_interest` records with `is_placeholder=true`. | Beta interest capture. | Yes if labeled as coming soon. | Real broker provider models, OAuth/API flow, token storage, sync jobs, connection statuses. | Medium |
| `backend/app/modules/broker_connections/router.py` | `/providers` and `/connect-placeholder` endpoints. | Beta interest capture. | Yes if explicitly placeholder. | Real connection initiation/callback/sync endpoints or remove route. | Medium |
| `backend/app/modules/broker_connections/schemas.py` | `BrokerProviderPlaceholder` schema and coming-soon status. | API contract for placeholder providers. | Yes. | Real provider schema and lifecycle states. | Low |
| `frontend/src/services/brokerConnectionsApi.ts`, `frontend/src/hooks/useBrokerConnections.ts`, `frontend/src/types/brokerConnections.ts` | Frontend API wiring and types for placeholder broker providers and placeholder connection creation. | Beta interest capture. | Yes if labeled. | Real broker connection API wiring and types. | Medium |
| `frontend/src/pages/BrokerConnectionsPage.tsx` | Broker sync placeholder page and mark-interest flow. | UI placeholder/interest capture. | Yes if no real broker auth claim. | Real broker auth/sync UI or a removed/deferred broker section. | Medium |
| `backend/app/modules/billing/service.py` | Static plan options; plan status `placeholder`; checkout returns `coming_soon`; webhook acknowledges without Stripe processing. | Beta plan/usage preview. | Yes if no payments are accepted. | Stripe or chosen billing integration, checkout sessions, subscription persistence, webhook verification. | High |
| `frontend/src/pages/BillingPage.tsx` | Billing placeholder messaging and checkout placeholder button in demo mode. | UI placeholder. | Yes for non-paying beta. | Real checkout/subscription UX and error states. | High |

### Tests And Fixtures

| File path | Type of mock data | Required for | Can stay for beta? | Must replace later | Risk |
| --- | --- | --- | --- | --- | --- |
| `backend/app/tests/test_market_data.py` | Unit/API tests assert deterministic mock and mock India prices, fixed timestamps, deterministic unknown-symbol prices, and cached mock price rows. | Tests. | Yes. | Keep fixture tests; add real-provider contract tests with mocked HTTP responses when provider integration ships. | Low |
| `backend/app/tests/test_ai_advisor.py` | Tests assert provider `mock` and deterministic advisor response contents. | Tests. | Yes. | Keep deterministic advisor tests for fallback; add provider-call tests and safety tests. | Low |
| `backend/app/tests/test_analytics.py` | Tests assert `insufficient_history` for volatility while concentration is calculated. | Tests. | Yes. | Update once historical risk metrics are implemented; keep insufficient-history coverage for sparse data. | Low |
| `backend/app/tests/test_supporting_mvp_api.py` | Tests broker placeholders, billing placeholders, and demo seed portfolio/holdings/prices. | Tests. | Yes. | Keep placeholder tests while surfaces exist; add real broker/billing tests later. | Low |
| `backend/app/tests/test_demo_gating.py` | Tests production rejects demo auth and demo seed. | Tests. | Yes; important safety coverage. | Keep as regression coverage even after production auth exists, adapted to route shape. | Low |
| `backend/app/tests/test_health.py` | Tests status endpoint exposes `demo_mode_enabled`, `market_data_provider=mock_india`, and `ai_provider_mode=mock`. | Tests. | Yes. | Update expected provider status when real providers become default. | Low |
| `backend/app/tests/test_settings.py` | Tests default local mock/demo settings and production demo gating. | Tests. | Yes. | Update defaults when production-safe config validation is added. | Low |
| `docs/sample_india_portfolio.csv`, `docs/sample_portfolio.csv` | Sample holdings CSVs with Indian equities. | Local demo/manual upload fixtures. | Yes. | Keep as sample files; optionally regenerate with clearer fixture disclaimers. | Low |
| `frontend/src/pages/UploadPage.tsx` | Inline sample CSV template download. | UI fixture/template. | Yes. | Keep as upload template; not a production blocker. | Low |

## Removal Path

1. Auth first: replace `backend/app/core/auth.py` and frontend placeholder auth pages with real auth/session plumbing. Keep demo auth only behind explicit local/demo configuration.
2. Market data second: choose one India-capable provider, implement it behind `MarketDataProvider`, make production fail closed if configured to `mock` unintentionally, and retain `MockProviderIndia` only for tests/local demos.
3. AI advisor third: replace deterministic response generation with real provider calls, keep structured context builder, persist provider/model metadata accurately, and retain deterministic fallback only as a clearly labeled non-production mode.
4. Historical analytics fourth: persist or fetch historical prices, then calculate volatility, Sharpe ratio, max drawdown, daily change, and portfolio value history. Keep `insufficient_history` for genuinely sparse data.
5. Billing and broker integrations fifth: either implement real Stripe/broker flows or remove production claims/buttons for those surfaces. Placeholder waitlist capture can remain for a private beta if labeled.
6. Frontend warning refinement: keep global warnings while any provider is mock; after real providers are live, switch to provider freshness, delay, and data-quality warnings rather than generic demo warnings.

## Risk Summary

- High risk production blockers: mock market data defaults/provider stubs, mock AI advisor, deterministic demo auth, placeholder auth UI, billing checkout/webhooks.
- Medium risk beta blockers: historical risk placeholders, dashboard history/cash/daily placeholders, demo seed reliance, broker placeholders, landing-page mock preview claims.
- Low risk acceptable fixtures: sample CSVs, test-only deterministic data, visible warning banners, source badges, generic form placeholder text.
