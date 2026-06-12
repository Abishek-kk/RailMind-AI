<div align="center">

<img src="https://img.shields.io/badge/RailMind_AI-v2.0-0A84FF?style=for-the-badge&logo=railway&logoColor=white" alt="RailMind AI"/>

# RailMind AI
### Intelligent Railway Safety & Security System

**Transforming passive CCTV infrastructure into proactive, life-saving intelligence.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.9-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)](https://pytorch.org)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-00CFFF?style=flat-square)](https://ultralytics.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.5-1C1C1C?style=flat-square)](https://langchain-ai.github.io/langgraph/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![FAR AWAY 2026](https://img.shields.io/badge/FAR_AWAY_2026-Hackathon-FF6B35?style=flat-square)](https://faraway2026.com)

<br/>

> **"Most incidents could be prevented if high-risk behaviours were detected early enough for timely intervention."**
> — *RailMind AI Core Principle*

<br/>

[ Quick Start](#-quick-start) · [ Architecture](#-system-architecture) · [ API Reference](#-api-reference) · [ AI Pipeline](#-ai--computer-vision-pipeline) · [ Dashboard](#-dashboard--screenshots) · [ Privacy](#-privacy--ethics)

</div>

---

## Table of Contents

- [Overview](#-overview)
- [Key Metrics](#-key-metrics)
- [Features](#-features)
- [System Architecture](#-system-architecture)
- [AI & Computer Vision Pipeline](#-ai--computer-vision-pipeline)
- [LSTM Behaviour Classifier](#-lstm-behaviour-classifier)
- [Agentic AI Framework](#-agentic-ai-framework)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running the Application](#-running-the-application)
- [Training the LSTM Models](#-training-the-lstm-models)
- [API Reference](#-api-reference)
- [Dashboard & Screenshots](#-dashboard--screenshots)
- [Edge Deployment](#-edge-deployment)
- [Privacy & Ethics](#-privacy--ethics)
- [Testing](#-testing)
- [Roadmap](#-roadmap)
- [Team](#-team)

---

## Overview

**RailMind AI** is an agentic, AI-powered railway safety and security platform that converts **existing passive CCTV infrastructure** into an intelligent behavioural monitoring network — with **zero additional hardware**.

Using a multi-stage computer-vision pipeline combined with a **three-tier agentic reasoning architecture**, the system detects high-risk passenger behaviours in real time, calculates dynamic risk scores, and dispatches automated alerts to railway staff — all without facial recognition.

The platform addresses two critical railway challenges:

| Challenge | Solution |
|-----------|----------|
| **Suicide Prevention** | Edge proximity + pacing + withdrawal detection via BiLSTM temporal classifier |
| **Crime Detection** | Pickpocketing and suspicious following via crowd-interaction and following-distance analysis |

### Why RailMind AI?

Railway stations are high-density public spaces where critical incidents can occur with little warning. Despite extensive CCTV coverage, most surveillance systems are **reactive** — they record incidents rather than prevent them. Human operators monitoring dozens of feeds simultaneously miss critical behavioural cues. **RailMind AI closes that gap.**

---

## Key Metrics

| Metric | Target |
|--------|--------|
| End-to-end alert latency | **< 500 ms** |
| LSTM classification accuracy | **> 92%** on test set |
| False positive rate | **< 8%** |
| Hardware requirement | **Zero** — uses existing CCTV |
| Processing throughput | **10 FPS** per camera feed |
| LSTM inference time | **< 5 ms** on GPU |
| YOLOv8 inference time | **~12 ms** per frame |

---

## Features

<details>
<summary><strong> Real-Time Behavioural Analysis</strong></summary>

Continuously monitors all detected passengers, extracting movement patterns and behavioural features from every video frame with sub-second latency. Processes up to 10 FPS per camera feed.
</details>

<details>
<summary><strong> Suicide Risk Detection</strong></summary>

Detects distress indicators including:
- Prolonged platform-edge proximity (> 60s)
- Repetitive pacing cycles
- Sudden direction reversals
- Crouching postures
- Social withdrawal patterns
</details>

<details>
<summary><strong> Pickpocketing Detection</strong></summary>

Identifies suspicious crowd-targeting behaviours:
- Abnormal following distances (< 0.5m sustained)
- Repeated close-contact interactions
- Coordinated group movements near high-density zones
</details>

<details>
<summary><strong> Multi-Agent AI Architecture</strong></summary>

Three specialised LangGraph agents — **Perception**, **Reasoning**, and **Intervention** — work in sequence to detect, evaluate, and act upon identified risks with defined input/output contracts.
</details>

<details>
<summary><strong> LSTM Temporal Classifier</strong></summary>

Bidirectional LSTM network trained on 30-second behavioural sequences. Captures temporal patterns and trajectory evolution that static classifiers miss, enabling nuanced risk classification that dramatically reduces false positives.
</details>

<details>
<summary><strong> Dynamic Risk Scoring (0–100)</strong></summary>

Risk scores computed by combining:
- LSTM classification output
- Edge proximity distance
- Behaviour duration
- Location zone & crowd density
- Historical incident patterns
- Platform context multipliers
</details>

<details>
<summary><strong> Automated Staff Alerts & Escalation</strong></summary>

Real-time WebSocket notifications dispatched to nearest available staff with platform, risk category, confidence level, and recommended action. Unacknowledged high-risk alerts auto-escalate after **60 seconds**.
</details>

<details>
<summary><strong> Privacy-Preserving by Design</strong></summary>

No facial recognition. No biometric storage. Track IDs are numeric and session-scoped. GDPR and PDPA compatible.
</details>

---

## System Architecture

RailMind AI follows a **layered edge-cloud hybrid pipeline** where each stage processes the output of the previous stage, progressively transforming raw video into actionable intelligence.

```

 EDGE TIER (Jetson Orin Nano) 

 CCTV Feed → OpenCV → YOLOv8 Detection → ByteTrack → YOLOv8-Pose 
 ↓ 
 Feature Extraction (7 features) 
 ↓ 
 BiLSTM Classifier (30s window) 

 Compact JSON payload

 CLOUD TIER (FastAPI + PostgreSQL) 

 LangGraph Reasoning Agent → Intervention Agent → WebSocket Hub 
 ↓ 
 PostgreSQL / Redis → React Dashboard 

```

### Pipeline Stages

| Stage | Component | Tier | Description |
|-------|-----------|------|-------------|
| Input | CCTV Camera Feed | Edge | H.264/H.265 via RTSP/ONVIF |
| 1 | OpenCV Processing | Edge | Decode, normalise, preprocess frames |
| 2 | YOLOv8 Detection | Edge | Person detection with bounding boxes |
| 3 | ByteTrack | Edge | Persistent ID tracking across frames |
| 4 | YOLOv8-Pose | Edge | 17 COCO body keypoints per person |
| 5 | Feature Extraction | Edge | 7 behavioural features per 30s window |
| 6 | LSTM Classifier | Edge | Temporal sequence classification |
| 7 | Reasoning Agent | Cloud | LangGraph context-aware risk scoring |
| 8 | Intervention Agent | Cloud | Alert dispatch & escalation management |
| 9 | PostgreSQL/SQLite | Cloud | Incident & analytics storage |
| 10 | React Dashboard | Cloud | Live alerts, heatmaps, analytics |

---

## AI & Computer Vision Pipeline

### Model Specifications

| Model | Task | Architecture | Input | Latency |
|-------|------|-------------|-------|---------|
| YOLOv8n/s | Person Detection | CSPDarknet + PANet | 640×640 | ~12ms |
| ByteTrack | Multi-Object Tracking | Kalman + Hungarian | Detections | ~3ms |
| YOLOv8-Pose | Pose Estimation | YOLOv8 + Keypoint Head | 640×640 | ~15ms |
| BiLSTM | Behaviour Classification | 2-layer Bidirectional LSTM | [30×7] seq | <5ms |
| LangGraph Agent | Risk Reasoning | LLM + Conditional Graph | Structured JSON | ~200ms |

### Behavioural Feature Vector

Each tracked individual generates a **7-dimensional feature vector** per second, accumulated over a 30-second sliding window:

```python
feature_vector = [
 edge_proximity_seconds, # Cumulative time within 0.5m of platform edge
 loitering_time, # Stationary duration in a single spatial zone
 pacing_count, # Back-and-forth movement cycles detected
 movement_speed, # Average velocity (m/s) over 10s window
 direction_changes, # Heading reversals per minute
 following_distance, # Sustained proximity to a single individual (metres)
 crowd_interactions, # Unique close-contact individuals
]
```

---

## LSTM Behaviour Classifier

The LSTM classifier is the **analytical heart** of RailMind AI. Unlike static classifiers that evaluate a single snapshot, the LSTM processes a **30-second temporal sequence** — modelling how behaviour evolves over time.

### Architecture

```
Input [batch, 30, 7]
 ↓
BiLSTM Layer 1 (128 units) → Dropout (0.3)
 ↓
BiLSTM Layer 2 (64 units) → Dropout (0.3)
 ↓
Dense (32, ReLU)
 ↓
Dense (4, Softmax)
 ↓
Output: [Normal, Suicide Risk, Pickpocketing, Security Threat]
```

### Why BiLSTM Over Static Classifiers?

| Criterion | XGBoost (Static) | BiLSTM (RailMind AI) |
|-----------|-----------------|----------------------|
| Input | Single snapshot | 30-second sequence [30×7] |
| Temporal awareness | None | Full — models evolution |
| Detects gradual escalation | Cannot | Core capability |
| False positive rate | High | < 8% target |
| Production suitability | Prototype only | Production-grade |

### Risk Class Definitions

| Class | Trigger Pattern | Threshold |
|-------|----------------|-----------|
| Normal | Typical passenger movement | Confidence > 0.6 |
| Suicide Risk | Edge proximity >30s + pacing >3 cycles + low crowd interaction | Score > 40 |
| Pickpocketing Risk | Following <0.5m sustained + crowd interaction >4 + rapid contacts | Score > 45 |
| Security Threat | High speed + aggressive posture + confrontational proximity | Score > 50 |

### Training Strategy

```bash
# Loss: Categorical cross-entropy with class weighting (Suicide Risk 3× weight)
# Optimiser: Adam (lr=0.001) with ReduceLROnPlateau
# Data augmentation: Gaussian noise injection on feature sequences
# Split: Stratified 80/10/10 train/validation/test
```

---

## Agentic AI Framework

RailMind AI uses a **three-tier agentic architecture** built with LangGraph. Each agent has a defined role, strict input/output contract, and operates as a node in a compiled state graph.

```

 PERCEPTION → REASONING → INTERVENTION 
 AGENT AGENT AGENT 

 • Pose extract • Risk scoring • Threshold eval 
 • Feature comp • LLM reasoning • WebSocket alert 
 • LSTM infer • Score 0-100 • Email/SMS 
 • Action decide • Escalation timer 

```

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

# 3. Provide YOLOv8 pose weights
# Download yolov8n-pose.pt from https://github.com/ultralytics/assets
# Set POSE_MODEL_PATH in .env

# 4. Train LSTM models
python -m app.lstm.cli train

# 5. Start backend
python run.py

# 6. Set up and start frontend (new terminal)
cd ../frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) — the dashboard will be live.

---

## Installation

### Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.11+ |
| Node.js | 18+ |
| CUDA (optional) | 11.8+ for GPU inference |
| GPU (optional) | NVIDIA (recommended for production) |

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

Download `yolov8n-pose.pt` (speed) or `yolov8s-pose.pt` (accuracy):

```bash
# Via Python
python -c "from ultralytics import YOLO; YOLO('yolov8n-pose.pt')"

# Or download manually from:
# https://github.com/ultralytics/assets/releases
```

Set `POSE_MODEL_PATH=/path/to/yolov8n-pose.pt` in your `.env`.

---

## Configuration

All configuration is managed via environment variables in `backend/.env`:

```env
# Core 
DEBUG=True
DATABASE_URL=sqlite:///./railmind.db # Use PostgreSQL in production
SECRET_KEY=your-secret-key-change-in-production
LOG_LEVEL=INFO

# CV Models 
POSE_MODEL_PATH=./yolov8n-pose.pt
POSE_DEVICE=cuda:0 # or cpu
LSTM_SEQUENCE_LENGTH=30

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
OPENAI_API_KEY=sk-... # For GPT-4 reasoning
ANTHROPIC_API_KEY=sk-ant-... # For Claude reasoning

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

Place MP4 files in `backend/data/mock_feeds/` or set a live RTSP URL, then:

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

## Training the LSTM Models

RailMind AI includes a complete LSTM training pipeline with API-based, CLI, and scheduled retraining options.

### Quick Train (CLI)

```bash
cd backend

# Train all three classifiers
python -m app.lstm.cli train

# Train specific model
python -m app.lstm.cli train --type suicide_classifier
python -m app.lstm.cli train --type pickpocket_classifier
python -m app.lstm.cli train --type anomaly_classifier

# Custom parameters
python -m app.lstm.cli train --epochs 50 --batch-size 16

# Check training status
python -m app.lstm.cli status --latest
python -m app.lstm.cli status --history 10
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

The scheduler automatically retrains all models **every Sunday at 2 AM UTC** using operator-labelled false positives accumulated during the week. Target: 2–3% accuracy improvement per quarter.

### Trained Model Files

Models are saved to `backend/lstm/saved_models/`:

```
lstm/saved_models/
 suicide_classifier.pt
 pickpocket_classifier.pt
 anomaly_classifier.pt
 suicide_classifier_scaler.pkl
 pickpocket_classifier_scaler.pkl
 anomaly_classifier_scaler.pkl
```

---

## API Reference

Full interactive docs available at `http://localhost:8000/docs` (Swagger UI) and `/redoc` (ReDoc).

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/incidents` | List incidents — filter by date, platform, status, category |
| `GET` | `/api/incidents/{id}` | Full incident detail with LSTM output and agent reasoning |
| `POST` | `/api/incidents/{id}/ack` | Staff acknowledges alert — clears escalation timer |
| `POST` | `/api/incidents/{id}/feedback` | Submit false positive flag |
| `GET` | `/api/analytics/heatmap` | Spatial heatmap data |
| `GET` | `/api/analytics/summary` | Aggregated stats: daily/weekly/monthly |
| `GET` | `/api/analytics/lstm-performance` | LSTM accuracy, false positive rate, confidence |
| `GET` | `/api/alerts/active` | All unacknowledged active alerts |
| `POST` | `/api/alerts/{id}/escalate` | Manually escalate an alert |
| `GET` | `/api/platforms` | All monitored platforms and camera status |
| `GET` | `/api/staff/available` | Available staff by platform zone |
| `WS` | `/ws/alerts` | Real-time alert event stream |
| `WS` | `/ws/feed/{camera_id}` | Live annotated video feed stream |

### WebSocket Alert Payload

```json
{
 "alert_id": "uuid-v4",
 "timestamp": "2026-01-15T14:32:07Z",
 "platform": "Platform 3B",
 "camera_id": "CAM_003",
 "risk_score": 88,
 "risk_category": "Suicide Risk",
 "lstm_confidence": 0.91,
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

<<<<<<< HEAD
![Live Monitoring — Real-time CCTV feeds with AI-annotated detections](assets/live.png)
=======
![Live Monitoring — Real-time CCTV feeds with AI-annotated detections](live.png)
>>>>>>> c9f80055ddfbc127771a7e7610e59eca994c414a

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

<<<<<<< HEAD
![Dashboard — Analytics overview with incident trends, heatmaps, and CCTV summary](assets/dashboard.png)
=======
![Dashboard — Analytics overview with incident trends, heatmaps, and CCTV summary](dashboard.png)
>>>>>>> c9f80055ddfbc127771a7e7610e59eca994c414a

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

<<<<<<< HEAD
![Alerts — Full alert list with risk scores, status tracking, and incident detail panel](assets/alerts.png)
=======
![Alerts — Full alert list with risk scores, status tracking, and incident detail panel](alearts.png)
>>>>>>> c9f80055ddfbc127771a7e7610e59eca994c414a

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

<<<<<<< HEAD
![CCTV Feed Selector — Per-platform camera filter dropdown](assets/alt2.png)
=======
![CCTV Feed Selector — Per-platform camera filter dropdown](alt2.png)
>>>>>>> c9f80055ddfbc127771a7e7610e59eca994c414a

Supports instant switching between CCTV-1 through CCTV-5 across all dashboard views.

---

### Dashboard Module Summary

| Module | Description |
|--------|-------------|
| **Live Alert Feed** | Real-time scrolling list of active alerts with one-click acknowledgement |
| **Platform Grid** | All monitored platforms showing camera status and current risk level |
| **Incident History** | Searchable log with full LSTM output and agent reasoning traces |
| **Heatmap Visualisation** | Spatial incident density overlaid on platform diagrams |
| **Temporal Analytics** | Incident trends by hour, day, and week with peak window identification |
| **LSTM Performance Panel** | Real-time accuracy, false positive rate, confidence distribution |
| **Staff Response Metrics** | Acknowledgement times, resolution rates, per-operator trends |

---

## Edge Deployment

For production deployment on **NVIDIA Jetson Orin Nano**:

| Component | Location | Rationale |
|-----------|----------|-----------|
| YOLOv8 Detection | Edge | Raw video stays local — zero bandwidth cost |
| ByteTrack | Edge | Per-frame continuity requires local state |
| YOLOv8-Pose | Edge | Latency-sensitive; feeds directly into features |
| Feature Extraction | Edge | Compact output: 7 floats vs full video stream |
| LSTM Classifier | Edge | TensorRT-optimised; < 5ms on Jetson |
| Reasoning Agent | Cloud | Requires LLM + historical incident data |
| Dashboard | Cloud | Multi-station aggregation |

### Jetson Orin Nano Specs

| Parameter | Value |
|-----------|-------|
| Device cost | ~$500 USD |
| YOLOv8n FPS | 30+ FPS with TensorRT FP16 |
| LSTM inference | < 5ms per sequence |
| Bandwidth saving | ~99.9% vs raw video streaming |
| Offline buffer | 24 hours if cloud connectivity lost |

---

## Privacy & Ethics

Privacy is a **foundational design constraint**, not an afterthought.

| Principle | Implementation |
|-----------|---------------|
| **No Facial Recognition** | Face detection models are explicitly excluded; analysis uses body movement and posture only |
| **No Biometric Storage** | Track IDs are numeric, session-scoped integers — expires when session ends |
| **Minimal Data Retention** | Raw video retained 72 hours by default; only flagged clips archived up to 30 days |
| **Behaviour-Only Analysis** | LSTM feature vector contains only anonymised movement metrics |
| **Human-in-the-Loop** | All alerts require human staff confirmation — AI recommends, humans decide |
| **Transparent Reasoning** | Every incident record includes full LSTM confidence, risk score, and LangGraph reasoning trace |
| **Regulatory Alignment** | Designed for GDPR (EU), PDPA (India), and equivalent frameworks |
| **Bias Monitoring** | Regular audits of alert rates by platform, time, and incident type |

---

## Testing

```bash
# Backend unit tests
cd backend
pytest

# Run specific test modules
pytest tests/test_agents.py
pytest tests/test_lstm.py
pytest tests/test_risk_scoring.py
pytest tests/test_cv.py

# Frontend E2E tests (requires both servers running)
cd frontend
npm run e2e
```

### Test Coverage

| Module | Tests |
|--------|-------|
| Agent pipeline | `test_agents.py` |
| LSTM model | `test_lstm.py` |
| Risk scoring | `test_risk_scoring.py` |
| CV pipeline | `test_cv.py` |
| Alert system | `test_alerts.py` |
| Incident & escalation | `test_incident_and_escalation.py` |
| Heatmap | `test_heatmap.py` |
| Dashboard trends | `test_dashboard_trend.py` |
| Reliability | `test_reliability.py` |
| Frontend E2E | `tests/e2e/feeds.spec.ts` |

---

## Database Schema

Core tables in PostgreSQL (SQLite for development):

```sql
incidents — id, track_id, timestamp, platform_id, risk_score, risk_category, lstm_confidence, status
alerts — id, incident_id, alert_type, sent_at, acknowledged_at, staff_id, escalation_level
tracks — id, track_id, camera_id, session_id, feature_sequence_json, lstm_label, confidence
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
- [x] Bidirectional LSTM behaviour classifier
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
- [x] LSTM confidence thresholding + temporal confirmation

### v2.0 — Production Release 
- [ ] LSTM continual learning pipeline (weekly retraining)
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
| Library | Purpose |
|---------|---------|
| Python 3.11+ | Core application language |
| FastAPI | High-performance async REST API |
| LangGraph 0.5 | Multi-agent orchestration |
| PyTorch 2.9 | LSTM model training & inference |
| Ultralytics YOLOv8 | Person detection + pose estimation |
| ByteTrack | Multi-object tracking |
| OpenCV | Video stream capture & preprocessing |
| SQLAlchemy + Alembic | ORM + schema migrations |
| APScheduler | Background job scheduling |
| Twilio | SMS escalation alerts |

### Frontend
| Library | Purpose |
|---------|---------|
| React 19 | Component-based UI |
| TanStack Router | Type-safe client-side routing |
| TanStack Query | Server state management |
| Tailwind CSS 4 | Utility-first styling |
| Recharts | Analytics charts |
| shadcn/ui | Accessible component library |
| Socket.io Client | Real-time WebSocket alerts |

---

## Project Structure

```
RailMind-AI/
 backend/
 app/
 agents/ # LangGraph multi-agent pipeline
 agent_graph.py
 perception_agent.py
 reasoning_agent.py
 intervention_agent.py
 cv/ # Computer vision pipeline
 video_processor.py
 pose_estimator.py
 lstm_behavior.py
 features/ # Behavioural feature detectors
 edge_proximity.py
 loitering_detector.py
 pacing_detector.py
 following_detector.py
 movement_analyzer.py
 lstm/ # LSTM model definition & training
 model.py
 trainer.py
 predictor.py
 cli.py
 api/routes/ # FastAPI route handlers
 services/ # Business logic services
 analytics/ # Dashboard metrics & heatmaps
 models/ # SQLAlchemy database models
 core/ # Config, database, WebSocket manager
 training/ # Training scripts & notebooks
 tests/ # Pytest test suite
 requirements.txt
 frontend/
 src/
 routes/ # Dashboard, alerts, live feed pages
 components/ # Reusable UI components
 lib/api/ # API client functions
 hooks/ # Custom React hooks
 tests/e2e/ # Playwright E2E tests
 README.md
```

---

## Team

**Team Accelerate** — FAR AWAY 2026 Hackathon

> Built for the **FAR AWAY 2026 International Hackathon** with a focus on real-world deployment viability, privacy-first architecture, and life-saving impact.

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgements

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) — object detection and pose estimation
- [LangGraph](https://github.com/langchain-ai/langgraph) — multi-agent orchestration framework
- [ByteTrack](https://github.com/ifzhang/ByteTrack) — multi-object tracking algorithm
- [PyTorch](https://pytorch.org) — deep learning framework
- [FastAPI](https://fastapi.tiangolo.com) — modern async Python web framework

---

<div align="center">

**RailMind AI** — Making railway stations safer, one frame at a time.

*Built with by Team Accelerate for FAR AWAY 2026*

<<<<<<< HEAD
</div>
=======
</div>
>>>>>>> c9f80055ddfbc127771a7e7610e59eca994c414a
