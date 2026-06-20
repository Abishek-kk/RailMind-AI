<div align="center">

<img src="https://img.shields.io/badge/RailMind_AI-v1.5-0A84FF?style=for-the-badge&logo=railway&logoColor=white" alt="RailMind AI"/>

# RailMind AI
### Intelligent Railway Safety & Security System.

**Turning existing CCTV infrastructure into proactive behavioural monitoring — no new cameras, no facial recognition.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.9-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)](https://pytorch.org)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-00CFFF?style=flat-square)](https://ultralytics.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.5-1C1C1C?style=flat-square)](https://langchain-ai.github.io/langgraph/)
[![Tests](https://img.shields.io/badge/backend_tests-57%2F57_passing-2EA44F?style=flat-square)](#testing)
[![FAR AWAY 2026](https://img.shields.io/badge/FAR_AWAY_2026-Hackathon-FF6B35?style=flat-square)](https://faraway2026.com)

</div>

---

## Status: Working Prototype

This is a hackathon build for **FAR AWAY 2026** by **Team Accelerate**. Everything described below as "implemented" has been verified by running it — backend boots, 57 backend tests pass, frontend builds, and the CV → LSTM → agent pipeline runs end-to-end on uploaded video.

Some capabilities described in early planning docs (edge/Jetson deployment, multi-camera re-identification, PA system integration, a mobile app) are **not yet built** — see [What's Not Built Yet](#whats-not-built-yet) below. We'd rather you find out from this README than from the code.

---

## Table of Contents

- [Overview](#overview)
- [What This Actually Does](#what-this-actually-does)
- [What's Not Built Yet](#whats-not-built-yet)
- [Screenshots](#screenshots)
- [System Architecture](#system-architecture)
- [AI Pipeline](#ai-pipeline)
- [LSTM Behaviour Classifier](#lstm-behaviour-classifier)
- [Agentic Reasoning](#agentic-reasoning)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Training the LSTM](#training-the-lstm)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Privacy & Ethics](#privacy--ethics)
- [Project Structure](#project-structure)
- [Roadmap](#roadmap)
- [Team](#team)

---

## Overview

RailMind AI processes existing CCTV video through a computer-vision pipeline (person detection → tracking → pose estimation → behavioural feature extraction) and feeds the result into a bidirectional LSTM that classifies 30-second behavioural windows into one of four categories: **Normal**, **Suicide Risk**, **Pickpocketing**, or **Security Threat**. A three-agent LangGraph pipeline takes that classification, computes a final risk score, and dispatches alerts to staff through a live dashboard — with no facial recognition and no biometric storage anywhere in the system.

| Challenge | Approach |
|---|---|
| **Suicide risk** | Edge proximity + pacing + low crowd interaction, modelled over a temporal window |
| **Pickpocketing / theft** | Sustained close-following distance + repeated crowd contact |

---

## What This Actually Does

Verified by running it, not just reading the code:

- **Person detection & tracking** — YOLOv8 detection + Ultralytics' `BYTETracker` for persistent IDs across frames.
- **Pose estimation** — YOLOv8-Pose extracts 17 COCO keypoints per tracked person.
- **Behavioural feature extraction** — 7 features per person per 30s window (edge proximity, loitering time, pacing count, movement speed, direction changes, following distance, crowd interactions).
- **Trained LSTM classifier** — a real, saved 2-layer bidirectional LSTM checkpoint (`backend/lstm/saved_models/behavior_classifier.pt`) with a fitted feature scaler, loaded and run at inference time.
- **LangGraph multi-agent pipeline** — a real `StateGraph` with Perception → Reasoning → Intervention nodes, compiled once and invoked per detection.
- **Optional LLM-assisted reasoning** — if an OpenAI or Anthropic API key is configured, the Reasoning Agent asks an LLM for a bounded risk-score adjustment (±10) and a reasoning summary; without a key, it falls back cleanly to the rule-based `RiskScorer`.
- **Live dashboard** — React 19 + TanStack Router/Query dashboard pulling real stats from the FastAPI backend (only camera thumbnail images are placeholders; incident counts, trends, and risk distributions are real).
- **Video upload & playback pipeline** — upload an `.mp4`, it runs through the full CV → LSTM → agent pipeline; not a canned demo loop.
- **WebSocket alert delivery** — a channel-based pub/sub `ConnectionManager` broadcasts alerts to all connected dashboard clients in real time.
- **Escalation timers** — unacknowledged alerts escalate after a configurable timeout (default 60s).
- **Email alerts (SMTP)** — implemented via `smtplib`, configurable via `.env`.
- **SMS escalation (Twilio)** — implemented in the escalation service, configurable via `.env`.
- **57 passing backend tests** covering agents, CV pipeline, LSTM inference, risk scoring, alerts, incidents, escalation, and heatmaps.

---

## What's Not Built Yet

Being direct about this so nobody — including us — overclaims it later:

| Planned capability | Actual status |
|---|---|
| **Edge deployment on Jetson Orin Nano / TensorRT** | Not implemented. No Jetson-specific or TensorRT code exists. The pipeline currently runs on whatever machine hosts the backend (CPU or CUDA GPU via PyTorch). |
| **Multi-camera person re-identification** | Not implemented. Tracking is per-camera only; a person is not currently re-linked across camera handoffs. |
| **Automated PA system integration** | Not implemented. No MQTT/PA-controller code exists. |
| **Mobile app for staff (React Native)** | Does not exist yet. Staff alerts currently surface via the web dashboard, email, and SMS only. |
| **True multi-station SaaS isolation** | The database has a `station_id` column, but there's no multi-tenant access control or per-station billing logic yet — this is single-deployment software today. |
| **Live RTSP camera ingestion** | The video processor uses `cv2.VideoCapture`, which can technically open an `rtsp://` URL, but this path has only been exercised against uploaded video files in testing, not a live camera feed. Treat RTSP support as untested, not proven. |
| **LSTM trained on real incident data** | The shipped model is trained on synthetic sequences generated from rule-based behavioural definitions, not real labelled incident footage. The reported accuracy is against this synthetic test set, not real-world data. |

---

## Screenshots

### Live Monitoring
2×2 grid of simultaneous CCTV feeds with AI-annotated bounding boxes, track IDs, and live risk labels overlaid directly on the video.

![Live Monitoring](assets/live.png)

### Dashboard
Aggregated analytics across all platforms — incident counts, 7-day trend, risk distribution, a platform heatmap, peak-risk-hour histogram, and a per-camera summary table.

![Dashboard](assets/dashboard.png)

### Alerts
Full alert triage view with filterable tabs by risk level, a sortable alert table, and a detail panel for acknowledging or resolving an incident.

![Alerts](assets/alerts.png)

---

## System Architecture

```
┌─────────────── PROCESSING ───────────────┐
│ Video Source → OpenCV → YOLOv8 Detection │
│   → ByteTrack → YOLOv8-Pose               │
│   → Feature Extraction (7 features)       │
│   → BiLSTM Classifier (30s window)        │
└────────────────────┬───────────────────────┘
                      │ classification + confidence
┌─────────────────────▼──────────────────────┐
│ LangGraph Agent Pipeline                    │
│ Perception → Reasoning → Intervention       │
└────────────────────┬───────────────────────┘
                      │ risk score + action
┌─────────────────────▼──────────────────────┐
│ FastAPI + SQLite/PostgreSQL                 │
│ WebSocket broadcast → React Dashboard       │
│ Email (SMTP) / SMS (Twilio) escalation      │
└──────────────────────────────────────────────┘
```

### Pipeline Stages

| Stage | Component | Description |
|---|---|---|
| 1 | OpenCV | Decode and preprocess video frames |
| 2 | YOLOv8 | Detect persons, output bounding boxes + confidence |
| 3 | ByteTrack | Assign and maintain persistent track IDs |
| 4 | YOLOv8-Pose | Extract 17 body keypoints per person |
| 5 | Feature Extraction | Compute 7 behavioural features per 30s window |
| 6 | BiLSTM Classifier | Classify the windowed sequence into a risk category |
| 7 | Reasoning Agent | Combine LSTM output with context into a final 0–100 risk score |
| 8 | Intervention Agent | Dispatch alerts, create incident record, start escalation timer |
| 9 | Database | Store incidents, alerts, tracks, analytics, feedback |
| 10 | Dashboard | Live alerts, incident history, heatmaps, analytics |

---

## AI Pipeline

### Behavioural Feature Vector

Each tracked person generates a 7-dimensional feature vector per 30-second window:

```python
feature_vector = [
    edge_proximity_seconds,   # Cumulative time within 0.5m of platform edge
    loitering_time,           # Stationary duration in a single spatial zone
    pacing_count,             # Back-and-forth movement cycles detected
    movement_speed,           # Average velocity (m/s)
    direction_changes,        # Heading reversals per minute
    following_distance,       # Sustained proximity to one other person
    crowd_interactions,       # Count of unique close-contact individuals
]
```

### Model Specifications

| Model | Task | Notes |
|---|---|---|
| YOLOv8n/s | Person detection | Ultralytics implementation |
| ByteTrack | Multi-object tracking | Via `ultralytics.trackers.BYTETracker` |
| YOLOv8-Pose | Pose estimation | 17 COCO keypoints |
| BiLSTM | Behaviour classification | 2-layer bidirectional LSTM, `[30, 7]` input sequence |
| LangGraph + optional LLM | Risk reasoning | Rule-based by default; LLM adjustment if API key configured |

---

## LSTM Behaviour Classifier

```
Input [30, 7] → BiLSTM (128 units) → Dropout (0.3)
              → BiLSTM (64 units)  → Dropout (0.3)
              → Dense (32, ReLU) → Dense (4, Softmax)
```

- **Output classes:** Normal, Suicide Risk, Pickpocketing, Security Threat
- **Training data:** synthetic sequences generated from rule-based behavioural definitions (see [Training the LSTM](#training-the-lstm))
- **Saved artifacts:** `backend/lstm/saved_models/behavior_classifier.pt` + a fitted `StandardScaler` pickle

> Reported accuracy figures are measured against the synthetic held-out test set used for training. They are not yet validated against real, labelled incident footage — treat them as a development benchmark, not a production guarantee.

---

## Agentic Reasoning

Three LangGraph nodes, compiled once into a `StateGraph` at startup:

| Agent | Role |
|---|---|
| **Perception** | Assembles the 30-second feature sequence and runs LSTM inference |
| **Reasoning** | Combines the LSTM output with context (edge distance, duration, following distance, pose) into a final risk score via `RiskScorer`; optionally asks a configured LLM (OpenAI or Anthropic) for a bounded ±10 score adjustment and a plain-language reasoning summary |
| **Intervention** | Applies score thresholds, dispatches the alert, creates the incident record, and starts the escalation timer |

If no LLM API key is set, the Reasoning Agent runs purely on rule-based scoring — the system does not require an LLM to function.

---

## Tech Stack

### Backend
| Library | Purpose |
|---|---|
| Python 3.11+ | Core language |
| FastAPI + Uvicorn | Async REST API |
| SQLAlchemy + Alembic | ORM + migrations |
| LangGraph | Multi-agent orchestration |
| PyTorch | LSTM training & inference |
| Ultralytics YOLOv8 | Detection, pose, tracking |
| OpenCV | Video decode/preprocess |
| smtplib | Email alerts |
| Twilio | SMS escalation |

### Frontend
| Library | Purpose |
|---|---|
| React 19 | UI |
| TanStack Router / Query | Routing + server state |
| Tailwind CSS 4 | Styling |
| Recharts | Analytics charts |
| shadcn/ui | Component library |
| Socket.io Client | Real-time alerts |

### Storage
SQLite for development (used in this build); PostgreSQL + Redis are the intended production path but are not what this repo currently runs on by default.

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- (Optional) an OpenAI or Anthropic API key for LLM-assisted reasoning

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # edit values as needed
python run.py --mode server --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

The dashboard expects the backend at the URL configured in `VITE_API_BASE_URL` (defaults to `http://localhost:8000/api`).

---

## Configuration

### Backend (`backend/.env`)

```bash
DEBUG=True
DATABASE_URL=sqlite:///./railmind.db
SECRET_KEY=your-secret-key-here
RAILMIND_API_KEY=change-this-admin-api-key
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# LSTM behaviour label thresholds
BEHAVIOR_HIGH_SCORE_THRESHOLD=0.65
BEHAVIOR_ERRATIC_SCORE_THRESHOLD=0.4
BEHAVIOR_FOLLOWING_DISTANCE_METERS=1.2

# Email (SMTP) — optional
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=alert@example.com
SMTP_PASSWORD=your-smtp-password
ALERT_EMAIL_RECIPIENTS=security@example.com,ops@example.com

# SMS (Twilio) — optional
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_FROM_NUMBER=+1234567890
TWILIO_TO_NUMBERS=+19876543210,+10987654321
```

### Frontend (`frontend/.env`)

```bash
VITE_API_BASE_URL=http://localhost:8000/api
VITE_RAILMIND_API_KEY=change-this-admin-api-key
VITE_WS_URL=ws://localhost:8000
```

---

## Training the LSTM

```bash
cd backend
python run.py --mode train-cli --model-type all --epochs 30 --batch-size 32
```

Or trigger training via the API while the server is running:

```bash
curl -X POST http://localhost:8000/api/training/trigger \
  -H "Content-Type: application/json" \
  -d '{"model_type": "all", "epochs": 30, "batch_size": 32}'
```

Training data is generated synthetically from rule-based behavioural definitions — see `backend/app/lstm/train.py`. Swapping in real labelled incident data is the top priority before any production claim about accuracy.

---

## API Reference

All routes are prefixed with `/api` unless noted. Selected endpoints:

| Method | Endpoint | Description |
|---|---|---|
| GET | `/incidents` | List incidents (filterable) |
| GET | `/incidents/{id}` | Full incident detail |
| POST | `/incidents/{id}/acknowledge` | Staff acknowledges an incident |
| POST | `/incidents/{id}/resolve` | Mark an incident resolved |
| POST | `/incidents/{id}/false-positive` | Flag a false positive |
| GET | `/alerts` | List alerts |
| GET | `/alerts/stats` | Alert statistics |
| PATCH | `/alerts/{id}/acknowledge` | Acknowledge an alert |
| PATCH | `/alerts/{id}/resolve` | Resolve an alert |
| PATCH | `/alerts/{id}/assign` | Assign an alert to staff |
| GET | `/dashboard/stats` | Headline dashboard metrics |
| GET | `/dashboard/trend` | Incident trend over time |
| GET | `/dashboard/risk-distribution` | Risk category breakdown |
| GET | `/dashboard/heatmap` | Spatial heatmap data |
| GET | `/dashboard/cctv-summary` | Per-camera summary |
| GET | `/analytics/lstm-performance` | LSTM accuracy/confidence metrics |
| GET | `/feeds` | List camera feeds |
| POST | `/feeds/upload` | Upload a video file for processing |
| GET | `/feeds/{id}/stream` | Stream a processed feed |
| GET | `/staff/available` | Available staff |
| POST | `/training/trigger` | Trigger LSTM retraining |
| GET | `/health` | Health check |
| WS | `/ws/alerts` | Real-time alert stream |

Full route definitions live in `backend/app/api/routes/`.

---

## Testing

```bash
cd backend
pytest                       # full suite — 57 tests, all passing as of this build
pytest tests/test_agents.py
pytest tests/test_lstm.py
pytest tests/test_risk_scoring.py
pytest tests/test_cv.py
```

| Test file | Covers |
|---|---|
| `test_agents.py` | Agent pipeline (perception → reasoning → intervention) |
| `test_lstm.py` | LSTM model loading and inference |
| `test_risk_scoring.py` | Risk score computation |
| `test_cv.py` | CV pipeline behaviour and degradation handling |
| `test_alerts.py` | Alert lifecycle |
| `test_incident_and_escalation.py` | Incident creation and escalation timers |
| `test_heatmap.py` | Heatmap analytics |
| `test_dashboard_trend.py` | Dashboard trend data |
| `test_reliability.py` | Failure-mode handling |
| `test_api_auth.py` | API authentication |
| `test_feeds.py` | Feed registration and upload |

Frontend:
```bash
cd frontend
npm run e2e   # Playwright E2E tests
```

---

## Privacy & Ethics

- **No facial recognition** — no face-detection model is used anywhere in the pipeline.
- **No biometric storage** — track IDs are numeric, session-scoped integers, not linked to identity.
- **Behaviour-only analysis** — the feature vector contains only movement metrics.
- **Human-in-the-loop** — every alert requires staff acknowledgement; the system never triggers a physical intervention on its own.
- **Operator accountability** — alerts, acknowledgements, and resolutions are logged with timestamps.

This is an architectural property of the current code, not just a policy statement — there is no facial recognition or identity-linking code anywhere in this repository.

---

## Project Structure

```
RailMind-AI/
├── assets/                  # Dashboard screenshots used in this README
├── backend/
│   ├── app/
│   │   ├── agents/        # LangGraph perception/reasoning/intervention nodes
│   │   ├── cv/             # Video processing, pose estimation
│   │   ├── features/       # Behavioural feature detectors
│   │   ├── lstm/            # Model definition, training, inference
│   │   ├── api/routes/      # FastAPI endpoints
│   │   ├── services/        # Risk scoring, alerts, escalation, notifications
│   │   ├── analytics/       # Dashboard metrics, heatmaps
│   │   ├── models/          # SQLAlchemy models
│   │   └── core/             # Config, database, WebSocket manager
│   ├── lstm/saved_models/    # Trained checkpoint + scaler
│   ├── tests/                  # Pytest suite
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── routes/            # Dashboard, alerts, live feed pages
│   │   ├── components/         # UI components
│   │   ├── lib/api/             # API client functions
│   │   └── hooks/                # useWebSocket, etc.
│   └── tests/e2e/                # Playwright tests
└── README.md
```

---

## Roadmap

### Done (verified working in this repo)
- [x] Video upload + CV pipeline (YOLOv8 + ByteTrack + Pose)
- [x] Bidirectional LSTM behaviour classifier with saved weights
- [x] LangGraph Perception + Reasoning + Intervention agents
- [x] SQLite storage with full schema
- [x] React dashboard with live alerts and analytics
- [x] WebSocket real-time alert broadcast
- [x] Email (SMTP) and SMS (Twilio) escalation channels
- [x] Configurable escalation timers
- [x] Optional LLM-assisted reasoning (OpenAI/Anthropic)
- [x] 57 passing backend tests

### Not yet built
- [ ] Live RTSP camera validation (currently untested beyond file upload)
- [ ] PostgreSQL + Redis production migration
- [ ] LSTM retrained on real, labelled incident data
- [ ] Multi-camera person re-identification
- [ ] Edge deployment (Jetson Orin Nano / TensorRT)
- [ ] Automated PA system integration
- [ ] Mobile app for staff (React Native)
- [ ] True multi-tenant multi-station SaaS isolation
- [ ] Predictive analytics / crowd flow optimisation

---

## Team

**Team Accelerate** — FAR AWAY 2026 Hackathon

---

<div align="center">

Built for the FAR AWAY 2026 Hackathon by Team Accelerate.

</div>

