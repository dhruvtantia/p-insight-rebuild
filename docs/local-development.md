# Local Development

This repo is the source of truth for the P-insight rebuild. Do not use any previous P-insight repository.

## Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

For a low-friction local Indian-market demo database, set these values in `backend/.env`:

```bash
MARKET_DATA_PROVIDER=mock_india
INDIAN_MARKET_DATA_PROVIDER=mock_india
DATABASE_URL=sqlite:///./p_insight_local.db
```

For PostgreSQL, create a database and set a PostgreSQL URL instead:

```bash
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/p_insight
```

## Database Setup

Run migrations from `backend/`:

```bash
alembic upgrade head
```

The test suite creates isolated SQLite databases and does not require local PostgreSQL.

## Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env
```

Set:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

Frontend code must not contain market data, AI, broker, or payment secret keys.

## Run Commands

Backend:

```bash
cd backend
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm run dev
```

Open `http://localhost:5173`.

## Demo Data

Option 1: click **Try demo portfolio** on the landing or onboarding page.

Option 2: call the backend endpoint:

```bash
curl -X POST http://localhost:8000/api/demo/seed
```

Option 3: run the backend seed command:

```bash
cd backend
python -m app.seed_demo
```

The demo seed creates a deterministic Indian demo user portfolio with `RELIANCE`, `TCS`, `HDFCBANK`, `INFY`, `ICICIBANK`, `SBIN`, `ITC`, `BHARTIARTL`, and `NIFTYBEES`, including realistic quantities, costs, and mock INR prices.

## Upload Sample

Use [sample_india_portfolio.csv](sample_india_portfolio.csv) for India CSV upload testing. [sample_portfolio.csv](sample_portfolio.csv) mirrors the India-first template for the default upload path.

## Test Commands

Backend:

```bash
cd backend
pytest
```

If `pytest` is unavailable on PATH in the Codex desktop runtime, use:

```bash
/Users/dhruvtantia/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m pytest
```

Frontend:

```bash
cd frontend
npm run build
```

## Main Local Flow

1. Open the landing page.
2. Use placeholder login or click **Try demo portfolio**.
3. Create or seed a portfolio.
4. Add an NSE/BSE holding manually or upload `docs/sample_india_portfolio.csv`.
5. Validate and confirm the upload.
6. Refresh prices from Holdings or Dashboard.
7. Review Dashboard analytics.
8. Open Analytics for allocation, risk, performance, and rules.
9. Open AI Advisor and generate a mock summary or ask a question.
