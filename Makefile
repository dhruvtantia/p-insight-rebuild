.PHONY: backend frontend test-backend build-frontend seed-demo

backend:
	cd backend && uvicorn app.main:app --reload

frontend:
	cd frontend && npm run dev

test-backend:
	cd backend && pytest

build-frontend:
	cd frontend && npm run build

seed-demo:
	cd backend && python -m app.seed_demo
