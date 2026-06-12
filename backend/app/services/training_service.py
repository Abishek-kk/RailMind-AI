"""Training service for managing LSTM model retraining workflows."""
import asyncio
import logging
import os
import traceback
from datetime import datetime
from typing import Dict, Optional

import numpy as np
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.lstm.train import (
    SyntheticDataGenerator,
    create_binary_dataset,
    train_classifier,
)
from app.models.training_run import TrainingRun

logger = logging.getLogger("railmind.training")


class TrainingService:
    """Manages LSTM model retraining with tracking and notifications."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def get_db_session(self) -> Session:
        """Get or create database session."""
        if self.db is None:
            return SessionLocal()
        return self.db

    def create_training_run_record(
        self,
        triggered_by: str,
        model_type: str = "all",
        epochs: int = 30,
        batch_size: int = 32,
    ) -> TrainingRun:
        """Create a new training run record in the database."""
        db = self.get_db_session()
        try:
            run = TrainingRun(
                triggered_by=triggered_by,
                status="pending",
                model_type=model_type,
                epochs=epochs,
                batch_size=batch_size,
            )
            db.add(run)
            db.commit()
            db.refresh(run)
            logger.info(f"Created training run record: {run.id}")
            return run
        finally:
            if self.db is None:
                db.close()

    def update_training_run(
        self,
        run_id: int,
        status: Optional[str] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        final_train_loss: Optional[float] = None,
        final_val_loss: Optional[float] = None,
        final_train_accuracy: Optional[float] = None,
        final_val_accuracy: Optional[float] = None,
        training_history: Optional[Dict] = None,
        error_message: Optional[str] = None,
        error_traceback: Optional[str] = None,
        model_saved_path: Optional[str] = None,
        is_production_ready: Optional[bool] = None,
    ) -> TrainingRun:
        """Update an existing training run record."""
        db = self.get_db_session()
        try:
            run = db.query(TrainingRun).filter(TrainingRun.id == run_id).first()
            if not run:
                raise ValueError(f"Training run {run_id} not found")

            if status is not None:
                run.status = status
            if started_at is not None:
                run.started_at = started_at
            if completed_at is not None:
                run.completed_at = completed_at
            if final_train_loss is not None:
                run.final_train_loss = final_train_loss
            if final_val_loss is not None:
                run.final_val_loss = final_val_loss
            if final_train_accuracy is not None:
                run.final_train_accuracy = final_train_accuracy
            if final_val_accuracy is not None:
                run.final_val_accuracy = final_val_accuracy
            if training_history is not None:
                run.training_history = training_history
            if error_message is not None:
                run.error_message = error_message
            if error_traceback is not None:
                run.error_traceback = error_traceback
            if model_saved_path is not None:
                run.model_saved_path = model_saved_path
            if is_production_ready is not None:
                run.is_production_ready = is_production_ready

            db.commit()
            db.refresh(run)
            return run
        finally:
            if self.db is None:
                db.close()

    def execute_training(
        self,
        run_id: int,
        model_type: str = "all",
        epochs: int = 30,
        batch_size: int = 32,
    ) -> None:
        """Execute the training pipeline for specified models.
        
        This is the main entry point for training. It coordinates synthetic data generation
        and model training for the specified model types.
        
        Args:
            run_id: Training run ID to track this execution
            model_type: "all", "suicide_classifier", "pickpocket_classifier", or "anomaly_classifier"
            epochs: Number of training epochs
            batch_size: Batch size for training
        """
        start_time = datetime.utcnow()
        
        try:
            # Update status to running
            self.update_training_run(run_id, status="running", started_at=start_time)
            logger.info(f"Starting training run {run_id} for {model_type}")

            # Generate synthetic data
            logger.info("Generating synthetic behavioral sequences...")
            generator = SyntheticDataGenerator(
                sequence_length=settings.LSTM_SEQUENCE_LENGTH,
                num_features=settings.LSTM_FEATURE_COUNT,
            )
            data = generator.generate_all_data()

            # Create model directory
            os.makedirs(settings.MODEL_DIR, exist_ok=True)

            # Define training tasks
            classifiers = [
                ("Suicide Risk", "suicide_classifier.pt", data["normal"], data["suicide"]),
                ("Pickpocket", "pickpocket_classifier.pt", data["normal"], data["pickpocket"]),
                ("Security Threat/Anomaly", "anomaly_classifier.pt", data["normal"], data["security_threat"]),
            ]

            # Filter based on model_type
            if model_type != "all":
                classifiers = [c for c in classifiers if c[1].replace("_classifier.pt", "") == model_type.replace("_classifier", "")]

            all_histories = {}
            final_accuracies = {}

            # Train each classifier
            for display_name, filename, normal_seq, threat_seq in classifiers:
                logger.info(f"\n{'='*70}")
                logger.info(f"Training {display_name} classifier")
                logger.info(f"{'='*70}")

                X_train, y_train, X_val, y_val, scaler = create_binary_dataset(
                    normal_seq, threat_seq, val_split=0.2, seed=42
                )

                history = train_classifier(
                    display_name,
                    X_train,
                    y_train,
                    X_val,
                    y_val,
                    filename,
                    scaler,
                    epochs=epochs,
                    batch_size=batch_size,
                )

                all_histories[filename] = history
                # Store final validation accuracy
                final_accuracies[filename] = history["val_accuracy"][-1] if history["val_accuracy"] else 0.0

            # Get final metrics from the last classifier
            if all_histories:
                last_history = list(all_histories.values())[-1]
                final_train_loss = last_history["train_loss"][-1] if last_history["train_loss"] else None
                final_val_loss = last_history["val_loss"][-1] if last_history["val_loss"] else None
                final_train_accuracy = last_history["train_accuracy"][-1] if last_history["train_accuracy"] else None
                final_val_accuracy = last_history["val_accuracy"][-1] if last_history["val_accuracy"] else None
            else:
                final_train_loss = final_val_loss = final_train_accuracy = final_val_accuracy = None

            # Mark as production ready if all accuracies are above threshold
            is_production_ready = all(acc >= 0.75 for acc in final_accuracies.values())

            # Update run with success
            self.update_training_run(
                run_id,
                status="completed",
                completed_at=datetime.utcnow(),
                final_train_loss=final_train_loss,
                final_val_loss=final_val_loss,
                final_train_accuracy=final_train_accuracy,
                final_val_accuracy=final_val_accuracy,
                training_history=all_histories,
                model_saved_path=settings.MODEL_DIR,
                is_production_ready=is_production_ready,
            )

            logger.info("\n" + "="*70)
            logger.info(f"✓ Training run {run_id} completed successfully!")
            logger.info("="*70)
            logger.info(f"Models saved in: {settings.MODEL_DIR}")
            logger.info(f"Production ready: {is_production_ready}")

        except Exception as e:
            error_msg = str(e)
            error_tb = traceback.format_exc()
            
            logger.error(f"Training run {run_id} failed: {error_msg}")
            logger.error(f"Traceback:\n{error_tb}")
            
            self.update_training_run(
                run_id,
                status="failed",
                completed_at=datetime.utcnow(),
                error_message=error_msg,
                error_traceback=error_tb,
            )

    async def execute_training_async(
        self,
        run_id: int,
        model_type: str = "all",
        epochs: int = 30,
        batch_size: int = 32,
    ) -> None:
        """Execute training in a background thread to avoid blocking the event loop."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self.execute_training,
            run_id,
            model_type,
            epochs,
            batch_size,
        )

    def get_training_run(self, run_id: int) -> Optional[TrainingRun]:
        """Get a training run by ID."""
        db = self.get_db_session()
        try:
            return db.query(TrainingRun).filter(TrainingRun.id == run_id).first()
        finally:
            if self.db is None:
                db.close()

    def get_training_history(self, limit: int = 10) -> list:
        """Get recent training runs."""
        db = self.get_db_session()
        try:
            return db.query(TrainingRun).order_by(TrainingRun.created_at.desc()).limit(limit).all()
        finally:
            if self.db is None:
                db.close()

    def get_latest_successful_run(self) -> Optional[TrainingRun]:
        """Get the most recent successful training run."""
        db = self.get_db_session()
        try:
            return (
                db.query(TrainingRun)
                .filter(TrainingRun.status == "completed", TrainingRun.is_production_ready == True)
                .order_by(TrainingRun.completed_at.desc())
                .first()
            )
        finally:
            if self.db is None:
                db.close()
