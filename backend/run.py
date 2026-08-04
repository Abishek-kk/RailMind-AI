from __future__ import annotations

import argparse
import os

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the RailMind backend server")
    parser.add_argument("--mode", choices=["server"], default="server")
    parser.add_argument("--host", default=os.getenv("HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8000")))
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()

    if args.mode != "server":
        raise SystemExit("Only --mode server is supported in this workspace snapshot")

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        workers=args.workers,
        reload=False,
    )


if __name__ == "__main__":
    main()
