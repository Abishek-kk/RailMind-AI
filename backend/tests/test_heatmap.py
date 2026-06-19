"""Live heatmap aggregation tests."""
from pathlib import Path
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(str(Path(__file__).resolve().parents[1]))

import app.models
from app.analytics.heatmap import (
    clear_live_heatmaps,
    get_live_platform_heatmap,
    get_persistent_platform_heatmap,
    update_live_heatmap,
)
from app.core.database import Base
from app.models.analytics import Analytics
from app.models.platform import Platform


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


def test_heatmap_updates_persist_hotspots_after_memory_clear():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()

    try:
        clear_live_heatmaps()
        update_live_heatmap(
            "CCTV_P2_01",
            "Platform 2",
            320,
            240,
            [{"center": (100, 80)}, {"center": (100, 80)}],
            db=session,
        )

        assert session.query(Platform).count() == 1
        assert session.query(Analytics).count() > 0

        clear_live_heatmaps()
        assert get_live_platform_heatmap() == []

        rows = get_persistent_platform_heatmap(session)

        assert rows
        assert rows[0]["platform"] == "Platform 2"
        assert rows[0]["camera_id"] == "CCTV_P2_01"
        assert rows[0]["zone"].startswith("CCTV_P2_01")
        assert rows[0]["intensity"] == 1.0
    finally:
        session.close()
