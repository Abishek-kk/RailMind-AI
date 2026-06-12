# TeamAccelerate — Local Dev & E2E Quickstart

This repository contains the backend FastAPI service and a Vite + React frontend. The repository includes a Playwright E2E test that validates upload -> dashboard -> stop flow.

## Run locally (dev)

Prereqs: Python 3.11, Node 18, npm

1. Start backend (from repo root):

```powershell
# Activate your venv if you use one
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Optional LSTM prototype training:

```powershell
cd backend
python -m app.lstm.train
```

If the expected `.pt` LSTM weights are missing, the backend leaves LSTM inference disabled and returns neutral LSTM scores. Do not use `app.lstm.generate_default_models` for real inference; it creates random-weight architecture placeholders only.

Pose model setup:

Set `POSE_MODEL_PATH` to a local YOLOv8 pose weights file, such as `yolov8n-pose.pt`. The backend does not download pose weights at startup; if the file is missing or `ultralytics` is unavailable, CV feed processing is disabled and logged instead of crashing the app.

2. Start frontend dev server (from repo root):

```powershell
cd frontend
npm install
npm run dev
# frontend will be available at http://localhost:5173
```

3. Use the UI to upload videos, view dashboard, and Stop feeds.

## Run Playwright E2E (local)

Make sure both backend and frontend dev servers are running as above, then run:

```bash
cd frontend
npm run e2e
```

The `e2e` script runs the Playwright test suite (the minimal test is at `tests/e2e/feeds.spec.ts`).

Environment variables (optional):
- `E2E_BASE_URL` — override the frontend URL used by tests (defaults to `http://localhost:5173`)
- `E2E_API_BASE` — override the backend API base (defaults to `http://localhost:8000/api`)

## CI

A GitHub Actions workflow was added at `.github/workflows/ci.yml` to run backend tests and the Playwright E2E against a built frontend and the backend server.

## Notes

- Processor lifecycle has been centralized into `backend/app/core/processor_manager.py` and endpoints now use that manager.
- Playwright and browsers are included as dev dependencies in `frontend/package.json`.

If you want, I can now:
- Consolidate further cleanup (remove any remaining local registries),
- Add a README section about running headless in CI, or
- Commit these changes and push a branch/PR.
