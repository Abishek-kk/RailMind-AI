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

#  RailMind-AI

**Turning existing CCTV infrastructure into a real-time railway safety assistant.**

RailMind-AI is an intelligent behavioural-safety system that watches railway station CCTV feeds and flags dangerous situations *before* they escalate — without using facial recognition or identifying anyone personally.

Built by **Team Accelerate**.

---

##  Table of Contents

- [In Plain Terms](#-in-plain-terms)
- [The Problem](#-the-problem)
- [Our Solution](#-our-solution)
- [How It Works (Technical)](#-how-it-works-technical)
- [Tech Stack](#-tech-stack)
- [System Flow](#-system-flow)
- [What Makes RailMind Different](#-what-makes-railmind-different)
- [Responsible AI](#-responsible-ai)
- [Roadmap](#-roadmap)
- [Getting Started](#-getting-started)
- [Glossary](#-glossary)
- [Team](#-team)
- [License](#-license)

---

##  In Plain Terms

Imagine a railway station with dozens of CCTV cameras. Every camera is recording — but nobody can watch all of them at once. If someone wanders too close to the platform edge, enters a restricted area, or lingers somewhere unusual for too long, a human operator might simply miss it in the middle of everything else on screen.

**RailMind-AI acts like a second pair of eyes that never gets tired.**

It watches the *same* CCTV footage a station already has, notices unusual or risky behaviour (not who the person is — just *what they're doing*), and immediately shows the operator: "look at this camera, right now, here's why."

Think of it less like a surveillance system and more like a **smoke detector for unsafe human behaviour** — quiet most of the time, but instantly alert when something needs attention.

No new cameras. No face database. Just smarter use of what's already there.

##  The Problem

Railway stations are crowded, fast-moving environments where a dangerous situation can develop in seconds — someone moving toward a platform edge, entering a restricted zone, or lingering somewhere unusual. Meanwhile, one operator is often expected to monitor dozens of screens at once.

This creates three recurring failure points:

| Challenge | What it means in practice |
|---|---|
| **Attention fatigue** | A human simply cannot watch 30+ screens with equal focus, all day |
| **Delayed detection** | By the time a risky moment is *noticed*, it may already be too late |
| **Missed patterns** | Danger often isn't visible in one frame — it's a *pattern* across many frames (e.g., pacing, lingering, repeated direction changes) |

Traditional CCTV is great at answering **"what happened?"** after the fact. RailMind-AI is built to answer a harder, more useful question: **"is something dangerous developing right now?"**

##  Our Solution

RailMind is built on one guiding philosophy:

> **We don't watch *who* you are. We watch *what* you do.**

Instead of facial recognition, the system studies movement, body posture, position, and timing — the same visual cues a trained human observer would notice, but applied consistently, across every camera, all the time.

Existing CCTV footage passes through a six-stage AI pipeline that turns raw video into a clear, explained alert on a dashboard.

##  How It Works (Technical)

| Stage | What it does | In plain terms |
|---|---|---|
| **1. Detection** — YOLOv8 | Detects every person present in each video frame | "There are people here, and here's exactly where." |
| **2. Tracking** — ByteTrack | Assigns a persistent ID to each person across frames | "That's the same person as three seconds ago, just moved." |
| **3. Pose Estimation** — YOLOv8-Pose | Extracts body keypoints (joints, posture) per person | "Here's how their body is positioned and moving — no face needed." |
| **4. Behaviour Analysis** | Combines movement, position, and time into behavioural signals — zone entry, dwell time, pacing, direction changes | "This isn't just standing still — it's *lingering* near the edge for 40 seconds." |
| **5. Risk Scoring** | Compares observed behaviour against defined safety thresholds | "This pattern crosses the line from 'normal' to 'needs attention.'" |
| **6. Alerting** | Sends the flagged event to the live staff dashboard in real time | "Camera 7, Platform 2 — here's what to look at and why." |

##  Tech Stack

| Layer | Technology | Role |
|---|---|---|
| Person Detection | **YOLOv8** | Finds people in each frame |
| Pose Estimation | **YOLOv8-Pose** | Extracts body keypoints |
| Multi-Object Tracking | **ByteTrack** | Follows individuals across frames |
| Behaviour Modelling | **PyTorch** | Learns and classifies behavioural patterns |
| Video Processing | **OpenCV** | Handles frame extraction and preprocessing |
| Real-Time Communication | **FastAPI + WebSockets** | Streams live events to the frontend |
| Monitoring Dashboard | **React** | Displays live alerts to station staff |

##  System Flow

```
Camera  →  Detection  →  Tracking  →  Pose  →  Behaviour  →  Risk  →  Alert  →  Human Action
```

- **Detection** tells us *what* is present
- **Tracking** tells us *where* it moves
- **Pose** tells us *how* the body is positioned
- **Behaviour Analysis** tells us *what is changing* over time
- **Risk Scoring** tells us *when* that behaviour becomes significant
- **Dashboard** tells the operator: *this is what needs your attention, and why*

**The AI detects the signal. The human makes the decision.**

##  What Makes RailMind Different

-  **Explainable, not mysterious** — every alert says exactly *why* it fired ("prolonged presence in danger zone," "abnormal pacing detected"), never a vague "AI flagged danger"
-  **Privacy by design** — behaviour is analysed, faces and identities are not
-  **Works with what already exists** — a software layer on top of current CCTV, not a hardware replacement
-  **Keeps humans in charge** — reduces what an operator has to watch manually, but never makes the final call itself

##  Responsible AI

RailMind-AI does **not** claim to read a person's intentions, and it does **not** claim to predict suicide or any specific outcome. It detects **observable behavioural risk signals** — patterns that may precede unsafe situations — so that a trained human can make an informed decision faster. Safety-critical AI should support human judgement, never replace it with unverified assumptions.

##  Roadmap

-  Extend coverage across multiple CCTV feeds and railway platforms simultaneously
-  Move inference closer to the source using edge devices, reducing bandwidth needs
-  Explore network-level behavioural intelligence across stations — still without using personal identity

##  Getting Started

> Update this section with your actual setup steps once finalized.

```bash
# Clone the repository
git clone <repo-url>
cd railmind-ai

# Backend setup
pip install -r requirements.txt

# Frontend setup
cd frontend
npm install
npm run dev
```

##  Glossary

*A few terms in plain language, for non-technical readers/judges.*

| Term | Plain-language meaning |
|---|---|
| **YOLOv8** | An AI model that spots people (and their poses) in a video frame, very quickly |
| **ByteTrack** | An algorithm that keeps track of "this is the same person" as they move across frames |
| **Pose estimation** | Mapping a person's body position (joints, posture) without identifying their face |
| **Behavioural signal** | A pattern of movement over time — like lingering, pacing, or repeated direction changes |
| **Risk threshold** | The point at which a behaviour pattern is considered concerning enough to alert a human |
| **Edge device** | A small on-site computer that can run AI locally, near the camera, instead of a distant server |

##  Team

**Team Accelerate**
- Abishek K (Lead)
- Badhrı Prasath D R
- Gauri
- Gaurika
---

*RailMind-AI — See. Understand. Alert.*

<div align="center">

Built for the FAR AWAY 2026 Hackathon by Team Accelerate.

</div>
