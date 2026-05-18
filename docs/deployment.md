# Deployment Notes

Phase 0 does not configure deployment automation.

## Target Shape

- Frontend: static Vite build hosted on a web platform.
- Backend: FastAPI app deployed as a single modular monolith.
- Database: PostgreSQL, with Supabase Postgres preferred later.
- Background work: add Redis-backed jobs only when needed.

## Deployment Principles

- Keep frontend free of secret keys.
- Run database migrations before backend release.
- Use separate environments for development, staging, and production.
- Configure observability before production launch.
- Keep mock providers available for non-production test environments.
