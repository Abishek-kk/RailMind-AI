import os
from pathlib import Path

import cv2
import numpy as np

from pipeline.frames_to_video import find_ffmpeg_binary, frames_to_video


def test_find_ffmpeg_binary_prefers_explicit_path(monkeypatch):
    monkeypatch.setenv("FFMPEG_PATH", "C:/ffmpeg/bin/ffmpeg.exe")
    monkeypatch.setattr("pipeline.frames_to_video.shutil.which", lambda cmd: None)
    assert find_ffmpeg_binary() == "C:/ffmpeg/bin/ffmpeg.exe"


def test_frames_to_video_without_ffmpeg_keeps_mp4(tmp_path, monkeypatch):
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()
    output_path = tmp_path / "annotated_output.mp4"

    for idx in range(2):
        frame = np.zeros((32, 32, 3), dtype=np.uint8)
        cv2.imwrite(str(frames_dir / f"frame_{idx:06d}.jpg"), frame)

    monkeypatch.setattr("pipeline.frames_to_video.find_ffmpeg_binary", lambda: None)
    frames_to_video(str(frames_dir), str(output_path), fps=10, reencode_for_browser=True)

    assert output_path.exists()
    assert output_path.stat().st_size > 0
