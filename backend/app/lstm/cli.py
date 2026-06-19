"""CLI entry point for LSTM model training and management."""
import argparse
import logging
import sys

from app.core.database import SessionLocal
from app.services.training_service import TrainingService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("railmind.cli")


def train_command(args):
    """Train LSTM models.
    
    Examples:
        python -m app.lstm.cli train                     # Train all models
        python -m app.lstm.cli train --type behavior_classifier
        python -m app.lstm.cli train --epochs 50 --batch-size 16
    """
    db = SessionLocal()
    training_service = TrainingService(db)
    
    # Create training run
    run = training_service.create_training_run_record(
        triggered_by="cli",
        model_type=args.type,
        epochs=args.epochs,
        batch_size=args.batch_size,
    )
    
    logger.info(f"Training run {run.id} created")
    logger.info(f"Model type: {args.type}")
    logger.info(f"Epochs: {args.epochs}, Batch size: {args.batch_size}")
    
    # Execute training
    try:
        training_service.execute_training(
            run.id,
            model_type=args.type,
            epochs=args.epochs,
            batch_size=args.batch_size,
        )
        
        # Get final run record
        final_run = training_service.get_training_run(run.id)
        
        logger.info("\n" + "="*70)
        logger.info("Training Summary")
        logger.info("="*70)
        logger.info(f"Status: {final_run.status}")
        logger.info(f"Model Type: {final_run.model_type}")
        logger.info(f"Final Train Loss: {final_run.final_train_loss:.4f}" if final_run.final_train_loss else "N/A")
        logger.info(f"Final Val Loss: {final_run.final_val_loss:.4f}" if final_run.final_val_loss else "N/A")
        logger.info(f"Final Train Accuracy: {final_run.final_train_accuracy:.4f}" if final_run.final_train_accuracy else "N/A")
        logger.info(f"Final Val Accuracy: {final_run.final_val_accuracy:.4f}" if final_run.final_val_accuracy else "N/A")
        logger.info(f"Production Ready: {final_run.is_production_ready}")
        logger.info(f"Models saved to: {final_run.model_saved_path}")
        logger.info("="*70)
        
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Training failed: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()


def status_command(args):
    """Check training run status.
    
    Examples:
        python -m app.lstm.cli status --run-id 5      # Check specific run
        python -m app.lstm.cli status --latest         # Check latest successful run
        python -m app.lstm.cli status --history 10     # List last 10 runs
    """
    db = SessionLocal()
    training_service = TrainingService(db)
    
    try:
        if args.run_id:
            run = training_service.get_training_run(args.run_id)
            if not run:
                logger.error(f"Training run {args.run_id} not found")
                sys.exit(1)
            
            logger.info(f"\nTraining Run #{run.id}")
            logger.info(f"  Status: {run.status}")
            logger.info(f"  Triggered By: {run.triggered_by}")
            logger.info(f"  Model Type: {run.model_type}")
            logger.info(f"  Created: {run.created_at}")
            logger.info(f"  Started: {run.started_at}")
            logger.info(f"  Completed: {run.completed_at}")
            if run.status == "completed":
                logger.info(f"  Final Train Loss: {run.final_train_loss:.4f}")
                logger.info(f"  Final Val Loss: {run.final_val_loss:.4f}")
                logger.info(f"  Final Train Accuracy: {run.final_train_accuracy:.4f}")
                logger.info(f"  Final Val Accuracy: {run.final_val_accuracy:.4f}")
                logger.info(f"  Production Ready: {run.is_production_ready}")
            elif run.status == "failed":
                logger.info(f"  Error: {run.error_message}")
        
        elif args.latest:
            run = training_service.get_latest_successful_run()
            if not run:
                logger.info("No successful training runs found")
                sys.exit(0)
            
            logger.info(f"\nLatest Successful Training Run #{run.id}")
            logger.info(f"  Status: {run.status}")
            logger.info(f"  Model Type: {run.model_type}")
            logger.info(f"  Completed: {run.completed_at}")
            logger.info(f"  Production Ready: {run.is_production_ready}")
            logger.info(f"  Final Val Accuracy: {run.final_val_accuracy:.4f}")
        
        else:  # history (default)
            runs = training_service.get_training_history(limit=args.history)
            
            logger.info(f"\n{'Last'} {len(runs)} Training Runs:")
            logger.info("-" * 100)
            logger.info(f"{'ID':<5} {'Status':<12} {'Type':<25} {'Triggered':<12} {'Created':<19} {'Completed':<19}")
            logger.info("-" * 100)
            
            for run in runs:
                completed_str = run.completed_at.strftime("%Y-%m-%d %H:%M:%S") if run.completed_at else "N/A"
                created_str = run.created_at.strftime("%Y-%m-%d %H:%M:%S")
                logger.info(
                    f"{run.id:<5} {run.status:<12} {run.model_type:<25} {run.triggered_by:<12} {created_str:<19} {completed_str:<19}"
                )
    
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="LSTM Model Training CLI",
        prog="python -m app.lstm.cli",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Train command
    train_parser = subparsers.add_parser("train", help="Train LSTM models")
    train_parser.add_argument(
        "--type",
        default="all",
        choices=["all", "behavior_classifier"],
        help="Model type to train (default: all)",
    )
    train_parser.add_argument(
        "--epochs",
        type=int,
        default=30,
        help="Number of training epochs (default: 30)",
    )
    train_parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for training (default: 32)",
    )
    train_parser.set_defaults(func=train_command)
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Check training run status")
    status_group = status_parser.add_mutually_exclusive_group()
    status_group.add_argument(
        "--run-id",
        type=int,
        help="Check status of specific training run ID",
    )
    status_group.add_argument(
        "--latest",
        action="store_true",
        help="Show latest successful training run",
    )
    status_group.add_argument(
        "--history",
        type=int,
        default=10,
        help="Show last N training runs (default: 10)",
    )
    status_parser.set_defaults(func=status_command)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    args.func(args)


if __name__ == "__main__":
    main()
