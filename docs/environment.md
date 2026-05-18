# Environment Variables

Do not commit real secrets. Use `.env.example` files as placeholders only.

## Frontend

```bash
VITE_API_BASE_URL=
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
VITE_APP_ENV=
VITE_POSTHOG_KEY=
VITE_SENTRY_DSN=
```

Frontend variables must not include market data provider keys, AI provider keys, broker secrets, service role keys, or Stripe secret keys.

## Backend

```bash
APP_NAME=P-insight
APP_ENV=local
SERVICE_NAME=p-insight-backend
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
DATABASE_URL=
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
JWT_SECRET=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
MARKET_DATA_PROVIDER=mock
MARKET_DATA_API_KEY=
POLYGON_API_KEY=
FMP_API_KEY=
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

Backend variables own all secrets and integration keys.
