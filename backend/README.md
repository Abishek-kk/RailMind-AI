# TeamAccelerate Backend

AI-powered platform monitoring and anomaly detection system for railway safety and security.

## Project Structure

```
backend/
├── app/                     # Main application code
│   ├── api/                # FastAPI routes and endpoints
│   ├── agents/             # Multi-agent system for decision-making
│   ├── core/               # Core config, database, constants
│   ├── cv/                 # Computer vision (detection, tracking, pose)
│   ├── features/           # Behavior detection modules
│   │   ├── edge_proximity.py        # Edge safety detection
│   │   ├── pacing_detector.py       # Repetitive movement detection
│   │   ├── loitering_detector.py    # Stationary person detection
│   │   ├── following_detector.py    # Suspicious following detection
│   │   └── movement_analyzer.py     # Movement pattern analysis
│   ├── lstm/               # LSTM models for behavior classification
│   ├── analytics/          # Dashboard metrics and analytics
│   ├── models/             # Database models
│   ├── schemas/            # Pydantic validation schemas
│   ├── services/           # Business logic services
│   └── utils/              # Utility functions and validators
├── training/               # Model training and datasets
│   ├── datasets/           # Training data by behavior type
│   │   ├── normal/
│   │   ├── suicide_risk/
│   │   ├── pickpocketing/
│   │   ├── loitering/
│   │   ├── track_intrusion/
│   │   └── suspicious_following/
│   ├── notebooks/          # Jupyter notebooks for analysis
│   └── scripts/            # Training and data preparation scripts
├── data/                   # Runtime data
│   ├── railmind.db         # SQLite database
│   └── mock_feeds/         # Sample video feeds
├── tests/                  # Test suite
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
├── .gitignore             # Git ignore patterns
└── README.md              # This file
```

## Features

- Real-time video feed processing
- Multi-behavior anomaly detection:
  - Suicide risk detection
  - Pickpocketing detection
  - Loitering/trespassing detection
  - Track intrusion detection
  - Suspicious following detection
  - Edge proximity warnings
- LSTM-based sequence analysis
- Multi-agent decision-making system
- Pose estimation and object tracking
- Movement pattern analysis
- Risk scoring and alert management
- Analytics and heatmaps
- WebSocket support for live updates
- RESTful API endpoints

## Setup

1. Clone the repository
2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
5. Run the application:
   ```bash
   python app/main.py
   ```

## API Endpoints

- `GET /health` - Health check
- `GET /alerts` - Get all alerts
- `POST /alerts` - Create new alert
- `GET /feeds` - Get all feeds
- `GET /dashboard` - Dashboard data

## Testing

Run tests with:
```bash
pytest
```

## License

Proprietary - TeamAccelerate

## Quickstart (Local Prototype)

Start the backend FastAPI server (from repository root):

```bash
# Activate your venv first
f:/teamaccelerate/.venv/Scripts/Activate.ps1  # PowerShell (Windows)
f:/teamaccelerate/.venv/Scripts/python.exe backend/run.py
```

Run the demo pipeline simulator (separate terminal):

```bash
f:/teamaccelerate/.venv/Scripts/python.exe backend/scripts/demo_runner.py
```

Notes:
- The demo runner simulates CV/LSTM outputs and executes the LangGraph agent pipeline locally.
- For a full CV pipeline, provide MP4 files under `backend/data/mock_feeds` or an RTSP URL and start
   the `VideoProcessor` via a small runner.

Run the full CV pipeline (YOLOv8-Pose + ByteTrack + feature extraction):

```bash
# Ensure you have model weights `backend/yolov8n-pose.pt` available and mock videos in data/mock_feeds
f:/teamaccelerate/.venv/Scripts/Activate.ps1
f:/teamaccelerate/.venv/Scripts/python.exe backend/scripts/run_video_processors.py --device cuda:0

Or force CPU-only:
```
f:/teamaccelerate/.venv/Scripts/python.exe backend/scripts/run_video_processors.py --device cpu
```

Notes:
- The runner uses the lightest pose model `yolov8n-pose.pt` by default (configured in `settings.POSE_MODEL_PATH`).
- Use `--device` to override the configured device at runtime.
```
