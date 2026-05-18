# P-insight

P-insight is a greenfield portfolio analytics dashboard for uploading portfolio data, validating holdings, viewing analytics, and later asking AI-powered portfolio questions from structured portfolio context.

## Greenfield-Only Rule

This repository is the only source for the rebuild. Do not inspect, import, copy, reuse, reference, or depend on any previous P-insight codebase.

## Tech Stack

Frontend:
- React
- TypeScript
- Vite
- Tailwind CSS
- TanStack Query
- React Hook Form
- Zod
- Recharts

Backend:
- FastAPI
- Python
- Pydantic
- SQLAlchemy
- Alembic
- PostgreSQL
- pytest

Planned integrations:
- Supabase Auth or Clerk for production auth
- Backend-only market data providers
- Backend-only AI providers
- Broker connection placeholders
- Billing placeholders

## Repo Structure

```text
frontend/   React application foundation
backend/    FastAPI modular monolith foundation
docs/       Product, architecture, API, environment, and deployment notes
```

## Local Development Plan

Phase 0 creates docs, folder skeletons, and env examples only. It does not implement backend routes, frontend screens, business logic, market data, AI, broker integrations, or payments.

Next phases should add implementation in small, testable commits:
1. Backend app bootstrap and health route.
2. Portfolio and holdings persistence through repository/service layers.
3. Upload validation before holdings writes.
4. Frontend MVP screens that call only backend APIs.
5. Analytics, rule-based insights, and AI advisor mocks.
