# P-insight Master Source of Truth

Last verified against repository state: 2026-05-21.

This document describes the current P-insight repository only. It is not a pitch deck, not a production-readiness claim, and not a future-state architecture. When a capability is planned but not implemented, it is marked as placeholder, future, UNKNOWN, or NEEDS VERIFICATION.

Primary source files inspected include `README.md`, `docs/*.md`, `backend/app/main.py`, `backend/app/core/*`, `backend/app/db/models.py`, `backend/app/modules/*`, `frontend/src/app/routes.tsx`, `frontend/src/pages/*`, `frontend/src/services/*Api.ts`, `frontend/src/hooks/*`, `backend/.env.example`, and `frontend/.env.example`.

## 1. Product Overview

P-insight is a portfolio analytics web application for uploading or manually entering investment holdings, validating portfolio data, reviewing backend-calculated analytics, and asking a mock AI advisor questions using structured portfolio context.

Target user: Indian retail investors who maintain holdings across Indian equities and ETFs and need a structured way to review value, allocation, concentration, missing data, and educational portfolio explanations.

Primary market: Indian retail investors. Current defaults and demo data are India-first: INR base currency, NSE/BSE symbol normalization, `NIFTY50` benchmark defaults, Indian sample CSVs, and deterministic Indian mock prices.

Core value proposition: turn local/manual holdings data into clear INR portfolio analytics and non-directive AI explanations while keeping market data, AI, broker, and billing secrets on the backend.

What the app currently does:

- Renders a React/Vite frontend with routes for landing, onboarding, dashboard, holdings, upload, analytics, AI advisor, watchlist, brokers, billing, settings, and admin in `frontend/src/app/routes.tsx`.
- Creates and lists portfolios through `/api/portfolios`.
- Adds, edits, deletes, and lists holdings through `/api/portfolios/{portfolio_id}/holdings`.
- Supports staged CSV/XLSX uploads through `/api/portfolios/{portfolio_id}/uploads`, `/api/uploads/{upload_job_id}/column-mapping`, `/validate`, `/confirm`, and `/errors`.
- Calculates portfolio summary, allocation, risk placeholders, performance, and rule insights in `backend/app/modules/analytics`.
- Refreshes deterministic mock prices from the backend market data layer and caches quotes in `asset_prices`.
- Seeds a deterministic Indian demo portfolio through `/api/demo/seed` and `python -m app.seed_demo`.
- Provides deterministic mock AI summaries/questions and persists conversations/messages.
- Exposes placeholder broker and billing surfaces.
- Shows a mock-data warning banner on key routes when the backend provider is `mock` or `mock_india`.

What the app does not yet do:

- No real production authentication.
- No real Indian market data provider integration.
- No real AI provider calls, even when keys exist.
- No broker sync or broker OAuth/token exchange.
- No Stripe checkout, payment collection, subscription enforcement, or webhook verification.
- No deployed production environment in this repo.
- No complete historical return series, benchmark comparison, volatility, Sharpe ratio, or max drawdown calculations.
- No mobile app.
- No tax optimization or trading execution.

## 2. Current Application Status

Local MVP status: implemented as a local/demo MVP with FastAPI, SQLite local fallback, deterministic demo user, mock Indian data, upload workflow, dashboard, analytics, and mock AI. It still needs smoother first-run verification and UI polish.

Internal demo status: usable for an internal India-first demo if local backend/frontend/migrations are running and `MARKET_DATA_PROVIDER=mock_india`. Manual browser QA is still required.

Private beta readiness: not ready as-is. The repo has private-beta checklists and deployment config, but production auth, user isolation, real provider decisions, legal language, observability, and deployment smoke tests are incomplete.

Production readiness: not production ready. Current auth is a demo placeholder, data providers and AI are mock/placeholder, billing is not live, and security/legal/operational hardening is incomplete.

Current scores:

| Area | Score / 100 | Rationale |
| --- | ---: | --- |
| Local MVP | 74 | Core local flows exist, tests exist, India demo exists, but local smoothness and manual QA still need work. |
| Internal demo | 65 | Demo portfolio, upload, dashboard, analytics, and mock AI can be shown, but the UI and runtime setup need verification. |
| Private beta | 42 | Deployment docs exist, but real auth/user isolation and beta hardening are not implemented. |
| Production | 18 | Architecture is pointed in the right direction, but critical production systems are placeholders. |

## 3. Target User Workflow

Intended current journey:

1. Open the landing page at `/`. The page states the India-first portfolio value proposition and offers onboarding, demo seed, or dashboard shell.
2. Create/access local demo or authenticated account later. Today `/login` and `/signup` are placeholder forms only when frontend demo mode is enabled; they navigate to onboarding and do not create real auth sessions.
3. Create a portfolio on `/onboarding` using defaults `base_currency=INR` and `benchmark_symbol=NIFTY50`.
4. Upload an Indian portfolio CSV/XLSX on `/upload`. The backend accepts `.csv` and `.xlsx` only.
5. Map columns to P-insight fields. Required fields are `symbol` and `quantity`; optional fields include `company_name`, `average_cost`, `market_value`, `currency`, `sector`, `asset_class`, and `exchange`.
6. Validate rows before holdings are created. Invalid rows remain staged in `upload_rows`.
7. Confirm import. Valid non-duplicate rows become holdings; invalid and duplicate rows are skipped with warnings.
8. Manually add/edit/delete holdings on `/holdings`.
9. Refresh mock Indian prices from `/holdings` or `/dashboard`. The backend refreshes holding `current_price` and inserts `asset_prices`.
10. View dashboard summary, allocation charts, top holdings, missing data, and active rule insights on `/dashboard`.
11. View deeper analytics tabs on `/analytics`.
12. Ask AI advisor questions on `/advisor`. Responses are deterministic mock text built from backend portfolio context.
13. Understand limitations through visible mock-data banners and placeholder messaging. The app must not be treated as investment advice.

## 4. Current Tech Stack

Backend:

- FastAPI: app factory in `backend/app/main.py`.
- Python: dependencies in `backend/requirements.txt`.
- Pydantic and pydantic-settings: schemas and config in `backend/app/modules/*/schemas.py` and `backend/app/core/config.py`.
- SQLAlchemy ORM: models/session in `backend/app/db/models.py` and `backend/app/db/session.py`.
- Alembic: migrations in `backend/alembic/versions`.
- PostgreSQL target: default `DATABASE_URL` in config points to PostgreSQL.
- SQLite local fallback: `backend/.env.example` and docs set `DATABASE_URL=sqlite:///./p_insight_local.db`.
- pytest: tests under `backend/app/tests`.
- openpyxl: XLSX parsing in `backend/app/modules/uploads/service.py`.

Frontend:

- React 18, TypeScript, Vite.
- Tailwind CSS via `frontend/tailwind.config.js` and `frontend/src/styles.css`.
- TanStack Query in `frontend/src/hooks/*`.
- React Hook Form and Zod in onboarding, auth, and holdings forms.
- Recharts in dashboard and analytics pages.
- lucide-react for icons.

Deployment target:

- Frontend: Vercel later; config in `frontend/vercel.json`.
- Backend: Render/Railway later; `render.yaml` and `backend/Procfile`.
- Database: Supabase Postgres later; documented in `docs/deployment.md`.

## 5. Repository Structure

- `backend/`: FastAPI application, Alembic migrations, backend tests, seed script, requirements, deployment process file.
- `frontend/`: React/Vite application, service clients, hooks, pages, components, package metadata, Vercel config.
- `docs/`: product, architecture, API, environment, local development, deployment, checklists, known issues, sample CSV files.
- `backend/app/core`: config, demo auth dependency, exception handling, JSON helpers, logging.
- `backend/app/db`: SQLAlchemy base, session factory, ORM models.
- `backend/app/modules`: domain modules for health/status, portfolios, holdings, uploads, market data, analytics, AI advisor, watchlist, broker connections, billing, usage, and demo seed.
- `frontend/src/app`: app provider setup and React Router configuration.
- `frontend/src/pages`: route-level screens and workflow composition.
- `frontend/src/components`: layout and reusable UI primitives.
- `frontend/src/services`: API client and typed backend endpoint wrappers.
- `frontend/src/hooks`: TanStack Query hooks and mutations that connect pages to services.
- `frontend/src/types`: TypeScript interfaces mirroring backend response/request shapes.

## 6. Backend Architecture

The backend is a modular monolith. `backend/app/main.py` creates one FastAPI app and includes routers from all modules.

Routers:

- Health/status: `backend/app/modules/health/router.py`
- Portfolios: `backend/app/modules/portfolios/router.py`
- Holdings: `backend/app/modules/holdings/router.py`
- Uploads: `backend/app/modules/uploads/router.py`
- Market data: `backend/app/modules/market_data/router.py`
- Analytics: `backend/app/modules/analytics/router.py`
- AI advisor: `backend/app/modules/ai_advisor/router.py`
- Watchlist: `backend/app/modules/watchlist/router.py`
- Broker placeholders: `backend/app/modules/broker_connections/router.py`
- Billing placeholders: `backend/app/modules/billing/router.py`
- Demo seed: `backend/app/modules/demo/router.py`

Services own business behavior. Examples: `PortfolioService`, `HoldingService`, `UploadService`, `MarketDataService`, `AnalyticsService`, `AIAdvisorService`, `BillingService`, and `BrokerConnectionService`.

Repositories are used where persistence operations are more than trivial: portfolios, holdings, uploads, and AI advisor all have repository files.

Schemas live per module and define request/response contracts with Pydantic.

Database models live centrally in `backend/app/db/models.py`. This keeps the current monolith simple while modules own API/service behavior.

Config management is in `backend/app/core/config.py`. Settings are loaded from `.env`, include computed CORS origins, compute `demo_mode_enabled`, and force `ai_provider_mode` to `"mock"`.

Auth placeholder: `backend/app/core/auth.py` defines `get_development_user`. It creates/returns `demo@p-insight.local` only when `demo_mode_enabled` is true. If not, it raises a permission error.

Demo mode gating:

- `demo_mode_enabled` is true when `APP_ENV=local` or `ENABLE_DEMO_MODE=true`.
- `/api/demo/seed` has `require_demo_mode`.
- The deterministic development user is also blocked outside demo mode.

Market data abstraction:

- `MarketDataService._build_provider` selects provider from `MARKET_DATA_PROVIDER`.
- Implemented deterministic providers: `mock` and `mock_india`.
- Placeholder providers: Twelve Data, Alpha Vantage, Marketstack, NSE/BSE/TrueData future, broker future, Polygon/Massive, and FMP. These return provider errors or require keys but do not fetch real data.

Analytics engine:

- `backend/app/modules/analytics/service.py` builds a bundle from current holdings.
- Calculators under `backend/app/modules/analytics/calculators` compute summary, allocation, concentration, performance, and rules.
- Historical risk metrics are placeholders with `insufficient_history`.

AI advisor module:

- `AIAdvisorContextBuilder` builds structured context.
- `AIAdvisorService` generates deterministic mock responses and persists conversations/messages.
- Provider keys only alter mock metadata; no real OpenAI/Anthropic call is made.

Upload module:

- `UploadService` parses CSV/XLSX, stages upload jobs/rows, applies mapping, validates rows, confirms import, and skips duplicates.

Broker placeholder:

- `BrokerConnectionService` lists placeholder providers and stores waitlist-interest records only.

Billing placeholder:

- `BillingService` returns Free/Pro/Premium Later plan surfaces, usage snapshot, and coming-soon checkout/webhook responses.

## 7. Frontend Architecture

Routes are defined in `frontend/src/app/routes.tsx` under a shared `AppLayout`.

App shell:

- `frontend/src/components/layout/AppLayout.tsx` renders sidebar, header, main content, and mock-data warning banner.
- `Sidebar.tsx` exposes all product areas.
- `Header.tsx` shows page title, search input shell, feedback link if configured, and login/signup links.

API client:

- `frontend/src/services/apiClient.ts` centralizes fetch calls, JSON handling, FormData handling, and API errors.
- `VITE_API_BASE_URL` is the only backend origin config used by the client.

Hooks:

- `usePortfolios`, `useHoldings`, `useUpload`, `useAnalytics`, `usePortfolioPrices`, `useAIAdvisor`, `useWatchlist`, `useBrokerConnections`, `useBilling`, `useAppStatus`, and `useDemoSeed` wrap backend APIs with TanStack Query.

Page-level responsibilities:

- `LandingPage`: product entry point and demo seed CTA.
- `OnboardingPage`: creates INR/NIFTY50 portfolio and can seed the demo.
- `DashboardPage`: first portfolio summary, refresh prices, charts, top holdings, insights, missing data.
- `HoldingsPage`: manual CRUD, filtering, refresh prices.
- `UploadPage`: CSV/XLSX staged upload wizard.
- `AnalyticsPage`: overview, allocation, risk, performance, rules tabs.
- `AIAdvisorPage`: context panel, question form, generated summary, conversation history.
- `BrokerConnectionsPage`: provider placeholders and mark-interest flow.
- `BillingPage`: placeholder plan/usage surface.
- `AuthPages`: placeholder login/signup only; no real session.
- `SettingsPage` and `AdminPage`: deferred shells.

Loading/error/empty states:

- Reusable components are in `frontend/src/components/ui/PageState.tsx`.
- Most pages handle loading, API errors, and empty portfolio/holding states explicitly.

Mock-data warning banner:

- `DemoDataBanner` displays: "Demo data: prices are simulated and not suitable for investment decisions."
- `AppLayout` shows it on `/dashboard`, `/holdings`, `/analytics`, `/advisor`, and `/watchlist` when `/api/status` reports provider `mock` or `mock_india`.

India-first UI assumptions:

- Portfolio creation defaults to INR and NIFTY50.
- Manual holding form defaults currency to INR.
- Upload sample template uses `RELIANCE` and `TCS`.
- Dashboard and analytics format currency from portfolio base currency.

## 8. Data Model

All major ORM entities are defined in `backend/app/db/models.py`.

### User

Purpose: owner identity for portfolios, subscriptions, usage, watchlist, and broker connections. Currently populated by demo auth.

Important fields: `id`, `email`, `display_name`, timestamps.

Relationships: has many portfolios, subscriptions, feature usage rows, watchlist items, broker connections.

### Portfolio

Purpose: user-owned portfolio container and base unit for holdings, analytics, uploads, AI, and broker account linkage.

Important fields: `id`, `user_id`, `name`, `base_currency`, `benchmark_symbol`, `risk_free_rate`, timestamps.

Relationships: belongs to user; has many holdings, portfolio snapshots, analytics results, AI conversations, upload jobs, watchlist items, broker accounts.

### Holding

Purpose: normalized position in a portfolio.

Important fields: `id`, `portfolio_id`, `symbol`, `company_name`, `quantity`, `average_cost`, `current_price`, `currency`, `sector`, `asset_class`, `exchange`, timestamps.

Relationships: belongs to portfolio. It intentionally does not contain broker-specific fields.

### Asset

Purpose: symbol-level metadata and anchor for cached prices.

Important fields: `id`, `symbol`, `company_name`, `currency`, `sector`, `asset_class`, `exchange`, timestamps.

Relationships: has many asset prices.

### AssetPrice

Purpose: cached quote records inserted by market data calls and demo seed.

Important fields: `id`, `asset_id`, `symbol`, `price`, `currency`, `source`, `as_of`, `is_realtime`, timestamps.

Relationships: optionally belongs to an asset.

### UploadJob

Purpose: staged upload batch before import into holdings.

Important fields: `id`, `portfolio_id`, `filename`, `status`, `total_rows`, `valid_rows`, `invalid_rows`, `column_mapping_json`, timestamps.

Relationships: belongs to portfolio; has many upload rows.

### UploadRow

Purpose: individual staged row with raw/mapped data and validation status.

Important fields: `id`, `upload_job_id`, `row_number`, `raw_data_json`, `mapped_data_json`, `validation_errors_json`, `status`, timestamps.

Relationships: belongs to upload job. Indexed by upload job and row number.

### AnalyticsResult

Purpose: persisted analytics snapshots created by `/api/portfolios/{portfolio_id}/analytics/recalculate`.

Important fields: `id`, `portfolio_id`, `result_type`, `result_json`, `generated_at`, timestamps.

Relationships: belongs to portfolio.

### AIConversation

Purpose: persisted AI advisor conversation shell for a portfolio.

Important fields: `id`, `portfolio_id`, `title`, `context_json`, timestamps.

Relationships: belongs to portfolio; has many AI messages.

### AIMessage

Purpose: persisted system/user/assistant messages for each AI conversation.

Important fields: `id`, `conversation_id`, `role`, `content`, `provider`, `model`, `metadata_json`, timestamps.

Relationships: belongs to AI conversation.

### Subscription

Purpose: placeholder subscription record for future billing.

Important fields: `id`, `user_id`, `plan_tier`, `status`, `provider`, `provider_subscription_id`, timestamps.

Relationships: belongs to user.

### FeatureUsage

Purpose: future feature usage tracking and plan enforcement basis.

Important fields: `id`, `user_id`, `feature`, `usage_count`, `period`, `metadata_json`, timestamps.

Relationships: belongs to user.

### WatchlistItem

Purpose: symbol watchlist outside current holdings.

Important fields: `id`, `user_id`, `portfolio_id`, `symbol`, `note`, timestamps.

Relationships: belongs to user; optionally belongs to portfolio.

Note: API schema refers to `notes` in docs, while ORM field is `note`. NEEDS VERIFICATION in the UI/API behavior before external documentation.

### BrokerConnection

Purpose: placeholder user-level broker connection or interest record.

Important fields: `id`, `user_id`, `provider`, `status`, `external_connection_id`, `metadata_json`, timestamps.

Relationships: belongs to user; has many broker accounts.

### BrokerAccount

Purpose: future broker account normalized under a broker connection and optionally linked to a portfolio.

Important fields: `id`, `broker_connection_id`, `portfolio_id`, `account_name`, `account_type`, `external_account_id`, `status`, `metadata_json`, timestamps.

Relationships: belongs to broker connection; optionally belongs to portfolio.

Additional entity present: `PortfolioSnapshot` exists for future historical snapshots but is not one of the requested major entities and is not actively surfaced in current workflows.

## 9. India-Market Design

INR default:

- `Portfolio.base_currency` defaults to `INR`.
- `Holding.currency` defaults to `INR`.
- `backend/.env.example` sets `MARKET_DATA_PROVIDER=mock_india`.
- Frontend onboarding and holding forms default to INR.

NSE/BSE exchange handling:

- `backend/app/modules/market_data/symbols.py` normalizes Indian symbols.
- Prefixes `NSE:` and `BSE:` are recognized.
- `.NS` and `.BO` suffixes are recognized.
- Numeric symbols default to BSE handling.
- Unknown/non-prefixed symbols default to NSE unless another valid default exchange is supplied.

Indian ticker examples:

- Equities: `RELIANCE`, `TCS`, `INFY`, `HDFCBANK`, `ICICIBANK`, `SBIN`, `ITC`, `LT`, `BHARTIARTL`.
- ETF: `NIFTYBEES`.
- Benchmarks: `NIFTY50`, `NIFTY`, `BANKNIFTY`.
- Provider examples: `RELIANCE.NS`, `^NSEI`, `BSE:500325`.

NIFTY50 benchmark assumption:

- Onboarding defaults `benchmark_symbol` to `NIFTY50`.
- Demo seed creates `Demo India Portfolio` with `benchmark_symbol="NIFTY50"` and `risk_free_rate=0.065`.

Symbol normalization rules:

- Whitespace is trimmed and symbols are uppercased.
- `NIFTY50`, `NIFTY 50`, and `NIFTY` map to normalized `NIFTY50` and provider `^NSEI`.
- `BANKNIFTY` and `BANK NIFTY` map to provider `^NSEBANK`.
- Known equities map to provider symbols like `RELIANCE.NS`.
- `.NS`/`.BO` suffixes are stripped from normalized symbol.
- Provider symbols like `RELIANCE.NS` map back to normalized `RELIANCE`.
- Asset class is derived as `Index` for index symbols, `ETF` for symbols ending in `BEES`, otherwise `Equity`.

Current mock Indian data behavior:

- `MockProviderIndia` returns INR quotes with source `mock_india` and fixed `as_of=2026-01-01T00:00:00Z`.
- Known Indian symbols have deterministic fixed prices.
- Unknown symbols receive deterministic pseudo-prices based on a hash.
- Mock provider company profiles include sectors for common India demo symbols.

Future real provider strategy:

- Keep all provider keys and calls on the backend.
- Add a real implementation behind the existing `MarketDataProvider` interface.
- Preserve normalized internal symbols and provider-specific mapping at the boundary.
- Label source and realtime/delayed status in all quotes.
- Keep `asset_prices` cache behavior.

Env vars needed for Indian market APIs:

- `MARKET_DATA_PROVIDER`
- `INDIAN_MARKET_DATA_PROVIDER`
- `MARKET_DATA_API_KEY`
- `TWELVE_DATA_API_KEY`
- `ALPHA_VANTAGE_API_KEY`
- `MARKETSTACK_API_KEY`
- Potential future provider-specific keys for NSE/BSE/TrueData.

## 10. Market Data Layer

Current mock provider:

- `MockProvider` in `backend/app/modules/market_data/providers/mock_provider.py` serves deterministic USD quotes for US symbols.
- `MockProviderIndia` serves deterministic INR quotes for Indian symbols.

`mock_india` provider:

- Implemented and default in backend config and `.env.example`.
- Source label is `mock_india`.
- Currency is `INR`.
- Default exchange is `NSE`.

Source labeling:

- Every `PriceQuote` includes `source`, `as_of`, and `is_realtime`.
- Frontend shows source badges after refresh and warning banners for mock sources.

Price refresh flow:

1. Frontend calls `POST /api/portfolios/{portfolio_id}/prices/refresh`.
2. `MarketDataService.refresh_portfolio_prices` verifies portfolio ownership through `PortfolioService`.
3. Holdings symbols are normalized and deduplicated.
4. Provider returns batch quotes.
5. Each holding `current_price` is updated.
6. Each quote is cached in `asset_prices`.
7. Response includes refreshed holding items and quote source labels.

`asset_prices` cache:

- Latest price and batch price calls insert `AssetPrice` rows.
- Refresh calls also insert `AssetPrice` rows.
- There is no cache eviction, latest-price selection API, or price history built from cached rows yet.

Future providers listed in code/docs:

- Twelve Data: placeholder `TwelveDataProvider`.
- Alpha Vantage: placeholder `AlphaVantageProvider`.
- Marketstack: placeholder `MarketstackProvider`.
- NSE/BSE/TrueData future: placeholder `NseBseProvider`.
- Polygon/Massive and FMP also exist as placeholders for non-India or future use.
- Broker-provided market data: placeholder `BrokerMarketDataProvider`.

Not yet implemented:

- Real external quote HTTP calls.
- Real delayed/realtime Indian market provider.
- Provider rate limiting, retry, backoff, or quota handling.
- Corporate actions.
- Dividends/splits.
- Historical portfolio performance from market history.
- Frontend direct provider calls. This must remain disallowed.

## 11. Upload Workflow

CSV/XLSX upload:

- `UploadService.create_upload` reads a FastAPI `UploadFile`.
- `parse_upload_rows` accepts `.csv` and `.xlsx` only.
- CSV parsing uses `csv.DictReader` with `utf-8-sig`.
- XLSX parsing uses `openpyxl.load_workbook(..., read_only=True, data_only=True)` and the active sheet.

`upload_jobs`:

- One row per uploaded file/batch.
- Tracks status, filename, row counts, and column mapping JSON.

`upload_rows`:

- One row per parsed file row.
- Stores raw data, mapped data, validation errors, and row status.

Column mapping:

- API: `POST /api/uploads/{upload_job_id}/column-mapping`.
- Mapping is from P-insight target field to source column.
- Supported fields: `symbol`, `company_name`, `quantity`, `average_cost`, `market_value`, `currency`, `sector`, `asset_class`, `exchange`.
- Required fields: `symbol`, `quantity`.
- Unknown target fields and missing source columns are rejected.

Validation:

- API: `POST /api/uploads/{upload_job_id}/validate`.
- `symbol` is required and normalized with India symbol logic.
- `quantity` is required and must be positive.
- `average_cost` and `market_value` cannot be negative.
- `current_price` is derived as `market_value / quantity` when possible.
- `currency` defaults to portfolio base currency or INR.
- `asset_class` and `exchange` fall back to symbol metadata when available.

Confirm import:

- API: `POST /api/uploads/{upload_job_id}/confirm`.
- Upload must have status `validated`.
- Valid rows are imported into holdings.
- Invalid rows are not imported.

Duplicate symbol behavior:

- Existing portfolio symbols are skipped.
- Repeated symbols within the same upload are skipped after the first importable occurrence.
- Skips are warnings and make response status `partial_imported`.
- Merge/update behavior is not implemented.

Invalid row behavior:

- Invalid rows stay in `upload_rows`.
- Confirm response reports `invalid_rows`.
- Invalid rows cause `partial_imported` when at least one row imports.

Indian CSV expectations:

- Current UI template uses columns: `Ticker`, `Name`, `Shares`, `Average Cost`, `Market Value`, `Currency`, `Sector`, `Asset Class`, `Exchange`.
- Sample docs include `docs/sample_india_portfolio.csv` and `docs/sample_portfolio.csv`.
- Expected symbols are normalized NSE/BSE symbols such as `RELIANCE`, `TCS`, `NSE:INFY`, or BSE codes when needed.

## 12. Portfolio and Holdings Workflow

Create portfolio:

- Frontend: `OnboardingPage`.
- Backend: `POST /api/portfolios`.
- Defaults: base currency INR; benchmark symbol can be normalized to `NIFTY50`.

Add holding:

- Frontend: `HoldingsPage` form.
- Backend: `POST /api/portfolios/{portfolio_id}/holdings`.
- Backend normalizes symbol, exchange, and asset class.

Edit holding:

- Frontend: edit row from holdings table.
- Backend: `PATCH /api/portfolios/{portfolio_id}/holdings/{holding_id}`.
- If symbol changes, it is re-normalized.

Delete holding:

- Frontend: delete action with browser confirmation.
- Backend: `DELETE /api/portfolios/{portfolio_id}/holdings/{holding_id}`.

List holdings:

- Frontend: holdings table with search and sector filter.
- Backend: `GET /api/portfolios/{portfolio_id}/holdings`.

Current calculations:

- Holding response computed fields: `market_value = quantity * current_price` when price exists.
- Holding response computed fields: `unrealized_gain_loss = quantity * (current_price - average_cost)` when both values exist.
- Analytics recalculates portfolio-level cost, value, gain/loss, allocation, and rules from backend holdings.

INR display expectations:

- Frontend uses `Intl.NumberFormat` with the holding or portfolio currency.
- India demo and defaults should display INR.
- Mixed-currency conversion is not implemented; currency exposure is bucketed, not converted.

## 13. Analytics Workflow

Total value:

- Sum of holding `market_value` where `current_price` exists.
- Missing prices contribute zero to total value.

Cost basis:

- Per holding: `quantity * average_cost` when `average_cost` exists.
- Portfolio total: sum of known cost bases.

Unrealized gain/loss:

- Per holding: `quantity * (current_price - average_cost)` when both values exist.
- Portfolio total: sum of known gain/loss values.

Allocation:

- Asset allocation, sector allocation, and currency exposure are calculated from priced holdings only.
- Missing `asset_class`, `sector`, or `currency` use fallback bucket names.

Concentration rules:

- Concentration risk uses priced holdings.
- `HIGH_CONCENTRATION`: largest holding weight greater than 25%.
- `MODERATE_CONCENTRATION`: largest holding weight greater than 15%.
- Risk status from concentration calculator can be `empty`, `ok`, `moderate`, or `high`.

Missing data rules:

- `MISSING_PRICE_DATA`: holdings without `current_price`.
- `MISSING_COST_BASIS`: holdings without `average_cost`.

Currency exposure:

- `CURRENCY_EXPOSURE`: non-base currency exposure greater than 20% of priced portfolio value.
- No FX conversion currently happens.

Risk metrics placeholders:

- Volatility, Sharpe ratio, and max drawdown return `value=null`, `status=insufficient_history`, and a message that historical price data is unavailable.

What is deterministic:

- Summary, allocation, concentration, performance, and rules are deterministic functions of current holdings.
- Mock prices are deterministic.
- AI context is deterministic from portfolio and analytics data.

What is not yet real because history is missing:

- Daily change.
- Historical portfolio value.
- Volatility.
- Sharpe ratio.
- Max drawdown.
- Benchmark-relative performance.
- Time-weighted or money-weighted returns.

## 14. AI Advisor Workflow

Structured context builder:

- `backend/app/modules/ai_advisor/context_builder.py` builds portfolio summary, holdings, risk metrics, allocation, rule insights, price freshness, and user question.
- AI uses backend analytics context, not frontend-computed analytics.

Summary endpoint:

- `POST /api/portfolios/{portfolio_id}/ai/summary`.
- Persists a conversation and system/user/assistant messages.

Question endpoint:

- `POST /api/portfolios/{portfolio_id}/ai/question` with `question`.
- Persists a separate conversation and messages.

Mock response behavior:

- `AIAdvisorService._provider_metadata` always returns provider `mock`.
- With OpenAI key set, model metadata becomes `openai-ready-mock`.
- With Anthropic key set, model metadata becomes `anthropic-ready-mock`.
- Without keys, model is `deterministic-advisor-v1`.
- No real model call is made.

AI safety wording:

- Responses are educational and framed as "Based on the provided data".
- The service replaces banned phrases including `buy this`, `sell this`, `guaranteed return`, and `this will outperform`.

Future real AI integration:

- Add backend-only provider call after context building.
- Keep prompts and guardrails server-side.
- Store provider/model metadata.
- Keep no AI keys in frontend.
- Add stronger financial-advice safety review before beta/prod.

What AI should say:

- Explain portfolio concentration, missing data, allocation, and limitations.
- Use cautious language: "suggests", "review", "compare", "may want to".
- Clearly identify when analysis is limited by mock data or missing prices/history.

What AI should not say:

- Direct buy/sell instructions.
- Guaranteed outcomes.
- Claims of outperformance certainty.
- Personalized legal/tax advice.
- Real-time market claims while data is mock.

## 15. Auth and User Isolation

Current demo auth:

- `CurrentUser` depends on `get_development_user` in `backend/app/core/auth.py`.
- The development user is deterministic: `demo@p-insight.local`.
- User is created on first authenticated request when demo mode is enabled.

Production demo gating:

- Demo auth works only when `APP_ENV=local` or `ENABLE_DEMO_MODE=true`.
- Outside demo mode, authenticated API dependencies raise permission errors.
- `/api/demo/seed` is separately gated with `require_demo_mode`.

Why production auth is not ready:

- No real login session validation.
- No Supabase/Clerk JWT verification.
- No frontend auth client.
- No passwordless/OAuth flow.
- No user onboarding tied to real identity.
- Hosted beta with `APP_ENV=production` and `ENABLE_DEMO_MODE=false` would block current user-dependent APIs until real auth is implemented.

Future Supabase Auth plan:

- Use Supabase Auth or Clerk; the repo has not chosen one.
- Backend should verify JWTs server-side.
- Backend should map auth subject/email to `users`.
- Frontend should store only public anon keys.
- Supabase service role key must remain backend-only.

User isolation requirements:

- Every portfolio query must filter by current user.
- Holdings, uploads, analytics, AI conversations, broker connections, watchlist, subscription, and usage must be scoped to current user through owned portfolio or direct `user_id`.
- Demo user must never be used for real production users.

## 16. Broker Integration Plan

Current state:

- Placeholder only.
- APIs exist for listing providers, creating placeholder interest, listing connections, and deleting connections.
- No broker OAuth, API token exchange, holdings sync, transaction sync, or account refresh exists.

Future providers:

- Zerodha: important India-first candidate.
- Dhan: mentioned in roadmap requirement but not currently present in code. Add when prioritizing India broker sync.
- Angel One: mentioned in roadmap requirement but not currently present in code. Add when prioritizing India broker sync.
- Interactive Brokers/IBKR: current placeholder provider and relevant for advanced/global portfolios.
- Plaid and Alpaca are also current placeholders, but they are not India-first.

Holdings normalization:

- Broker-specific fields must stay out of `Holding`.
- Broker account metadata belongs in `BrokerConnection`/`BrokerAccount`.
- Synced positions should normalize to the same internal `Holding` model as manual/upload imports.

Why broker sync is not MVP:

- Manual upload must stabilize first.
- Broker API coverage, consent, token storage, refresh scheduling, reconciliation, duplicate handling, and compliance requirements add high complexity.
- India market value can be demonstrated with upload and mock prices before broker integration.

## 17. Billing and Freemium Plan

Current placeholder state:

- `GET /api/billing/plan` returns plan options and usage snapshot.
- `POST /api/billing/create-checkout-session` returns coming soon.
- `POST /api/billing/webhook` acknowledges placeholder receipt only.
- No Stripe checkout or webhook verification is implemented.

Free:

- Current plan default.
- Features shown: one portfolio, manual upload, basic analytics, limited AI questions, delayed price refresh.

Pro:

- Coming soon.
- Intended features: multiple portfolios, advanced analytics, more AI questions, export reports later, faster price refresh.

Premium Later:

- Later tier.
- Intended features: broker sync, weekly AI reports, mobile alerts, advanced diagnostics.

Feature usage tracking:

- `FeatureUsage` table exists.
- `FeatureUsageSnapshotService` reports current portfolio count, holdings count, and AI conversation count.
- Enforcement is disabled.

Why Stripe is not wired yet:

- Product limits and auth identity are not finalized.
- Real subscriptions require production auth, secure webhooks, hosted environment, plan enforcement, and billing/legal copy.

## 18. Environment Variables

Backend local required:

```bash
APP_ENV=local
ENABLE_DEMO_MODE=false
DATABASE_URL=sqlite:///./p_insight_local.db
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
MARKET_DATA_PROVIDER=mock_india
INDIAN_MARKET_DATA_PROVIDER=mock_india
```

Backend beta required:

```bash
APP_NAME=P-insight
APP_ENV=production
SERVICE_NAME=p-insight-backend
ENABLE_DEMO_MODE=false
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:PORT/postgres
FRONTEND_URL=https://your-vercel-app.vercel.app
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=
JWT_SECRET=
MARKET_DATA_PROVIDER=mock_india
```

Backend future optional:

```bash
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
MARKET_DATA_API_KEY=
POLYGON_API_KEY=
FMP_API_KEY=
TWELVE_DATA_API_KEY=
ALPHA_VANTAGE_API_KEY=
MARKETSTACK_API_KEY=
PLAID_CLIENT_ID=
PLAID_SECRET=
PLAID_ENV=
ZERODHA_API_KEY=
ZERODHA_API_SECRET=
IBKR_CLIENT_ID=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
REDIS_URL=
RESEND_API_KEY=
SENTRY_DSN=
```

Frontend local required:

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_ENV=local
VITE_ENABLE_DEMO_MODE=false
```

Frontend beta required:

```bash
VITE_API_BASE_URL=https://your-backend.example.com
VITE_APP_ENV=production
VITE_ENABLE_DEMO_MODE=false
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=
```

Frontend future optional:

```bash
VITE_POSTHOG_KEY=
VITE_GA_MEASUREMENT_ID=
VITE_SENTRY_DSN=
VITE_BETA_FEEDBACK_URL=
```

Frontend must not contain market data provider keys, AI provider keys, broker secrets, Stripe secret keys, Supabase service role keys, or database credentials.

## 19. Current Commands

Start backend locally:

```bash
cd backend
uvicorn app.main:app --reload
```

Start frontend locally:

```bash
cd frontend
npm run dev
```

Run backend tests:

```bash
cd backend
pytest
```

Fallback if `pytest` is unavailable on PATH:

```bash
cd backend
/Users/dhruvtantia/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m pytest
```

Run frontend build:

```bash
cd frontend
npm run build
```

Run migrations:

```bash
cd backend
alembic upgrade head
```

Seed demo data:

```bash
cd backend
python -m app.seed_demo
```

Or:

```bash
curl -X POST http://localhost:8000/api/demo/seed
```

Run local demo checklist:

```bash
cat docs/local-demo-checklist.md
```

Then execute the checklist manually: backend setup, migrations, backend server, frontend setup/server, seed demo, upload `docs/sample_india_portfolio.csv`, refresh prices, verify dashboard, verify analytics, verify AI advisor.

Makefile shortcuts:

```bash
make backend
make frontend
make test-backend
make build-frontend
make seed-demo
```

## 20. Current QA Status

Backend tests status: pytest suite exists under `backend/app/tests`. Latest run result should be recorded below after this document is created.

Frontend build status: `npm run build` exists and currently uses `tsc -b && vite build`. Latest run result should be recorded below after this document is created.

Upload API status: implemented and covered by tests in `backend/app/tests/test_uploads_api.py`.

Upload UI status: implemented as a multi-step wizard in `frontend/src/pages/UploadPage.tsx`; needs manual browser verification for the full CSV/XLSX path.

Dashboard status: implemented in `frontend/src/pages/DashboardPage.tsx`; uses the first portfolio currently. Needs manual visual QA.

Analytics status: implemented in `frontend/src/pages/AnalyticsPage.tsx`; risk history metrics are placeholders.

AI advisor status: implemented with deterministic backend mock responses and persisted conversations; no real AI provider call.

Production safety status: not production ready. Demo auth is blocked outside local/demo mode, which is safe against accidental shared demo auth but also means real hosted auth-dependent APIs are not usable until production auth is implemented.

Latest verification:

- Backend tests: PASS on 2026-05-21. `pytest` was not on PATH, so the documented Codex fallback was used from `backend/`: `/Users/dhruvtantia/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m pytest`. Result: 72 passed.
- Frontend build: PASS on 2026-05-21 from `frontend/` with `npm run build`. Result: `tsc -b && vite build` completed successfully. Vite emitted a large-chunk warning for the bundled app JS, matching the existing known issue.

## 21. Known Limitations

- The app may not run smoothly locally yet without following setup exactly.
- Market prices are mock data.
- AI advisor is mock AI.
- No real authentication.
- No real Indian market data provider.
- No broker sync.
- No payments.
- No production deployment performed from this task.
- UI needs redesign/polish before beta.
- Upload UI may still need manual browser verification.
- Dashboard and analytics currently select the first portfolio in some places instead of a global selected-portfolio state.
- Historical risk metrics are placeholders.
- Mixed-currency portfolios are bucketed by currency but not FX-converted.
- No real legal disclaimer language has been approved.
- Watchlist API/schema naming around `note`/`notes` needs verification.

## 22. Immediate Roadmap

Phase A: make local app run seamlessly.

- Verify clean checkout setup.
- Confirm migrations against SQLite and Postgres.
- Make `make backend`, `make frontend`, `make seed-demo`, `pytest`, and `npm run build` reliable.
- Fix first-run errors and document exact prerequisites.

Phase B: make India-first demo solid.

- Verify `mock_india` throughout status, refresh, dashboard, analytics, AI, and upload.
- Confirm `docs/sample_india_portfolio.csv` imports cleanly.
- Ensure mock-data warning is visible wherever prices/AI may be interpreted as real.

Phase C: improve UI.

- Redesign dashboard/analytics/holdings/upload flows for a clearer Indian retail investor demo.
- Add consistent portfolio selection.
- Improve mobile/table responsiveness.
- Manual browser QA for empty/loading/error/success states.

Phase D: add real auth.

- Choose Supabase Auth or Clerk.
- Implement frontend auth client and backend JWT verification.
- Map auth identities to `users`.
- Remove reliance on deterministic demo user outside local demo.

Phase E: connect real/delayed Indian data.

- Choose first provider.
- Implement provider client behind backend abstraction.
- Add source/delay labeling and rate-limit handling.
- Keep frontend provider-key-free.

Phase F: deploy controlled beta.

- Supabase Postgres.
- Render/Railway backend.
- Vercel frontend.
- Run migrations and smoke tests.
- Invite a small controlled user set only after auth and data boundaries are verified.

Phase G: production hardening.

- Observability, audit logging, backups, security review, provider reliability, legal disclaimers, billing readiness, broker security, and operational runbooks.

## 23. Non-Negotiable Engineering Rules

- No frontend secrets.
- No mock data without a clear warning.
- No AI financial certainty.
- No demo auth in production.
- No direct external API calls from frontend for market data, AI, broker, payment, or service-role operations.
- No broker-specific data inside the core holdings model.
- No analytics logic duplicated in frontend; frontend displays backend analytics.
- No production claims until auth, user isolation, real provider status, security, and legal language are verified.
- No real payment flow until Stripe webhook verification and auth-linked subscriptions exist.
- No real broker sync until token storage, consent, normalization, and reconciliation are designed.

## 24. Open Questions

- Which Indian market data provider should be integrated first?
- Supabase Auth or Clerk?
- Should local demo standardize on SQLite or require Postgres for closer beta parity?
- What exact UI style should be implemented for the India-first product?
- What legal disclaimer language is needed for India-market portfolio analytics and AI explanations?
- Which broker integration matters first: Zerodha, Dhan, Angel One, or another provider?
- Should `NIFTY50` remain the default benchmark for all Indian portfolios?
- What usage limits define Free vs Pro before billing is wired?
- Should watchlist be portfolio-scoped, user-scoped, or both?
- What is the minimum private-beta observability stack?

## 25. Next Codex Prompts

Local runtime stabilization:

```text
You are working on P-insight. Work only inside /Users/dhruvtantia/Documents/Codex/p-insight-rebuild. Do not deploy. Stabilize the local runtime: verify fresh backend/frontend setup, migrations, demo seed, pytest, and npm build. Fix only issues required for the documented local MVP to run smoothly.
```

Manual upload wizard verification:

```text
You are working on P-insight. Work only inside /Users/dhruvtantia/Documents/Codex/p-insight-rebuild. Do not add new product features. Manually verify the upload wizard against docs/sample_india_portfolio.csv and the backend upload API. Fix bugs in the current upload flow only.
```

India-first demo QA:

```text
You are working on P-insight. Work only inside /Users/dhruvtantia/Documents/Codex/p-insight-rebuild. Run the India-first local demo checklist end to end. Verify mock_india prices, INR display, NIFTY50 benchmark defaults, dashboard, analytics, and AI advisor. Fix only demo-blocking bugs.
```

UI redesign planning:

```text
You are working on P-insight. Work only inside /Users/dhruvtantia/Documents/Codex/p-insight-rebuild. Do not implement yet. Inspect the current frontend and propose a practical India-first UI redesign plan for dashboard, holdings, upload, analytics, and AI advisor.
```

Supabase Auth integration:

```text
You are working on P-insight. Work only inside /Users/dhruvtantia/Documents/Codex/p-insight-rebuild. Implement real Supabase Auth for the existing backend/frontend architecture. Preserve local demo mode, remove demo auth from production paths, and add tests for user isolation.
```

Real market data provider integration:

```text
You are working on P-insight. Work only inside /Users/dhruvtantia/Documents/Codex/p-insight-rebuild. Integrate the chosen Indian market data provider behind the backend MarketDataProvider abstraction. Keep all provider secrets backend-only, label source/delay clearly, and preserve mock_india for tests/local demo.
```
