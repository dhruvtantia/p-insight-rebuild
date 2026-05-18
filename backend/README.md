# P-insight Backend

FastAPI backend foundation for the P-insight modular monolith.

## Local Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run Backend

```bash
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/api/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "p-insight-backend"
}
```

## Run Tests

```bash
pytest
```

## Development Auth Placeholder

Portfolio and holdings APIs currently use a deterministic demo user dependency. If the demo user does not exist, the backend creates it on first authenticated request. This is temporary and will be replaced by Supabase Auth or Clerk in a later auth phase.

## Alembic

Alembic is initialized in `alembic/`. The initial migration defines the Phase 1 data model tables.

```bash
alembic upgrade head
```

Set `DATABASE_URL` before running migrations against a real database.
