"""Background job scheduler for LSTM model retraining."""
import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.database import SessionLocal
from app.services.station_fp_rate_service import flag_stations_above_threshold
from app.services.training_service import TrainingService

logger = logging.getLogger("railmind.scheduler")

# Global scheduler instance
_scheduler: BackgroundScheduler = None


def get_scheduler() -> BackgroundScheduler:
    """Get the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
    return _scheduler


def start_scheduler():
    """Start the background scheduler with configured jobs."""
    scheduler = get_scheduler()
    
    if scheduler.running:
        logger.warning("Scheduler already running, skipping start")
        return
    
    # Add weekly retraining job (every Sunday at 2 AM UTC)
    scheduler.add_job(
        _scheduled_training_job,
        CronTrigger(day_of_week=6, hour=2, minute=0),  # Sunday 2 AM
        id="weekly_lstm_retrain",
        name="Weekly LSTM Model Retraining",
        replace_existing=True,
    )

    # Add daily FP-rate station alert check (every day at 3 AM UTC)
    scheduler.add_job(
        _scheduled_fp_rate_job,
        CronTrigger(hour=3, minute=0),
        id="daily_fp_rate_check",
        name="Daily Station False-Positive Rate Check",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started with weekly retraining job")


def stop_scheduler():
    """Stop the background scheduler gracefully."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=True)
        logger.info("Scheduler stopped")


def _scheduled_training_job():
    """Execute scheduled training job."""
    logger.info("=" * 70)
    logger.info("Executing scheduled LSTM model retraining")
    logger.info("=" * 70)
    
    try:
        db = SessionLocal()
        training_service = TrainingService(db)
        
        # Create a scheduled training run
        run = training_service.create_training_run_record(
            triggered_by="scheduled",
            model_type="all",
            epochs=30,
            batch_size=32,
        )
        
        logger.info(f"Scheduled training run {run.id} created")
        
        # Execute training synchronously (blocking)
        # This is fine for background jobs since they don't interfere with the event loop
        training_service.execute_training(
            run.id,
            model_type="all",
            epochs=30,
            batch_size=32,
        )
        
        logger.info(f"Scheduled training run {run.id} completed")
        
    except Exception as e:
        logger.error(f"Scheduled training job failed: {str(e)}", exc_info=True)
    finally:
        db.close()


def _scheduled_fp_rate_job():
    """Execute daily false-positive rate station check."""
    logger.info("=" * 70)
    logger.info("Executing scheduled station false-positive rate check")
    logger.info("=" * 70)

    try:
        db = SessionLocal()
        flagged = flag_stations_above_threshold(db)
        if flagged:
            logger.info("Flagged %d station(s): %s", len(flagged), ", ".join(flagged))
        else:
            logger.info("No stations exceeded the false-positive rate threshold")
    except Exception as e:
        logger.error(f"Scheduled FP rate check failed: {str(e)}", exc_info=True)
    finally:
        db.close()
