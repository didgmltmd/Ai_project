from pathlib import Path
from typing import Any

import cv2


def extract_frames(video_path: Path, sample_fps: int) -> list[dict[str, Any]]:
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError("영상 파일을 열 수 없습니다.")

    source_fps = capture.get(cv2.CAP_PROP_FPS) or 30
    frame_interval = max(int(source_fps // sample_fps), 1)
    frames: list[dict[str, Any]] = []
    frame_index = 0

    while True:
        ok, frame = capture.read()
        if not ok:
            break
        if frame_index % frame_interval == 0:
            frames.append(
                {
                    "frameIndex": frame_index,
                    "timestamp": frame_index / source_fps,
                    "image": frame,
                }
            )
        frame_index += 1

    capture.release()
    return frames
