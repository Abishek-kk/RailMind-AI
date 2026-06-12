# LSTM Training Pipeline

## Overview

The LSTM training pipeline has been fully integrated into the RailMind backend with multiple entry points for retraining:

1. **API Endpoints** - Trigger training remotely via HTTP
2. **CLI Tool** - Run training from command line
3. **Scheduled Jobs** - Automatic weekly retraining via APScheduler
4. **Status Tracking** - Monitor training runs in database

## Architecture

### New Components

#### Models
- **TrainingRun** (`app/models/training_run.py`) - Tracks all training execution history and metrics

#### Services
- **TrainingService** (`app/services/training_service.py`) - Business logic for training orchestration
  - Manages data generation, model training, and result persistence
  - Supports async execution to avoid blocking the event loop
  - Tracks metrics and errors

#### Background Jobs
- **Scheduler** (`app/core/scheduler.py`) - APScheduler-based background job runner
  - Weekly retraining every Sunday at 2 AM UTC
  - Extensible for additional scheduled tasks

#### API Routes
- **Training Routes** (`app/api/routes/training.py`) - REST endpoints for training management
  - `/training/trigger` - Start a new training run
  - `/training/runs/{run_id}` - Get status of specific run
  - `/training/runs` - Get training history
  - `/training/latest` - Get latest successful run
  - `/training/status` - Get system status

#### CLI
- **Training CLI** (`app/lstm/cli.py`) - Command-line interface for training
  - `train` command - Execute training directly
  - `status` command - Check run status and history

## Usage

### 1. API-Based Training (Recommended for Production)

**Start the server:**
```bash
cd backend
python run.py
```

**Trigger training via curl:**
```bash
# Train all models (default)
curl -X POST http://localhost:8000/api/training/trigger \
  -H "Content-Type: application/json" \
  -d '{"model_type": "all", "epochs": 30, "batch_size": 32}'

# Response: {"run_id": 1, "status": "pending", "message": "..."}
```

**Check status:**
```bash
# Get specific run status
curl http://localhost:8000/api/training/runs/1

# Get recent runs
curl http://localhost:8000/api/training/runs?limit=10

# Get latest successful run
curl http://localhost:8000/api/training/latest

# Get system status
curl http://localhost:8000/api/training/status
```

**Using Python requests:**
```python
import requests

# Trigger training
response = requests.post(
    "http://localhost:8000/api/training/trigger",
    json={"model_type": "all", "epochs": 30, "batch_size": 32}
)
run_id = response.json()["run_id"]

# Poll for status
import time
while True:
    status = requests.get(f"http://localhost:8000/api/training/runs/{run_id}").json()
    print(f"Status: {status['status']}")
    if status['status'] in ['completed', 'failed']:
        break
    time.sleep(5)
```

### 2. CLI Training (Development/Manual)

**Train all models:**
```bash
cd backend
python -m app.lstm.cli train
```

**Train specific model:**
```bash
python -m app.lstm.cli train --type suicide_classifier
python -m app.lstm.cli train --type pickpocket_classifier
python -m app.lstm.cli train --type anomaly_classifier
```

**Custom training parameters:**
```bash
python -m app.lstm.cli train --epochs 50 --batch-size 16 --type all
```

**Check training status:**
```bash
# Show last 10 runs
python -m app.lstm.cli status

# Show specific run
python -m app.lstm.cli status --run-id 1

# Show latest successful run
python -m app.lstm.cli status --latest

# Show last N runs
python -m app.lstm.cli status --history 20
```

### 3. Alternative: Using run.py

**CLI mode:**
```bash
cd backend
python run.py --mode train-cli --model-type all --epochs 30 --batch-size 32
```

**Note:** The `--mode train` option with `run.py` shows instructions for using the API instead.

### 4. Automatic Weekly Retraining

The scheduler automatically runs every **Sunday at 2 AM UTC**:
- Trains all three classifiers
- Stores results in database
- Can be monitored via API

**To manually trigger what would happen on schedule:**
```bash
python -m app.lstm.cli train --type all --epochs 30 --batch-size 32
```

## Workflow Examples

### Example 1: Development - Quick Training

```bash
# 1. Start server
python run.py

# 2. In another terminal, start quick training
python -m app.lstm.cli train --epochs 10 --batch-size 64

# 3. Check results
python -m app.lstm.cli status --latest
```

### Example 2: Production - API-Based with Monitoring

```bash
# 1. Trigger training
RESPONSE=$(curl -X POST http://localhost:8000/api/training/trigger \
  -H "Content-Type: application/json" \
  -d '{"model_type": "all", "epochs": 30, "batch_size": 32}')

RUN_ID=$(echo $RESPONSE | jq -r '.run_id')
echo "Started training run: $RUN_ID"

# 2. Monitor progress
while true; do
  STATUS=$(curl -s http://localhost:8000/api/training/runs/$RUN_ID | jq -r '.status')
  echo "Status: $STATUS"
  [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ] && break
  sleep 10
done

# 3. Check final results
curl http://localhost:8000/api/training/runs/$RUN_ID | jq '.'
```

### Example 3: Scheduled Retraining

The application automatically runs training every Sunday at 2 AM UTC. You can:

1. **Monitor scheduled runs:**
   ```bash
   # Get runs triggered by scheduler
   python -m app.lstm.cli status --history 5
   
   # The "Triggered" column will show "scheduled"
   ```

2. **Verify latest production model:**
   ```bash
   curl http://localhost:8000/api/training/latest | jq '.is_production_ready'
   ```

3. **Check system health:**
   ```bash
   curl http://localhost:8000/api/training/status | jq '.'
   ```

## Training Run Metadata

Each training run stores:

```json
{
  "id": 1,
  "triggered_by": "manual|scheduled|api|cli",
  "status": "pending|running|completed|failed",
  "model_type": "all|suicide_classifier|pickpocket_classifier|anomaly_classifier",
  "epochs": 30,
  "batch_size": 32,
  "final_train_loss": 0.0123,
  "final_val_loss": 0.0456,
  "final_train_accuracy": 0.95,
  "final_val_accuracy": 0.92,
  "started_at": "2024-01-15T02:00:00",
  "completed_at": "2024-01-15T02:45:00",
  "created_at": "2024-01-15T02:00:00",
  "error_message": null,
  "model_saved_path": "/path/to/models",
  "is_production_ready": true
}
```

## Model Files

Trained models are saved in the configured `MODEL_DIR` (default: `backend/lstm/saved_models/`):
- `suicide_classifier.pt` - Binary classifier for suicide risk
- `pickpocket_classifier.pt` - Binary classifier for pickpocketing
- `anomaly_classifier.pt` - Binary classifier for security threats
- `*_scaler.pkl` - StandardScaler objects for feature normalization

## Production Readiness

A training run is marked as `is_production_ready=true` when:
- Training completes successfully
- All models achieve ≥75% validation accuracy
- No errors during execution

## Monitoring & Debugging

### View Training Logs

**Server logs (includes training):**
```bash
# If server is running, training logs appear in stdout
```

**Check database:**
```bash
# Using Python
from app.core.database import SessionLocal
from app.models.training_run import TrainingRun

db = SessionLocal()
runs = db.query(TrainingRun).order_by(TrainingRun.created_at.desc()).limit(5).all()
for run in runs:
    print(f"Run {run.id}: {run.status} - {run.model_type} - {run.triggered_by}")
```

### Common Issues

**Training hangs/never completes:**
- Check server logs for errors
- Verify GPU/CUDA availability if using GPU
- Increase timeout if training very large models

**API endpoint not found:**
- Ensure you're using the correct API URL: `http://localhost:8000/api/training/...`
- Check that training routes are mounted in `app/api/routes/__init__.py`

**Scheduler not triggering:**
- Server must be running for scheduled jobs to execute
- Check logs for "Scheduler started" message on startup
- Verify system time is accurate for cron triggers

## Next Steps

1. **Add frontend UI** - Create dashboard to trigger and monitor training
2. **Model versioning** - Track model versions and rollback capability
3. **Notifications** - Alert when training completes or fails
4. **Metrics export** - Export metrics to monitoring systems (Prometheus, etc.)
5. **Hyperparameter tuning** - Make epochs/batch-size configurable per model
