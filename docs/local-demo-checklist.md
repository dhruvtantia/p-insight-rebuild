# Local Demo Checklist

Use this checklist to run the local P-insight MVP from a clean checkout and verify the Indian retail investor demo flow. All market prices and AI responses are mock data.

## 1. Backend Setup

From the repository root:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

For the Indian-market local demo, set these values in `backend/.env`:

```bash
APP_ENV=local
ENABLE_DEMO_MODE=false
DATABASE_URL=sqlite:///./p_insight_local.db
MARKET_DATA_PROVIDER=mock_india
```

Verify backend status config after the backend is running:

```bash
curl http://127.0.0.1:8000/api/status
```

Expected key values:

```json
{
  "app_env": "local",
  "demo_mode_enabled": true,
  "market_data_provider": "mock_india",
  "ai_provider_mode": "mock"
}
```

## 2. Run Migrations

From `backend/`:

```bash
alembic upgrade head
```

If you need a completely fresh SQLite demo database:

```bash
rm -f p_insight_local.db
alembic upgrade head
```

Only remove `p_insight_local.db` when you intentionally want to discard local demo data.

## 3. Start Backend

Terminal 1, from `backend/`:

```bash
uvicorn app.main:app --reload
```

Equivalent repo-root Make command:

```bash
make backend
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

## 4. Frontend Setup

Terminal 2, from the repository root:

```bash
cd frontend
npm install
cp .env.example .env
```

Set this value in `frontend/.env`:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## 5. Start Frontend

Terminal 2, from `frontend/`:

```bash
npm run dev
```

Equivalent repo-root Make command:

```bash
make frontend
```

Open:

```text
http://localhost:5173
```

## 6. Seed Demo Data

With the backend running and `MARKET_DATA_PROVIDER=mock_india`, run either command from the repository root:

```bash
make seed-demo
```

Or:

```bash
cd backend
python -m app.seed_demo
```

Expected terminal output includes `Demo India Portfolio` and Indian symbols such as `RELIANCE`, `TCS`, and `INFY`.

You can also seed through the API:

```bash
curl -X POST http://localhost:8000/api/demo/seed
```

## 7. Upload Sample India CSV

Use the UI for the upload workflow:

1. Open `http://localhost:5173`.
2. Go to `Onboarding` and create a fresh portfolio named `India Upload Demo`.
3. Use base currency `INR`.
4. Use benchmark `NIFTY50`.
5. Go to `Upload`.
6. Select the `India Upload Demo` portfolio.
7. Upload `docs/sample_india_portfolio.csv`.
8. Confirm the detected column mapping. `symbol` and `quantity` are required.
9. Validate the upload.
10. Confirm import.

Expected result: valid rows are imported as holdings with INR currency and NSE exchange metadata.

## 8. Refresh Prices

Use either page:

1. Go to `Holdings`.
2. Select the seeded `Demo India Portfolio` or uploaded `India Upload Demo` portfolio.
3. Click `Refresh Prices`.

Or:

1. Go to `Dashboard`.
2. Click `Refresh Prices`.

Expected result: refresh result shows provider/source badges with `mock_india`, and the global banner remains visible:

```text
Demo data: prices are simulated and not suitable for investment decisions.
```

## 9. Verify Dashboard

Open `Dashboard` and verify:

- The demo-data warning banner is visible.
- Portfolio value cards show INR-formatted values for the India demo portfolio.
- Holdings count is non-zero.
- Last updated changes after price refresh.
- Price refresh result shows a `mock_india` source badge.
- Top holdings and allocation sections render without errors.

## 10. Verify Analytics

Open `Analytics` and verify:

- The demo-data warning banner is visible.
- Overview metrics render for the selected portfolio.
- Allocation tab shows asset, sector, and currency exposure.
- Risk tab shows concentration status.
- Performance tab renders gain/loss tables or empty states without errors.
- Rules tab shows rule-based insights or an empty state.

## 11. Verify AI Advisor

Open `AI Advisor` and verify:

- The demo-data warning banner is visible.
- Select the India demo portfolio.
- Click `Generate summary`.
- Ask a question such as `Where is my portfolio concentrated?`.
- Each assistant response shows the `Mock AI response` badge.
- Responses mention portfolio context without giving real investment advice.

## Local Demo Known Limitations

- Demo auth: local APIs use a deterministic development user, not real user authentication.
- Mock prices: `mock` and `mock_india` prices are simulated and not suitable for investment decisions.
- Mock AI: AI advisor responses are deterministic mock responses built from backend context.
- No broker sync: broker connection screens are placeholders and do not sync holdings.
- No real payments: billing and checkout flows are placeholders.

## Manual Pass/Fail Table

| Check | Expected Result | Pass/Fail | Notes |
| --- | --- | --- | --- |
| Backend migrations | `alembic upgrade head` completes without errors |  |  |
| Backend server | `/api/health` returns `status: ok` |  |  |
| Status endpoint | `/api/status` returns `market_data_provider: mock_india` and `ai_provider_mode: mock` |  |  |
| Frontend server | `http://localhost:5173` loads |  |  |
| Demo seed | `Demo India Portfolio` is created with Indian tickers |  |  |
| India CSV upload | `docs/sample_india_portfolio.csv` validates and imports |  |  |
| Price refresh | Holdings refresh with `mock_india` source badge |  |  |
| Dashboard | Warning banner, INR metrics, and portfolio sections render |  |  |
| Analytics | Overview, allocation, risk, performance, and rules render |  |  |
| AI Advisor | Assistant responses show `Mock AI response` badge |  |  |
| Limitations visible | Mock-data warning remains visible on target pages |  |  |

## Verification Commands

Backend:

```bash
cd backend
pytest
```

If `pytest` is unavailable on PATH, use the project virtualenv:

```bash
cd backend
.venv/bin/pytest
```

Frontend:

```bash
cd frontend
npm run build
```
