#!/usr/bin/env python
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse
import uvicorn

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RailMind AI Backend")
    parser.add_argument(
        "--mode",
        choices=["server", "train", "train-cli"],
        default="server",
        help="Mode to run: server (default), train (trigger training via API), or train-cli (CLI training)",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload on file changes")
    
    # Training-specific args
    parser.add_argument("--model-type", default="all", help="Model type to train")
    parser.add_argument("--epochs", type=int, default=30, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size for training")
    
    args = parser.parse_args()
    
    if args.mode == "server":
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
        )
    
    elif args.mode == "train":
        # Trigger training via API (requires running server)
        print("ERROR: --mode train requires a running server. Use:")
        print("  curl -X POST http://localhost:8000/api/training/trigger -H 'Content-Type: application/json' \\")
        print(f"    -d '{{\"model_type\": \"{args.model_type}\", \"epochs\": {args.epochs}, \"batch_size\": {args.batch_size}}}'")
        sys.exit(1)
    
    elif args.mode == "train-cli":
        # Use the CLI directly
        from app.lstm.cli import main as cli_main
        sys.argv = [
            "python -m app.lstm.cli",
            "train",
            "--type", args.model_type,
            "--epochs", str(args.epochs),
            "--batch-size", str(args.batch_size),
        ]
        cli_main()

