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

## Local Development

See [docs/local-development.md](docs/local-development.md) for backend setup, frontend setup, database setup, run commands, demo seeding, and test commands.

Quick local path:

```bash
make backend
make frontend
```

Seed demo data:

```bash
make seed-demo
```

Known MVP limitations are tracked in [docs/known-issues.md](docs/known-issues.md).
