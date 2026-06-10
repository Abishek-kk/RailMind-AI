from fastapi import APIRouter

router = APIRouter()

@router.get("")
async def health_check():
    """Returns the operational status of the RailMind AI backend engine."""
    return {
        "status": "online",
        "system": "RailMind AI",
        "version": "1.0.0",
        "gpu_available": False  # Toggle based on actual inference device
    }