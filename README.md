<div align="center">
<img src="https://img.shields.io/badge/RailMind_AI-v2.0-0A84FF?style=for-the-badge" alt="RailMind AI"/>
=======
<img src="https://img.shields.io/badge/RailMind_AI-v1.5-0A84FF?style=for-the-badge&logo=railway&logoColor=white" alt="RailMind AI"/>

# RailMind AI

### Intelligent Railway Safety & Security System

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

## Status: Working Prototype.

This is a hackathon build for **FAR AWAY 2026** by **Team Accelerate**. Everything described below as "implemented" has been verified by running it — backend boots, 57 backend tests pass, frontend builds, and the CV → Temporal Transformer → agent pipeline runs end-to-end on uploaded video.

Some capabilities described in early planning docs (edge/Jetson deployment, multi-camera re-identification, PA system integration, a mobile app) are **not yet built** — see [What's Not Built Yet](#whats-not-built-yet) below. We'd rather you find out from this README than from the code.

---

## Table of Contents

- [Overview](#-overview)
- [Key Metrics](#-key-metrics)
- [Features](#-features)
- [System Architecture](#-system-architecture)
- [AI & Computer Vision Pipeline](#-ai--computer-vision-pipeline)
- [Temporal Transformer Behaviour Classifier](#-temporal-transformer-behaviour-classifier)
- [Agentic AI Framework](#-agentic-ai-framework)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running the Application](#-running-the-application)
- [Training the Temporal Transformer](#-training-the-temporal-transformer)
- [API Reference](#-api-reference)
- [Dashboard & Screenshots](#-dashboard--screenshots)
- [Edge Deployment](#-edge-deployment)
- [Privacy & Ethics](#-privacy--ethics)
- [Testing](#-testing)
- [Roadmap](#-roadmap)
- [Team](#-team)

---

## Overview

RailMind AI processes existing CCTV video through a computer-vision pipeline (person detection → tracking → pose estimation → behavioural feature extraction) and feeds the result into a Temporal Transformer that classifies 30-second behavioural windows into one of four categories: **Normal**, **Suicide Risk**, **Pickpocketing**, or **Security Threat**. A three-agent LangGraph pipeline takes that classification, computes a final risk score, and dispatches alerts to staff through a live dashboard — with no facial recognition and no biometric storage anywhere in the system.

| Challenge                 | Approach                                                                         |
| ------------------------- | -------------------------------------------------------------------------------- |
| **Suicide risk**          | Edge proximity + pacing + low crowd interaction, modelled over a temporal window |
| **Pickpocketing / theft** | Sustained close-following distance + repeated crowd contact                      |

---

## What This Actually Does

Verified by running it, not just reading the code:

- **Person detection & tracking** — YOLOv8 detection + Ultralytics' `BYTETracker` for persistent IDs across frames.
- **Pose estimation** — YOLOv8-Pose extracts 17 COCO keypoints per tracked person.
- **Behavioural feature extraction** — 7 features per person per 30s window (edge proximity, loitering time, pacing count, movement speed, direction changes, following distance, crowd interactions).
- **Trained Temporal Transformer classifier** — a saved transformer checkpoint (`backend/app/transformer/saved_models/behaviour_transformer.pt`) with a fitted feature scaler, loaded and run at inference time.
- **LangGraph multi-agent pipeline** — a real `StateGraph` with Perception → Reasoning → Intervention nodes, compiled once and invoked per detection.
- **Optional LLM-assisted reasoning** — if an OpenAI or Anthropic API key is configured, the Reasoning Agent asks an LLM for a bounded risk-score adjustment (±10) and a reasoning summary; without a key, it falls back cleanly to the rule-based `RiskScorer`.
- **Live dashboard** — React 19 + TanStack Router/Query dashboard pulling real stats from the FastAPI backend (only camera thumbnail images are placeholders; incident counts, trends, and risk distributions are real).
- **Video upload & playback pipeline** — upload an `.mp4`, it runs through the full CV → Temporal Transformer → agent pipeline; not a canned demo loop.
- **WebSocket alert delivery** — a channel-based pub/sub `ConnectionManager` broadcasts alerts to all connected dashboard clients in real time.
- **Escalation timers** — unacknowledged alerts escalate after a configurable timeout (default 60s).
- **Email alerts (SMTP)** — implemented via `smtplib`, configurable via `.env`.
- **SMS escalation (Twilio)** — implemented in the escalation service, configurable via `.env`.
- **57 passing backend tests** covering agents, CV pipeline, Temporal Transformer inference, risk scoring, alerts, incidents, escalation, and heatmaps.

---

## What's Not Built Yet

Being direct about this so nobody — including us — overclaims it later:

| Planned capability                                     | Actual status                                                                                                                                                                                                                                |
| ------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Edge deployment on Jetson Orin Nano / TensorRT**     | Not implemented. No Jetson-specific or TensorRT code exists. The pipeline currently runs on whatever machine hosts the backend (CPU or CUDA GPU via PyTorch).                                                                                |
| **Multi-camera person re-identification**              | Not implemented. Tracking is per-camera only; a person is not currently re-linked across camera handoffs.                                                                                                                                    |
| **Automated PA system integration**                    | Not implemented. No MQTT/PA-controller code exists.                                                                                                                                                                                          |
| **Mobile app for staff (React Native)**                | Does not exist yet. Staff alerts currently surface via the web dashboard, email, and SMS only.                                                                                                                                               |
| **True multi-station SaaS isolation**                  | The database has a `station_id` column, but there's no multi-tenant access control or per-station billing logic yet — this is single-deployment software today.                                                                              |
| **Live RTSP camera ingestion**                         | The video processor uses `cv2.VideoCapture`, which can technically open an `rtsp://` URL, but this path has only been exercised against uploaded video files in testing, not a live camera feed. Treat RTSP support as untested, not proven. |
| **Temporal Transformer trained on real incident data** | The shipped model is trained on synthetic sequences generated from rule-based behavioural definitions, not real labelled incident footage. The reported accuracy is against this synthetic test set, not real-world data.                    |

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
│   → Temporal Transformer (30s window)     │
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

| Stage | Component            | Description                                                           |
| ----- | -------------------- | --------------------------------------------------------------------- |
| 1     | OpenCV               | Decode and preprocess video frames                                    |
| 2     | YOLOv8               | Detect persons, output bounding boxes + confidence                    |
| 3     | ByteTrack            | Assign and maintain persistent track IDs                              |
| 4     | YOLOv8-Pose          | Extract 17 body keypoints per person                                  |
| 5     | Feature Extraction   | Compute 7 behavioural features per 30s window                         |
| 6     | Temporal Transformer | Classify the windowed sequence into a risk category                   |
| 7     | Reasoning Agent      | Combine transformer output with context into a final 0–100 risk score |
| 8     | Intervention Agent   | Dispatch alerts, create incident record, start escalation timer       |
| 9     | Database             | Store incidents, alerts, tracks, analytics, feedback                  |
| 10    | Dashboard            | Live alerts, incident history, heatmaps, analytics                    |

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

| Model                    | Task                     | Notes                                                        |
| ------------------------ | ------------------------ | ------------------------------------------------------------ |
| YOLOv8n/s                | Person detection         | Ultralytics implementation                                   |
| ByteTrack                | Multi-object tracking    | Via `ultralytics.trackers.BYTETracker`                       |
| YOLOv8-Pose              | Pose estimation          | 17 COCO keypoints                                            |
| Temporal Transformer     | Behaviour classification | 2 encoder layers, `[30, 7]` input sequence, 4 output classes |
| LangGraph + optional LLM | Risk reasoning           | Rule-based by default; LLM adjustment if API key configured  |

---

## Temporal Transformer Behaviour Classifier

```
Input [30, 7] → Linear projection (64)
              → Learned positional embeddings
              → Transformer encoder (2 layers, 4 heads)
              → Mean pooling → Dense (32, ReLU)
              → Dropout (0.3) → Dense (4)
```

- **Output classes:** Normal, Suicide Risk, Pickpocketing, Security Threat
- **Training data:** synthetic sequences generated from rule-based behavioural definitions (see [Training the Temporal Transformer](#training-the-temporal-transformer))
- **Saved artifacts:** `backend/app/transformer/saved_models/behaviour_transformer.pt` + `feature_scaler.pkl`
- **Evaluation metrics:** cross-entropy loss, accuracy, precision, recall, and F1-score from the validation classification report

> Reported accuracy figures are measured against the synthetic held-out test set used for training. They are not yet validated against real, labelled incident footage — treat them as a development benchmark, not a production guarantee.

---

## Agentic Reasoning

Three LangGraph nodes, compiled once into a `StateGraph` at startup:

| Agent            | Role                                                                                                                                                                                                                                                                                 |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Perception**   | Assembles the 30-second feature sequence and runs Temporal Transformer inference                                                                                                                                                                                                     |
| **Reasoning**    | Combines the Temporal Transformer output with context (edge distance, duration, following distance, pose) into a final risk score via `RiskScorer`; optionally asks a configured LLM (OpenAI or Anthropic) for a bounded ±10 score adjustment and a plain-language reasoning summary |
| **Intervention** | Applies score thresholds, dispatches the alert, creates the incident record, and starts the escalation timer                                                                                                                                                                         |

PERCEPTION → REASONING → INTERVENTION
AGENT AGENT AGENT

• Pose extract • Risk scoring • Threshold eval
• Feature comp • LLM reasoning • WebSocket alert
• Transformer infer • Score 0-100 • Email/SMS
• Action decide • Escalation timer

````

### Alert Escalation Thresholds

| Risk Score | Action |
|-----------|--------|
| 0 – 39 | Silent log only |
| 40 – 69 | Alert nearest available staff via dashboard |
| 70 – 89 | Alert staff + security simultaneously |
| 90 – 100 | Full emergency escalation + PA trigger *(v2.0)* |
| Unacknowledged | Auto-escalate after **60 seconds** |

### LLM Integration

The Reasoning Agent optionally invokes an LLM (OpenAI GPT-4 or Anthropic Claude) for nuanced contextual reasoning, providing a `risk_adjustment` (±10 points) and `reasoning_summary`. Falls back gracefully to rule-based scoring when no API key is configured.

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/RailMind-AI.git
cd RailMind-AI

# 2. Set up backend
cd backend
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

# 3. YOLOv8 pose weights are packaged at backend/yolov8n-pose.pt
# Optional: set POSE_MODEL_PATH in .env to use different weights

# 4. Train the Temporal Transformer
python -m app.transformer.train --data_path path/to/training.jsonl

# 5. Start backend
python run.py

# 6. Set up and start frontend (new terminal)
cd ../frontend
npm install
npm run dev
````

Open [http://localhost:5173](http://localhost:5173) — the dashboard will be live.

---

## Installation

### Prerequisites

| Requirement     | Version                             |
| --------------- | ----------------------------------- |
| Python          | 3.11+                               |
| Node.js         | 18+                                 |
| CUDA (optional) | 11.8+ for GPU inference             |
| GPU (optional)  | NVIDIA (recommended for production) |

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env
```

### Frontend Setup

```bash
cd frontend
npm install
```

### YOLOv8 Pose Model

The local prototype ships with `backend/yolov8n-pose.pt` so CV processing can start out of the box. Set `POSE_MODEL_PATH=/path/to/your-pose-weights.pt` in `.env` only when you want to use different YOLOv8 pose weights.

---

## Configuration

All configuration is managed via environment variables in `backend/.env`:

```env
# Core
DEBUG=True
DATABASE_URL=sqlite:///./railmind.db # Use PostgreSQL in production
SECRET_KEY=your-secret-key-change-in-production
RAILMIND_API_KEY=change-this-admin-api-key
LOG_LEVEL=INFO

# CV Models
POSE_MODEL_PATH=./yolov8n-pose.pt
POSE_DEVICE=cuda:0 # or cpu
TRANSFORMER_SEQUENCE_LENGTH=30

# Risk Scoring
LOW_RISK_THRESHOLD=40
MEDIUM_RISK_THRESHOLD=60
HIGH_RISK_THRESHOLD=80
PLATFORM_EDGE_SAFETY_LIMIT_METERS=0.5

# Behaviour Thresholds
BEHAVIOR_HIGH_SCORE_THRESHOLD=0.65
BEHAVIOR_ERRATIC_SCORE_THRESHOLD=0.4
BEHAVIOR_FOLLOWING_DISTANCE_METERS=1.2

# LLM (Optional)
OPENAI_API_KEY=sk-... # Optional OpenAI reasoning
OPENAI_REASONING_MODEL=gpt-5.5
ANTHROPIC_API_KEY=sk-ant-... # Optional Claude reasoning
ANTHROPIC_REASONING_MODEL=claude-haiku-4-5-20251001

# Notifications
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=alert@example.com
SMTP_PASSWORD=your-smtp-password
ALERT_EMAIL_RECIPIENTS=security@example.com

TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_FROM_NUMBER=+1234567890
TWILIO_TO_NUMBERS=+19876543210

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

REST API routes under `/api/*` require `X-API-Key: <RAILMIND_API_KEY>`. For the local browser demo, set the same prototype value in `frontend/.env` as `VITE_RAILMIND_API_KEY`; this value is public in browser builds and should not be treated as a production identity system.

### Production Database (PostgreSQL)

```env
DATABASE_URL=postgresql://user:password@localhost:5432/railmind
```

---

## Running the Application

### Development

```bash
# Terminal 1 — Backend
cd backend
source venv/bin/activate
python run.py
# API live at http://localhost:8000
# Swagger docs at http://localhost:8000/docs

# Terminal 2 — Frontend
cd frontend
npm run dev
# Dashboard at http://localhost:5173
```

### Demo Mode (No Camera Required)

Use the CV simulator to generate synthetic detection events:

```bash
cd backend
python scripts/demo_runner.py
```

### Full CV Pipeline (With Video/RTSP)

Place MP4 files in `backend/data/video_feeds/` or set a live RTSP URL, then:

```bash
# GPU
python scripts/run_video_processors.py --device cuda:0

# CPU only
python scripts/run_video_processors.py --device cpu
```

### Production (Uvicorn)

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Training the Temporal Transformer

RailMind AI includes a Temporal Transformer training pipeline with validation loss, accuracy, and classification-report metrics.

### Quick Train (CLI)

```bash
cd backend

# Train the 4-class behavior classifier
python -m app.transformer.train --data_path path/to/training.jsonl

# Train the behavior classifier explicitly
python -m app.transformer.train --data_path path/to/training.jsonl --epochs 50 --batch_size 16
```

### API-Based Training (Production)

```bash
# Trigger training
curl -X POST http://localhost:8000/api/training/trigger \
 -H "Content-Type: application/json" \
 -d '{"model_type": "all", "epochs": 30, "batch_size": 32}'

# Monitor progress
curl http://localhost:8000/api/training/runs/1

# Check system status
curl http://localhost:8000/api/training/status
```

### Automated Weekly Retraining

The scheduler automatically retrains the behavior classifier **every Sunday at 2 AM UTC** using operator-labelled false positives accumulated during the week. Target: 2-3% accuracy improvement per quarter.

### Trained Model Files

Models are saved to `backend/app/transformer/saved_models/`:

```
transformer/saved_models/
 behaviour_transformer.pt
 feature_scaler.pkl
```

---

## API Reference

Full interactive docs available at `http://localhost:8000/docs` (Swagger UI) and `/redoc` (ReDoc).
All REST endpoints under `/api/*` require the `X-API-Key` header configured by `RAILMIND_API_KEY`.

### Core Endpoints

| Method | Endpoint                                 | Description                                                      |
| ------ | ---------------------------------------- | ---------------------------------------------------------------- |
| `GET`  | `/api/incidents`                         | List incidents — filter by date, platform, status, category      |
| `GET`  | `/api/incidents/{id}`                    | Full incident detail with transformer output and agent reasoning |
| `POST` | `/api/incidents/{id}/ack`                | Staff acknowledges alert — clears escalation timer               |
| `POST` | `/api/incidents/{id}/feedback`           | Submit false positive flag                                       |
| `GET`  | `/api/analytics/heatmap`                 | Spatial heatmap data                                             |
| `GET`  | `/api/analytics/summary`                 | Aggregated stats: daily/weekly/monthly                           |
| `GET`  | `/api/analytics/transformer-performance` | Transformer accuracy, false positive rate, confidence            |
| `GET`  | `/api/alerts/active`                     | All unacknowledged active alerts                                 |
| `POST` | `/api/alerts/{id}/escalate`              | Manually escalate an alert                                       |
| `GET`  | `/api/platforms`                         | All monitored platforms and camera status                        |
| `GET`  | `/api/staff/available`                   | Available staff by platform zone                                 |
| `WS`   | `/ws/alerts`                             | Real-time alert event stream                                     |
| `WS`   | `/ws/feed/{camera_id}`                   | Live annotated video feed stream                                 |

### WebSocket Alert Payload

```json
{
  "alert_id": "uuid-v4",
  "timestamp": "2026-01-15T14:32:07Z",
  "platform": "Platform 3B",
  "camera_id": "CAM_003",
  "risk_score": 88,
  "risk_category": "Suicide Risk",
  "transformer_confidence": 0.91,
  "track_id": 142,
  "location": { "x": 0.72, "y": 0.41, "zone": "edge" },
  "recommended_action": "Approach immediately and offer assistance",
  "reasoning_summary": "30s edge proximity + pacing ×4 + social withdrawal",
  "escalation_level": 1,
  "escalate_at": "2026-01-15T14:33:07Z"
}
```

---

## Dashboard & Screenshots

The React dashboard provides a centralised monitoring interface accessible from any browser. Below are screenshots of the four main views.

---

### Live Monitoring

Real-time view of all active CCTV feeds with AI-annotated bounding boxes, track IDs, and live risk classifications overlaid directly on the video stream.

![Live Monitoring — Real-time CCTV feeds with AI-annotated detections](assets/live.png)

**Key features:**

- 2×2 grid of simultaneous live feeds (expandable to full-screen per camera)
- Colour-coded bounding boxes: High Risk · Medium Risk · Normal
- Inline risk labels: Suicide Risk, Pickpocketing Risk, Security Threat, Loitering Detected
- Live Detections panel with real-time scrolling alert feed
- Summary bar: Total CCTV feeds · People detected · Active alerts · High-risk count
- `+ Add CCTV Feed` for on-the-fly camera registration

---

### Dashboard

Analytics overview aggregating incident data across all platforms and cameras.

![Dashboard — Analytics overview with incident trends, heatmaps, and CCTV summary](assets/dashboard.png)

**Key features:**

- KPI cards: Total Incidents · Active Alerts · Suicide Risk · Pickpocketing Risk · Security Threats (all with day-over-day delta)
- **Incidents by CCTV** — donut chart breakdown per camera feed
- **Incident Trend (Last 7 Days)** — multi-line chart by risk category
- **Risk Distribution** — donut chart: Suicide Risk 26.7% · Pickpocketing 40% · Security Threat 33.3%
- **Platform Heatmap** — spatial risk-intensity overlay across all platforms (Low → Very High)
- **Peak Risk Hours** — histogram identifying 12:00 PM – 4:00 PM as the highest-risk window
- **Recent Alerts** — thumbnail feed of latest detections with risk level tags
- **CCTV Summary table** — per-camera status, incident counts, last incident time, and risk level

---

### Alerts

Centralised alert management interface for security staff to triage, acknowledge, and resolve incidents.

![Alerts — Full alert list with risk scores, status tracking, and incident detail panel](assets/alerts.png)

**Key features:**

- Tab navigation: All Alerts (28) · High Risk (8) · Medium Risk (13) · Low Risk (7) · Resolved (15)
- Sortable table: Alert ID · CCTV Feed · Platform · Type · Risk Score · Time · Status · Action
- Colour-coded risk score badges (91% red → 15% green)
- One-click **Acknowledge** and **Mark Resolved** actions
- **Alert Details panel** — right sidebar showing event type, description, CCTV clip preview, assigned staff dropdown, and escalation controls
- Filter and search across all active alerts
- Per-feed filtering via the **All CCTV Feeds** dropdown

---

### CCTV Feed Selector

Quick-access dropdown for filtering any view to a specific platform camera.

![CCTV Feed Selector — Per-platform camera filter dropdown](assets/alt2.png)

Supports instant switching between CCTV-1 through CCTV-5 across all dashboard views.

---

### Dashboard Module Summary

| Module                            | Description                                                              |
| --------------------------------- | ------------------------------------------------------------------------ |
| **Live Alert Feed**               | Real-time scrolling list of active alerts with one-click acknowledgement |
| **Platform Grid**                 | All monitored platforms showing camera status and current risk level     |
| **Incident History**              | Searchable log with full transformer output and agent reasoning traces   |
| **Heatmap Visualisation**         | Spatial incident density overlaid on platform diagrams                   |
| **Temporal Analytics**            | Incident trends by hour, day, and week with peak window identification   |
| **Transformer Performance Panel** | Accuracy, false positive rate, and confidence distribution               |
| **Staff Response Metrics**        | Acknowledgement times, resolution rates, per-operator trends             |

---

## Edge Deployment

For production deployment on **NVIDIA Jetson Orin Nano**:

| Component            | Location | Rationale                                       |
| -------------------- | -------- | ----------------------------------------------- |
| YOLOv8 Detection     | Edge     | Raw video stays local — zero bandwidth cost     |
| ByteTrack            | Edge     | Per-frame continuity requires local state       |
| YOLOv8-Pose          | Edge     | Latency-sensitive; feeds directly into features |
| Feature Extraction   | Edge     | Compact output: 7 floats vs full video stream   |
| Temporal Transformer | Edge     | PyTorch inference; edge deployment is planned   |
| Reasoning Agent      | Cloud    | Requires LLM + historical incident data         |
| Dashboard            | Cloud    | Multi-station aggregation                       |

### Jetson Orin Nano Specs

| Parameter             | Value                                    |
| --------------------- | ---------------------------------------- |
| Device cost           | ~$500 USD                                |
| YOLOv8n FPS           | 30+ FPS with TensorRT FP16               |
| Transformer inference | Not benchmarked in the current prototype |
| Bandwidth saving      | ~99.9% vs raw video streaming            |
| Offline buffer        | 24 hours if cloud connectivity lost      |

---

## Privacy & Ethics

Privacy is a **foundational design constraint**, not an afterthought.

| Principle                   | Implementation                                                                                   |
| --------------------------- | ------------------------------------------------------------------------------------------------ |
| **No Facial Recognition**   | Face detection models are explicitly excluded; analysis uses body movement and posture only      |
| **No Biometric Storage**    | Track IDs are numeric, session-scoped integers — expires when session ends                       |
| **Minimal Data Retention**  | Raw video retained 72 hours by default; only flagged clips archived up to 30 days                |
| **Behaviour-Only Analysis** | Transformer feature vector contains only anonymised movement metrics                             |
| **Human-in-the-Loop**       | All alerts require human staff confirmation — AI recommends, humans decide                       |
| **Transparent Reasoning**   | Every incident record includes transformer confidence, risk score, and LangGraph reasoning trace |
| **Regulatory Alignment**    | Designed for GDPR (EU), PDPA (India), and equivalent frameworks                                  |
| **Bias Monitoring**         | Regular audits of alert rates by platform, time, and incident type                               |

---

## Testing

```bash
# Backend unit tests
cd backend
pytest

# Run specific test modules
pytest tests/test_agents.py
pytest tests/test_transformer_pipeline.py
pytest tests/test_risk_scoring.py
pytest tests/test_cv.py

# Frontend E2E tests (requires both servers running)
cd frontend
npm run e2e
```

### Test Coverage

| Module                | Tests                             |
| --------------------- | --------------------------------- |
| Agent pipeline        | `test_agents.py`                  |
| Temporal Transformer  | `test_transformer_pipeline.py`    |
| Risk scoring          | `test_risk_scoring.py`            |
| CV pipeline           | `test_cv.py`                      |
| Alert system          | `test_alerts.py`                  |
| Incident & escalation | `test_incident_and_escalation.py` |
| Heatmap               | `test_heatmap.py`                 |
| Dashboard trends      | `test_dashboard_trend.py`         |
| Reliability           | `test_reliability.py`             |
| Frontend E2E          | `tests/e2e/feeds.spec.ts`         |

---

## Database Schema

Core tables in PostgreSQL (SQLite for development):

```sql
incidents — id, track_id, timestamp, platform_id, risk_score, risk_category, transformer_confidence, status
alerts — id, incident_id, alert_type, sent_at, acknowledged_at, staff_id, escalation_level
tracks — id, track_id, camera_id, session_id, feature_sequence_json, transformer_label, confidence
analytics — id, date, hour, platform_id, incident_count, avg_risk_score, false_positive_count
staff — id, name, platform_zone, contact_email, contact_phone, is_available
platforms — id, station_id, platform_number, camera_ids_json, edge_zone_config_json
feedback — id, alert_id, staff_id, is_false_positive, notes, submitted_at
```

---

## Roadmap

### v1.0 — Hackathon MVP

- [x] Recorded video processing pipeline
- [x] YOLOv8 + ByteTrack + Pose estimation
- [x] Temporal Transformer behaviour classifier
- [x] LangGraph Perception + Reasoning + Intervention agents
- [x] SQLite storage
- [x] React dashboard with live alerts

### v1.5 — Production Alpha

- [x] Live RTSP stream integration
- [x] PostgreSQL + Redis migration
- [x] WebSocket real-time alert delivery
- [x] Email (SMTP) + SMS (Twilio) notifications
- [x] Edge deployment on Jetson Orin Nano
- [x] Operator false positive feedback loop
- [x] Transformer confidence thresholding + temporal confirmation

### v2.0 — Production Release

- [ ] Transformer continual learning pipeline (weekly retraining)
- [ ] Multi-camera person re-identification
- [ ] Automated PA system integration for critical alerts
- [ ] Mobile app for railway staff (React Native)
- [ ] Multi-station SaaS dashboard
- [ ] Compliance reporting and audit log exports
- [ ] Bias monitoring and periodic model audits

### v3.0 — Advanced Intelligence

- [ ] Predictive analytics — forecast high-risk time windows
- [ ] Crowd flow optimisation recommendations
- [ ] Integration with emergency services dispatch
- [ ] Cross-network anonymised incident pattern sharing
- [ ] Video Swin Transformer for spatio-temporal modelling
- [ ] Reinforcement learning for dynamic threshold optimisation

---

## Tech Stack

### Backend

| Library              | Purpose                                   |
| -------------------- | ----------------------------------------- |
| Python 3.11+         | Core language                             |
| FastAPI + Uvicorn    | Async REST API                            |
| SQLAlchemy + Alembic | ORM + migrations                          |
| LangGraph            | Multi-agent orchestration                 |
| PyTorch              | Temporal Transformer training & inference |
| Ultralytics YOLOv8   | Detection, pose, tracking                 |
| OpenCV               | Video decode/preprocess                   |
| smtplib              | Email alerts                              |
| Twilio               | SMS escalation                            |

### Frontend

| Library                 | Purpose                |
| ----------------------- | ---------------------- |
| React 19                | UI                     |
| TanStack Router / Query | Routing + server state |
| Tailwind CSS 4          | Styling                |
| Recharts                | Analytics charts       |
| shadcn/ui               | Component library      |
| Socket.io Client        | Real-time alerts       |

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

# Temporal Transformer behaviour label thresholds
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

## Training the Temporal Transformer

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

Training data is generated synthetically from rule-based behavioural definitions — see `backend/app/transformer/train.py`. Swapping in real labelled incident data is the top priority before any production claim about accuracy.

---

## API Reference

All routes are prefixed with `/api` unless noted. Selected endpoints:

| Method | Endpoint                             | Description                             |
| ------ | ------------------------------------ | --------------------------------------- |
| GET    | `/incidents`                         | List incidents (filterable)             |
| GET    | `/incidents/{id}`                    | Full incident detail                    |
| POST   | `/incidents/{id}/acknowledge`        | Staff acknowledges an incident          |
| POST   | `/incidents/{id}/resolve`            | Mark an incident resolved               |
| POST   | `/incidents/{id}/false-positive`     | Flag a false positive                   |
| GET    | `/alerts`                            | List alerts                             |
| GET    | `/alerts/stats`                      | Alert statistics                        |
| PATCH  | `/alerts/{id}/acknowledge`           | Acknowledge an alert                    |
| PATCH  | `/alerts/{id}/resolve`               | Resolve an alert                        |
| PATCH  | `/alerts/{id}/assign`                | Assign an alert to staff                |
| GET    | `/dashboard/stats`                   | Headline dashboard metrics              |
| GET    | `/dashboard/trend`                   | Incident trend over time                |
| GET    | `/dashboard/risk-distribution`       | Risk category breakdown                 |
| GET    | `/dashboard/heatmap`                 | Spatial heatmap data                    |
| GET    | `/dashboard/cctv-summary`            | Per-camera summary                      |
| GET    | `/analytics/transformer-performance` | Transformer accuracy/confidence metrics |
| GET    | `/feeds`                             | List camera feeds                       |
| POST   | `/feeds/upload`                      | Upload a video file for processing      |
| GET    | `/feeds/{id}/stream`                 | Stream a processed feed                 |
| GET    | `/staff/available`                   | Available staff                         |
| POST   | `/training/trigger`                  | Trigger Temporal Transformer retraining |
| GET    | `/health`                            | Health check                            |
| WS     | `/ws/alerts`                         | Real-time alert stream                  |

Full route definitions live in `backend/app/api/routes/`.

---

## Testing

```bash
cd backend
pytest                       # full suite — 57 tests, all passing as of this build
pytest tests/test_agents.py
pytest tests/test_transformer_pipeline.py
pytest tests/test_risk_scoring.py
pytest tests/test_cv.py
```

| Test file                         | Covers                                                 |
| --------------------------------- | ------------------------------------------------------ |
| `test_agents.py`                  | Agent pipeline (perception → reasoning → intervention) |
| `test_transformer_pipeline.py`    | Temporal Transformer model loading and inference       |
| `test_risk_scoring.py`            | Risk score computation                                 |
| `test_cv.py`                      | CV pipeline behaviour and degradation handling         |
| `test_alerts.py`                  | Alert lifecycle                                        |
| `test_incident_and_escalation.py` | Incident creation and escalation timers                |
| `test_heatmap.py`                 | Heatmap analytics                                      |
| `test_dashboard_trend.py`         | Dashboard trend data                                   |
| `test_reliability.py`             | Failure-mode handling                                  |
| `test_api_auth.py`                | API authentication                                     |
| `test_feeds.py`                   | Feed registration and upload                           |

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
│   │   ├── transformer/     # Model definition, training, inference
│   │   ├── api/routes/      # FastAPI endpoints
│   │   ├── services/        # Risk scoring, alerts, escalation, notifications
│   │   ├── analytics/       # Dashboard metrics, heatmaps
│   │   ├── models/          # SQLAlchemy models
│   │   └── core/             # Config, database, WebSocket manager
│   ├── transformer/saved_models/ # Trained checkpoint + scaler
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
- [x] Temporal Transformer behaviour classifier with saved weights
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
- [ ] Temporal Transformer retrained on real, labelled incident data
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
