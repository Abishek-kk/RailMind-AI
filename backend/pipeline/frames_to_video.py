"""
frames_to_video.py

Stitches a directory of annotated frames back into a single video file.

Usage:
    from frames_to_video import frames_to_video
    frames_to_video(
        frames_dir="pipeline_data/<video_id>/annotated",
        output_path="pipeline_data/<video_id>/annotated_output.mp4",
        fps=25,  # match the original video's FPS
    )
"""

import os
import shutil
import subprocess
import cv2


def frames_to_video(frames_dir, output_path, fps=30, image_ext=".jpg",
                     fourcc_str="mp4v", reencode_for_browser=True):
    """
    frames_dir:   directory containing frames, sorted alphabetically
                  (your pipeline already names them safety_frame_000000.jpg etc,
                  so plain sort() puts them back in the correct order)
    output_path:  path to write the final .mp4
    fps:          MUST match the frame rate the frames were extracted at,
                  or playback speed will be wrong. Use the same value you
                  passed into the pipeline (or read it back from the
                  original source video -- see get_fps_from_video below).
    fourcc_str:   video codec for the initial write. "mp4v" is the most
                  widely supported by OpenCV builds, but browsers often
                  won't play mp4v directly in a <video> tag.
    reencode_for_browser: if True (default), after writing with mp4v,
                  automatically re-encodes to H.264 (yuv420p, faststart)
                  via ffmpeg -- the combination that reliably plays in
                  browsers. Requires ffmpeg on PATH. If ffmpeg isn't
                  found, this step is skipped with a warning and you're
                  left with the mp4v file (fine for local playback,
                  often not for a web <video> tag).
    """
    frame_files = sorted(f for f in os.listdir(frames_dir) if f.lower().endswith(image_ext))
    if not frame_files:
        raise RuntimeError(f"No '{image_ext}' frames found in '{frames_dir}'")

    first_frame = cv2.imread(os.path.join(frames_dir, frame_files[0]))
    if first_frame is None:
        raise RuntimeError(f"Could not read first frame: {frame_files[0]}")
    height, width = first_frame.shape[:2]
    raw_path = output_path + ".raw.mp4" if reencode_for_browser else output_path

    fourcc = cv2.VideoWriter_fourcc(*fourcc_str)
    writer = cv2.VideoWriter(raw_path, fourcc, fps, (width, height))
    if not writer.isOpened():
        raise RuntimeError(
            f"VideoWriter failed to open with fourcc='{fourcc_str}'. "
            f"Your OpenCV build may lack this codec. Try a different fourcc_str."
        )

    print(f"Writing {len(frame_files)} frames -> '{raw_path}' at {fps} fps ({width}x{height})")
    for i, fname in enumerate(frame_files):
        frame = cv2.imread(os.path.join(frames_dir, fname))
        if frame is None:
            print(f"  Warning: could not read '{fname}', skipping")
            continue
        if frame.shape[:2] != (height, width):
            frame = cv2.resize(frame, (width, height))
        writer.write(frame)

        if (i + 1) % 50 == 0 or (i + 1) == len(frame_files):
            print(f"  {i + 1}/{len(frame_files)} frames written")

    writer.release()

    if not reencode_for_browser:
        print(f"Done: '{output_path}'")
        return

    if shutil.which("ffmpeg") is None:
        print("Warning: ffmpeg not found on PATH -- skipping browser re-encode. "
              f"Renaming raw file to final output path instead: '{output_path}'")
        os.replace(raw_path, output_path)
        return

    print(f"Re-encoding to browser-compatible H.264 -> '{output_path}'")
    cmd = [
        "ffmpeg", "-y", "-i", raw_path,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    os.remove(raw_path)

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg re-encode failed:\n{result.stderr}")

    print(f"Done: '{output_path}'")


def get_fps_from_video(video_path, fallback=25):
    """Read the FPS of the original source video, so the output matches it exactly."""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    if not fps or fps <= 1:
        return fallback
    return fps


# if __name__ == "__main__":
#     frames_dir = "../pipeline/pipeline/02d89ad6f186af41/annotated"
#     output_path = "annotated_output.mp4"
#     fps = 30

#     frames_to_video(frames_dir, output_path, fps=fps)