"""Training service for managing LSTM model retraining workflows."""
import asyncio
import logging
import os
import traceback
from datetime import datetime
from typing import Any, Dict, Optional

import numpy as np
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.lstm.train import (
    BEHAVIOR_LABELS,
    SyntheticDataGenerator,
    create_multiclass_dataset,
    train_behavior_classifier,
)
from app.models.alert import Alert
from app.models.feedback import Feedback
from app.models.incident import Incident
from app.models.training_run import TrainingRun

logger = logging.getLogger("railmind.training")

MIN_REAL_SAMPLES_FOR_BLEND = 50
REAL_DATA_BLEND_RATIO = 0.20


class TrainingService:
    """Manages LSTM model retraining with tracking and notifications."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def get_db_session(self) -> Session:
        """Get or create database session."""
        if self.db is None:
            return SessionLocal()
        return self.db

    def get_labelled_feedback_dataset(self) -> Dict[str, Any]:
        """Return operator-labelled feedback examples for future retraining."""
        db = self.get_db_session()
        try:
            rows = (
                db.query(Feedback, Alert, Incident)
                .join(Alert, Feedback.alert_id == Alert.id)
                .outerjoin(Incident, Incident.alert_id == Alert.id)
                .order_by(Feedback.submitted_at.desc(), Incident.timestamp.desc())
                .all()
            )

            examples = []
            for feedback, alert, incident in rows:
                examples.append(
                    {
                        "feedback_id": feedback.id,
                        "label": feedback.corrected_label,
                        "is_false_positive": feedback.is_false_positive,
                        "notes": feedback.notes,
                        "submitted_at": feedback.submitted_at,
                        "staff_id": feedback.staff_id,
                        "training_run_id": feedback.training_run_id,
                        "alert": {
                            "id": alert.id,
                            "person_id": alert.person_id,
                            "camera_id": alert.camera_id,
                            "platform": alert.platform,
                            "incident_type": alert.incident_type,
                            "risk_score": alert.risk_score,
                            "risk_level": alert.risk_level,
                            "lstm_confidence": alert.lstm_confidence,
                            "bounding_box": alert.bounding_box,
                            "timestamp": alert.timestamp,
                        },
                        "incident": {
                            "id": incident.id,
                            "camera_id": incident.camera_id,
                            "platform": incident.platform,
                            "incident_type": incident.incident_type,
                            "risk_score": incident.risk_score,
                            "risk_level": incident.risk_level,
                            "status": incident.status,
                            "false_positive": incident.false_positive,
                            "timestamp": incident.timestamp,
                        }
                        if incident is not None
                        else None,
                    }
                )

            return {"source": "feedback", "count": len(examples), "examples": examples}
        finally:
            if self.db is None:
                db.close()

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
        synthetic_sample_count: Optional[int] = None,
        real_sample_count: Optional[int] = None,
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
            if synthetic_sample_count is not None:
                run.synthetic_sample_count = synthetic_sample_count
            if real_sample_count is not None:
                run.real_sample_count = real_sample_count

            db.commit()
            db.refresh(run)
            return run
        finally:
            if self.db is None:
                db.close()

    def _feedback_label_for_training(self, example: Dict[str, Any]) -> Optional[str]:
        """Map operator feedback and incident context into the 4-class LSTM label space."""
        corrected_label = (example.get("label") or "").strip().lower().replace(" ", "_")
        label_aliases = {
            "normal": "normal",
            "safe": "normal",
            "false_positive": "normal",
            "suicide": "suicide",
            "suicide_risk": "suicide",
            "self_harm": "suicide",
            "pickpocket": "pickpocket",
            "pickpocketing": "pickpocket",
            "theft": "pickpocket",
            "security": "security_threat",
            "security_threat": "security_threat",
            "threat": "security_threat",
            "violence": "security_threat",
        }
        if corrected_label in label_aliases:
            return label_aliases[corrected_label]

        if example.get("is_false_positive"):
            return "normal"

        context = example.get("incident") or example.get("alert") or {}
        incident_type = (context.get("incident_type") or "").lower()
        if any(term in incident_type for term in ("suicide", "self harm", "track intrusion", "edge")):
            return "suicide"
        if any(term in incident_type for term in ("pickpocket", "theft", "steal")):
            return "pickpocket"
        if any(term in incident_type for term in ("security", "threat", "weapon", "violence", "fight")):
            return "security_threat"
        if any(term in incident_type for term in ("normal", "safe", "false positive")):
            return "normal"
        return None

    def _feedback_example_to_sequence(self, example: Dict[str, Any]) -> Optional[tuple[str, np.ndarray]]:
        """Convert a labelled feedback example into one LSTM-compatible sequence."""
        label = self._feedback_label_for_training(example)
        if label is None:
            return None

        context = example.get("incident") or example.get("alert") or {}
        risk_score = float(context.get("risk_score") or 0.0)
        risk = max(0.0, min(risk_score / 100.0, 1.0))
        incident_type = (context.get("incident_type") or "").lower()
        confidence = example.get("alert", {}).get("lstm_confidence")
        confidence = 0.5 if confidence is None else max(0.0, min(float(confidence), 1.0))

        feature_vector = np.array(
            [
                30.0 * risk if label == "suicide" else 6.0 * risk,
                30.0 * risk if "loiter" in incident_type else 12.0 * risk,
                8.0 * risk if label == "suicide" else 3.0 * risk,
                0.2 + (4.8 * risk if label == "security_threat" else 1.8 * (1.0 - risk)),
                12.0 * risk if label in {"suicide", "security_threat"} else 4.0 * risk,
                10.0 * (1.0 - risk),
                10.0 * risk if label == "pickpocket" else 3.0 * confidence,
            ],
            dtype=float,
        )
        sequence = np.tile(feature_vector, (settings.LSTM_SEQUENCE_LENGTH, 1))
        return label, sequence

    def _real_feedback_sequences_by_label(self, examples: list[Dict[str, Any]]) -> dict[str, np.ndarray]:
        sequences_by_label: dict[str, list[np.ndarray]] = {label: [] for label in BEHAVIOR_LABELS}
        for example in examples:
            converted = self._feedback_example_to_sequence(example)
            if converted is None:
                continue
            label, sequence = converted
            sequences_by_label[label].append(sequence)

        return {
            label: np.array(sequences, dtype=float).reshape(
                len(sequences),
                settings.LSTM_SEQUENCE_LENGTH,
                settings.LSTM_FEATURE_COUNT,
            )
            for label, sequences in sequences_by_label.items()
        }

    def _blend_real_feedback_with_synthetic(
        self,
        synthetic_data: dict[str, np.ndarray],
        feedback_dataset: Dict[str, Any],
    ) -> tuple[dict[str, np.ndarray], int, int, int]:
        """Blend enough labelled real samples into synthetic data to hit the configured ratio."""
        synthetic_sample_count = sum(len(synthetic_data[label]) for label in BEHAVIOR_LABELS)
        available_real_count = int(feedback_dataset.get("count") or 0)
        examples = feedback_dataset.get("examples") or []

        if available_real_count < MIN_REAL_SAMPLES_FOR_BLEND:
            logger.info(
                "Using synthetic-only training data: %s labelled real samples available, "
                "minimum is %s.",
                available_real_count,
                MIN_REAL_SAMPLES_FOR_BLEND,
            )
            return synthetic_data, synthetic_sample_count, 0, available_real_count

        real_by_label = self._real_feedback_sequences_by_label(examples)
        usable_real_count = sum(len(real_by_label[label]) for label in BEHAVIOR_LABELS)
        if usable_real_count < MIN_REAL_SAMPLES_FOR_BLEND:
            logger.info(
                "Using synthetic-only training data: %s labelled real samples were usable, "
                "minimum is %s.",
                usable_real_count,
                MIN_REAL_SAMPLES_FOR_BLEND,
            )
            return synthetic_data, synthetic_sample_count, 0, available_real_count

        target_real_count = max(
            usable_real_count,
            int(np.ceil(synthetic_sample_count * REAL_DATA_BLEND_RATIO / (1.0 - REAL_DATA_BLEND_RATIO))),
        )
        target_by_label = {
            label: int(round(target_real_count * (len(real_by_label[label]) / usable_real_count)))
            for label in BEHAVIOR_LABELS
        }
        count_delta = target_real_count - sum(target_by_label.values())
        if count_delta:
            largest_label = max(BEHAVIOR_LABELS, key=lambda label: len(real_by_label[label]))
            target_by_label[largest_label] += count_delta

        blended_data = {label: synthetic_data[label] for label in BEHAVIOR_LABELS}
        real_samples_used = 0
        for label in BEHAVIOR_LABELS:
            label_sequences = real_by_label[label]
            label_target = target_by_label[label]
            if len(label_sequences) == 0 or label_target <= 0:
                continue

            repeats = int(np.ceil(label_target / len(label_sequences)))
            oversampled = np.tile(label_sequences, (repeats, 1, 1))[:label_target]
            blended_data[label] = np.concatenate([synthetic_data[label], oversampled], axis=0)
            real_samples_used += len(oversampled)

        logger.info(
            "Blending training data: %s synthetic samples + %s real feedback samples "
            "from %s usable labelled examples.",
            synthetic_sample_count,
            real_samples_used,
            usable_real_count,
        )
        return blended_data, synthetic_sample_count, real_samples_used, available_real_count

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
            model_type: "all" or "behavior_classifier"
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
            feedback_dataset = self.get_labelled_feedback_dataset()
            data, synthetic_sample_count, real_sample_count, available_real_count = (
                self._blend_real_feedback_with_synthetic(data, feedback_dataset)
            )
            self.update_training_run(
                run_id,
                synthetic_sample_count=synthetic_sample_count,
                real_sample_count=real_sample_count,
            )
            logger.info(
                "Training run %s data summary: synthetic_used=%s, real_used=%s, real_available=%s",
                run_id,
                synthetic_sample_count,
                real_sample_count,
                available_real_count,
            )

            # Create model directory
            os.makedirs(settings.MODEL_DIR, exist_ok=True)

            if model_type not in {"all", "behavior_classifier"}:
                raise ValueError("Only the 4-class behavior_classifier model is supported")

            logger.info(f"\n{'='*70}")
            logger.info("Training 4-class Behavior classifier")
            logger.info(f"{'='*70}")

            X_train, y_train, X_val, y_val, scaler = create_multiclass_dataset(
                data, val_split=0.2, seed=42
            )

            history = train_behavior_classifier(
                X_train,
                y_train,
                X_val,
                y_val,
                scaler,
                output_filename="behavior_classifier.pt",
                epochs=epochs,
                batch_size=batch_size,
            )

            final_train_loss = history["train_loss"][-1] if history["train_loss"] else None
            final_val_loss = history["val_loss"][-1] if history["val_loss"] else None
            final_train_accuracy = history["train_accuracy"][-1] if history["train_accuracy"] else None
            final_val_accuracy = history["val_accuracy"][-1] if history["val_accuracy"] else None

            # Mark as production ready if all accuracies are above threshold
            is_production_ready = bool(final_val_accuracy is not None and final_val_accuracy >= 0.75)

            # Update run with success
            self.update_training_run(
                run_id,
                status="completed",
                completed_at=datetime.utcnow(),
                final_train_loss=final_train_loss,
                final_val_loss=final_val_loss,
                final_train_accuracy=final_train_accuracy,
                final_val_accuracy=final_val_accuracy,
                training_history={"behavior_classifier.pt": history},
                model_saved_path=settings.MODEL_DIR,
                is_production_ready=is_production_ready,
                synthetic_sample_count=synthetic_sample_count,
                real_sample_count=real_sample_count,
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
