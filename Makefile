.PHONY: setup backend frontend dev

setup:
	cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
	cd frontend && npm install

backend:
	cd backend && .venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

frontend:
	cd frontend && npm run dev

# Run backend + frontend together (needs two shells).
dev:
	@echo "Open two terminals and run:  make backend   /   make frontend"
