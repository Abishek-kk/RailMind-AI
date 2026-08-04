import json
import os
import shutil
import tempfile

from pipeline import pipeline


def test_pipeline_paths_are_resolved_from_module_location(monkeypatch):
    monkeypatch.chdir("D:\\pro")

    work_root = pipeline._get_work_root()
    model_path = pipeline._get_model_path()

    assert os.path.isabs(work_root)
    assert os.path.isabs(model_path)
    assert os.path.normpath(work_root) == os.path.normpath(
        os.path.join(pipeline._get_backend_root(), "pipeline_data")
    )
    assert os.path.basename(model_path) == "yolov8n-pose.pt"


def test_ensure_zones_calibrated_falls_back_when_interactive_calibration_is_unavailable(monkeypatch):
    temp_dir = tempfile.mkdtemp(prefix="railmind-test-", dir="D:\\pro")
    try:
        frames_dir = os.path.join(temp_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)
        with open(os.path.join(frames_dir, "frame_000000.jpg"), "wb") as handle:
            handle.write(b"fake")
        zones_path = os.path.join(temp_dir, "zones.json")

        monkeypatch.setenv("RAILMIND_INTERACTIVE_ZONE_CALIBRATION", "0")
        monkeypatch.setattr(pipeline, "_get_config_zones", lambda _path: (_ for _ in ()).throw(RuntimeError("no display")))

        zones = pipeline._ensure_zones_calibrated(frames_dir, zones_path)

        assert zones["track_zone"] == [(0, 0), (1, 0), (1, 1), (0, 1)]
        assert zones["platform_zone"] == [(0, 0), (1, 0), (1, 1), (0, 1)]
        assert os.path.exists(zones_path)
        persisted = json.loads(open(zones_path, "r", encoding="utf-8").read())
        assert persisted["track_zone"] == [[0, 0], [1, 0], [1, 1], [0, 1]]
        assert persisted["platform_zone"] == [[0, 0], [1, 0], [1, 1], [0, 1]]
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
