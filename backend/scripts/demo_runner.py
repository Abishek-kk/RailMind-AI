"""Demo runner: simulates CV/LSTM outputs and executes the agent pipeline locally.

Run: f:/teamaccelerate/.venv/Scripts/python.exe backend/scripts/demo_runner.py
"""
import sys
import os
import asyncio
import random
import time
from typing import Dict, Any

# Ensure the backend package directory is importable when running this script directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.agent_graph import run_agent_pipeline


def make_sample_raw_state(person_id: int) -> Dict[str, Any]:
    # Simulate a range of behaviours including normal, pacing, edge approach, and following
    edge_proximity = random.choice([0, 5, 15, 35, 70])
    following_distance = random.choice([float('inf'), 0.3, 1.2, 0.6])
    pacing = random.choice([0, 1, 3, 5])
    movement_speed = random.uniform(0.0, 1.5)

    lstm_scores = {
        "normal": max(0.0, 1.0 - random.random()),
        "suicide": random.random() * (edge_proximity / 100.0),
        "pickpocket": random.random() * (1.0 if following_distance < 1.0 else 0.1),
        "anomaly": random.random() * 0.5,
    }

    return {
        "person_id": person_id,
        "camera_id": "CAM_DEMO_01",
        "platform": "DemoPlatform",
        "lstm_scores": lstm_scores,
        "lstm_anomaly_score": lstm_scores.get("anomaly", 0.0),
        "lstm_score": max(lstm_scores.values()),
        "edge_distance_meters": max(0.0, 1.0 - (edge_proximity / 100.0)),
        "edge_proximity_seconds": float(edge_proximity),
        "behavior_duration_seconds": random.randint(1, 200),
        "following_distance": following_distance,
        "pose_classification": "distress" if edge_proximity > 30 else "normal",
        "bounding_box": [100, 100, 200, 300],
        "metadata": {"demo": True},
    }


async def run_demo_loop(iterations: int = 10, delay: float = 1.0):
    for i in range(iterations):
        raw = make_sample_raw_state(person_id=i + 1)
        final = await run_agent_pipeline(raw)
        print(f"--- Demo Iteration {i+1} ---")
        print(final)
        await asyncio.sleep(delay)


if __name__ == "__main__":
    print("Starting RailMind AI local demo runner (agent pipeline simulation)...")
    try:
        asyncio.run(run_demo_loop(iterations=8, delay=0.8))
    except KeyboardInterrupt:
        print("Demo runner interrupted by user.")
