# Private Beta Checklist

Use this checklist before inviting beta users.

## Infrastructure

- [ ] Create production Supabase Postgres database.
- [ ] Configure backend `DATABASE_URL` with the Supabase Postgres connection string.
- [ ] Run `alembic upgrade head` against production.
- [ ] Seed demo data with `python -m app.seed_demo` if the beta environment should include sample data.
- [ ] Set backend environment variables.
- [ ] Set frontend environment variables.
- [ ] Deploy backend to Render or Railway.
- [ ] Deploy frontend to Vercel.
- [ ] Configure backend `FRONTEND_URL` to the Vercel production URL.
- [ ] Confirm CORS allows the Vercel URL and localhost dev URLs.

## Smoke Tests

- [ ] Test backend health endpoint: `GET /api/health`.
- [ ] Test create portfolio.
- [ ] Test upload flow with `docs/sample_india_portfolio.csv`.
- [ ] Test dashboard loads summary data.
- [ ] Test holdings page loads positions.
- [ ] Test analytics page loads allocation, performance, and risk data.
- [ ] Test AI advisor with mock provider or real AI key.
- [ ] Test beta feedback CTA opens the configured feedback URL.

## Beta Launch

- [ ] Invite 5 beta users.
- [ ] Share known limitations with beta users.
- [ ] Collect feedback through `VITE_BETA_FEEDBACK_URL`.
- [ ] Review backend logs after first user sessions.
- [ ] Review product analytics if PostHog or GA is configured.
- [ ] Triage beta feedback before expanding the invite list.
