# P-insight Frontend

React/Vite frontend foundation for the P-insight app shell.

## Environment

Copy `frontend/.env.example` to `frontend/.env` and set:

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
VITE_APP_ENV=local
VITE_ENABLE_DEMO_MODE=false
VITE_POSTHOG_KEY=
VITE_GA_MEASUREMENT_ID=
VITE_SENTRY_DSN=
VITE_BETA_FEEDBACK_URL=
```

Frontend code must not include market data, AI, broker, or payment secret keys.

## Install

```bash
cd frontend
npm install
```

## Run

```bash
npm run dev
```

## Build

```bash
npm run build
```

Vite 8 requires Node.js `^20.19.0` or `>=22.12.0`.

## Vercel

Use these private beta settings:

- Root directory: `frontend`
- Build command: `npm run build`
- Output directory: `dist`
- Required API variable: `VITE_API_BASE_URL=https://your-backend.example.com`

`frontend/vercel.json` includes a React Router rewrite to `index.html`.
