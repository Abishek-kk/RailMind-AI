"""Training run database model to track LSTM model retraining history"""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean
from sqlalchemy.sql import func

from app.core.database import Base


class TrainingRun(Base):
    """Tracks LSTM model training history and performance metrics."""
    __tablename__ = "training_runs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Metadata
    triggered_by = Column(String, nullable=False)  # "manual", "scheduled", "cli"
    status = Column(String, nullable=False, default="pending")  # pending, running, completed, failed
    
    # Model targets
    model_type = Column(String, nullable=False)  # "behavior_classifier" or "all"
    
    # Training parameters
    epochs = Column(Integer, nullable=False, default=30)
    batch_size = Column(Integer, nullable=False, default=32)
    
    # Performance metrics
    final_train_loss = Column(Float, nullable=True)
    final_val_loss = Column(Float, nullable=True)
    final_train_accuracy = Column(Float, nullable=True)
    final_val_accuracy = Column(Float, nullable=True)
    
    # Training history (JSON array of epoch metrics)
    training_history = Column(JSON, nullable=True)  # {"train_loss": [...], "val_loss": [...], ...}
    
    # Execution details
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Error handling
    error_message = Column(String, nullable=True)
    error_traceback = Column(String, nullable=True)
    
    # Model artifacts
    model_saved_path = Column(String, nullable=True)
    is_production_ready = Column(Boolean, nullable=False, default=False)
    deployed_at = Column(DateTime(timezone=True), nullable=True)
