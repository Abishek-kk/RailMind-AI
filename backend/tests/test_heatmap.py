"""Live heatmap aggregation tests."""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.analytics.heatmap import clear_live_heatmaps, get_live_platform_heatmap, update_live_heatmap


def test_live_heatmap_returns_normalized_hotspots():
    clear_live_heatmaps()

    update_live_heatmap(
        "CCTV_P1_04",
        "Platform 1",
        320,
        240,
        [
            {"center": (40, 30)},
            {"bbox": [35, 25, 45, 35]},
            {"center": (280, 210)},
        ],
    )

    rows = get_live_platform_heatmap()

    assert rows
    assert rows[0]["platform"] == "Platform 1"
    assert rows[0]["zone"].startswith("CCTV_P1_04")
    assert rows[0]["intensity"] == 1.0

    clear_live_heatmaps()


def test_live_heatmap_is_empty_without_frames():
    clear_live_heatmaps()

    assert get_live_platform_heatmap() == []
