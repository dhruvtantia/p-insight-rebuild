# P-insight Architecture

## Modular Monolith

P-insight starts as a modular monolith, not microservices. The backend should be one deployable FastAPI application organized into clear modules with API, service, repository, schema, and model boundaries.

The goal is to keep early development simple while preserving separation of concerns. Modules can evolve independently inside one codebase before any service extraction is considered.

## Responsibilities

Frontend responsibilities:
- Render product workflows.
- Manage UI state, forms, loading states, empty states, and error states.
- Call only P-insight backend APIs.
- Never hold market data API keys or AI API keys.
- Never implement core analytics logic.

Backend responsibilities:
- Own API contracts.
- Validate inputs.
- Enforce upload validation before holdings writes.
- Own portfolio analytics and rule-based insights.
- Build structured AI portfolio context.
- Abstract market data, broker, auth, and billing integrations.

Database responsibilities:
- Store users, portfolios, holdings, transactions, upload batches, usage events, and later billing records.
- Use PostgreSQL for local production-like development and production.
- Allow SQLite only for isolated fast tests when explicitly configured.

## Central Portfolio Data Model

Portfolio data is the source of truth. Every product feature should read from or write to portfolio data through backend APIs and service/repository layers.

Core portfolio concepts:
- Portfolio
- Holding
- Transaction
- Upload batch
- Validation result
- Market quote snapshot
- Analytics snapshot
- Usage event

Broker-specific fields must not leak into the core holdings model. Broker data should be normalized before entering the portfolio domain.

## Market Data Abstraction Plan

Market data will be accessed only from the backend through a provider abstraction.

Initial provider:
- Mock provider for deterministic development and tests.

Future providers:
- Polygon or Massive.
- Financial Modeling Prep.
- Additional providers as needed.

The frontend will request prices, derived values, and analytics only through backend APIs.

## AI Advisor Architecture

The AI advisor must receive structured portfolio context from backend services before any model call.

The context should include:
- Portfolio summary.
- Holdings summary.
- Allocation data.
- Rule-based insights.
- Relevant risk flags.
- Guardrails that prohibit guaranteed investment advice.

If no AI provider key is configured, the backend should return deterministic mock responses.

## Broker Placeholder Architecture

Broker integrations are not part of the MVP implementation. Placeholder interfaces should exist later for:
- Plaid
- Zerodha
- IBKR
- Alpaca

All broker imports must normalize into the same internal holdings and transactions model used by manual uploads.

## Upload Import Assumption

CSV and XLSX uploads use a staged backend workflow: file parse, upload rows, column mapping, validation, then confirm import. Upload rows never write directly into holdings before validation.

For MVP duplicate handling, confirm import skips any uploaded symbol that already exists in the portfolio. It also skips repeated symbols within the same upload after the first importable occurrence. The response includes warnings and reports a partial import when duplicates or invalid rows are skipped. This avoids silently changing existing holdings from uploaded data; merge/update behavior can be designed later.

## Assumptions Log

- MVP auth starts as a deterministic demo user placeholder and can later support Supabase Auth or Clerk.
- PostgreSQL is the preferred database for local and production development.
- SQLite may be used only for isolated test runs.
- Uploads are validated before holdings are saved.
- Duplicate symbols in uploads are skipped during confirm import and reported as warnings.
- AI responses are educational explanations, not guaranteed investment advice.
- Billing is represented as plan and usage structure before live Stripe integration.
