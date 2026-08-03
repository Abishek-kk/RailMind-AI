"""Training API routes for managing temporal transformer model retraining."""
import asyncio
import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from datetime import datetime

from app.core.database import SessionLocal
from app.models.training_run import TrainingRun
from app.services.training_service import TrainingService

logger = logging.getLogger("railmind.training.api")

router = APIRouter()


# Schema models
class TrainingRunSchema(BaseModel):
    id: int
    triggered_by: str
    status: str
    model_type: str
    epochs: int
    batch_size: int
    synthetic_sample_count: int
    real_sample_count: int
    final_train_loss: Optional[float]
    final_val_loss: Optional[float]
    final_train_accuracy: Optional[float]
    final_val_accuracy: Optional[float]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    error_message: Optional[str]
    model_saved_path: Optional[str]
    is_production_ready: bool

    class Config:
        from_attributes = True


class TrainRequest(BaseModel):
    model_type: str = "all"  # "all" or "behavior_classifier"
    epochs: int = 30
    batch_size: int = 32


class TrainingStatusResponse(BaseModel):
    run_id: int
    status: str
    message: str


@router.post("/training/trigger", response_model=TrainingStatusResponse, tags=["Training"])
async def trigger_training(request: TrainRequest = Body(...)) -> TrainingStatusResponse:
    """Trigger a new transformer model training run.
    
    This endpoint:
    - Creates a training run record in the database
    - Starts the training in the background
    - Returns immediately with the run ID for status tracking
    
    Args:
        model_type: Which model to train ("all" or "behavior_classifier")
        epochs: Number of training epochs (default: 30)
        batch_size: Batch size for training (default: 32)
    
    Returns:
        TrainingStatusResponse with run ID and status
    """
    try:
        db = SessionLocal()
        training_service = TrainingService(db)
        
        # Create training run record
        run = training_service.create_training_run_record(
            triggered_by="api",
            model_type=request.model_type,
            epochs=request.epochs,
            batch_size=request.batch_size,
        )
        
        logger.info(f"Training run {run.id} created via API")
        
        # Start training in background (without awaiting)
        asyncio.create_task(
            training_service.execute_training_async(
                run.id,
                model_type=request.model_type,
                epochs=request.epochs,
                batch_size=request.batch_size,
            )
        )
        
        return TrainingStatusResponse(
            run_id=run.id,
            status="pending",
            message=f"Training run {run.id} started in the background. Use /training/runs/{run.id} to check status.",
        )
    
    except Exception as e:
        logger.error(f"Failed to trigger training: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger training: {str(e)}"
        )


@router.get("/training/runs/{run_id}", response_model=TrainingRunSchema, tags=["Training"])
async def get_training_status(run_id: int) -> TrainingRunSchema:
    """Get the status and details of a specific training run.
    
    Args:
        run_id: The training run ID
    
    Returns:
        TrainingRunSchema with current status and metrics
    """
    try:
        db = SessionLocal()
        training_service = TrainingService(db)
        
        run = training_service.get_training_run(run_id)
        if not run:
            raise HTTPException(
                status_code=404,
                detail=f"Training run {run_id} not found"
            )
        
        return TrainingRunSchema.from_orm(run)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get training status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get training status: {str(e)}"
        )


@router.get("/training/runs", response_model=List[TrainingRunSchema], tags=["Training"])
async def get_training_history(limit: int = 10) -> List[TrainingRunSchema]:
    """Get recent training run history.
    
    Args:
        limit: Maximum number of runs to return (default: 10)
    
    Returns:
        List of recent TrainingRun records
    """
    try:
        db = SessionLocal()
        training_service = TrainingService(db)
        
        runs = training_service.get_training_history(limit=limit)
        return [TrainingRunSchema.from_orm(run) for run in runs]
    
    except Exception as e:
        logger.error(f"Failed to get training history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get training history: {str(e)}"
        )


@router.get("/training/latest", response_model=Optional[TrainingRunSchema], tags=["Training"])
async def get_latest_training() -> Optional[TrainingRunSchema]:
    """Get the latest successful (production-ready) training run.
    
    Returns:
        The most recent successful TrainingRun or None if no successful runs exist
    """
    try:
        db = SessionLocal()
        training_service = TrainingService(db)
        
        run = training_service.get_latest_successful_run()
        if not run:
            return None
        
        return TrainingRunSchema.from_orm(run)
    
    except Exception as e:
        logger.error(f"Failed to get latest training: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get latest training: {str(e)}"
        )


@router.get("/training/status", response_model=Dict, tags=["Training"])
async def get_training_system_status() -> Dict:
    """Get overall training system status.
    
    Returns:
        Dictionary with training system health and statistics
    """
    try:
        db = SessionLocal()
        training_service = TrainingService(db)
        
        # Get counts by status
        pending = db.query(TrainingRun).filter(TrainingRun.status == "pending").count()
        running = db.query(TrainingRun).filter(TrainingRun.status == "running").count()
        completed = db.query(TrainingRun).filter(TrainingRun.status == "completed").count()
        failed = db.query(TrainingRun).filter(TrainingRun.status == "failed").count()
        
        latest = training_service.get_latest_successful_run()
        
        return {
            "system_status": "operational",
            "training_runs": {
                "pending": pending,
                "running": running,
                "completed": completed,
                "failed": failed,
                "total": pending + running + completed + failed,
            },
            "latest_successful_run": {
                "id": latest.id if latest else None,
                "completed_at": latest.completed_at if latest else None,
                "is_production_ready": latest.is_production_ready if latest else False,
            } if latest else None,
        }
    
    except Exception as e:
        logger.error(f"Failed to get training system status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get training system status: {str(e)}"
        )
