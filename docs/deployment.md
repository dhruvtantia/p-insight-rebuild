# Private Beta Deployment

This guide prepares the MVP for a private beta deployment with:

- Frontend: Vercel
- Backend: Render or Railway
- Database: Supabase Postgres

The deployment target is a working private beta, not a fully hardened production release.

## Environment Checklist

Backend environment variables:

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
MARKET_DATA_API_KEY=
POLYGON_API_KEY=
FMP_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
SENTRY_DSN=
```

Frontend environment variables:

```bash
VITE_API_BASE_URL=https://your-backend.example.com
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=
VITE_APP_ENV=production
VITE_ENABLE_DEMO_MODE=false
VITE_POSTHOG_KEY=
VITE_GA_MEASUREMENT_ID=
VITE_SENTRY_DSN=
VITE_BETA_FEEDBACK_URL=https://your-feedback-form.example.com
```

Keep market data, AI, broker, Stripe, Supabase service role, and other secret keys on the backend only.

## Database: Supabase Postgres

1. Create a Supabase project for private beta.
2. Copy the Postgres connection string from Supabase.
3. Prefer the Supabase pooled connection string for hosted app traffic.
4. Convert the SQLAlchemy driver prefix to `postgresql+psycopg2://`.
5. Set `DATABASE_URL` in Render or Railway.
6. Store `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` on the backend.
7. Store only `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` on the frontend.

Example SQLAlchemy URL shape:

```bash
DATABASE_URL=postgresql+psycopg2://postgres.xxxxx:PASSWORD@aws-0-region.pooler.supabase.com:6543/postgres
```

## Backend: Render

Render can deploy from the repo root with `render.yaml`, or from the dashboard with these settings:

- Root directory: `backend`
- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/api/health`

After the service is created, set all backend environment variables from the checklist.

## Backend: Railway

Railway can deploy the `backend` directory using the included `Procfile`.

Recommended settings:

- Service root: `backend`
- Install command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/api/health`

Set `DATABASE_URL`, `FRONTEND_URL`, `CORS_ORIGINS`, Supabase values, provider keys, and optional Sentry values in Railway variables.

## Frontend: Vercel

Deploy the Vite app from `frontend`.

Vercel settings:

- Root directory: `frontend`
- Install command: `npm install`
- Build command: `npm run build`
- Output directory: `dist`
- Framework preset: Vite

Set `VITE_API_BASE_URL` to the deployed backend origin, for example `https://p-insight-api.onrender.com`.

The included `frontend/vercel.json` rewrites all routes to `index.html` so browser refreshes work for React Router routes.

## CORS

The backend always allows local Vite origins by default through `CORS_ORIGINS`:

```bash
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

For private beta, set:

```bash
FRONTEND_URL=https://your-vercel-app.vercel.app
```

`FRONTEND_URL` is automatically added to the allowed CORS origins. If you need extra preview domains, add them to `CORS_ORIGINS` as a comma-separated list.

## Migrations

Run migrations before routing beta traffic to the backend.

Local or one-off command:

```bash
cd backend
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:PORT/postgres alembic upgrade head
```

On Render or Railway, run the same command in a one-off shell or job with the production `DATABASE_URL` already configured.

## Seed and Demo Data

Seed demo data only when the target environment is meant to include the deterministic demo portfolio.

```bash
cd backend
python -m app.seed_demo
```

For private beta, seed once after migrations, then verify dashboard, upload, analytics, and AI advisor flows against the deployed backend.

## Observability Placeholders

Sentry is documented but not required for beta:

- Backend: `SENTRY_DSN`
- Frontend: `VITE_SENTRY_DSN`

Product analytics are also placeholders:

- PostHog: `VITE_POSTHOG_KEY`
- Google Analytics: `VITE_GA_MEASUREMENT_ID`

No real Sentry, PostHog, or GA key is required to run the app.

## Demo Mode

Demo auth and `/api/demo/seed` are enabled automatically only when `APP_ENV=local`. In any hosted beta environment, keep `ENABLE_DEMO_MODE=false` unless you are intentionally deploying a shared demo sandbox.

On the frontend, set `VITE_ENABLE_DEMO_MODE=false` for production beta. Demo and placeholder CTAs are hidden unless `VITE_APP_ENV=local` or `VITE_ENABLE_DEMO_MODE=true`.
