from dataclasses import dataclass
from typing import Any

from app.core.config import settings


COCO_KEYPOINTS = {
    "left_shoulder": 5,
    "right_shoulder": 6,
    "left_elbow": 7,
    "right_elbow": 8,
    "left_wrist": 9,
    "right_wrist": 10,
    "left_hip": 11,
    "right_hip": 12,
    "left_knee": 13,
    "right_knee": 14,
    "left_ankle": 15,
    "right_ankle": 16,
}


@dataclass
class PoseFrameResult:
    frame_index: int
    timestamp: float
    keypoints: dict[str, tuple[float, float, float]]


class YoloPoseEstimator:
    def __init__(self, model_name: str = settings.yolo_pose_model) -> None:
        self.model_name = model_name
        self._model: Any | None = None

    def _load_model(self) -> Any:
        if self._model is None:
            try:
                from ultralytics import YOLO
            except ImportError as exc:
                raise RuntimeError("ultralytics가 설치되어 있지 않아 YOLO Pose를 실행할 수 없습니다.") from exc
            self._model = YOLO(self.model_name)
        return self._model

    def extract_pose_keypoints(self, frame: Any, frame_index: int, timestamp: float) -> PoseFrameResult:
        model = self._load_model()
        results = model(frame, conf=settings.yolo_conf, classes=[0], verbose=False)
        if not results or results[0].keypoints is None or results[0].keypoints.xy is None:
            return PoseFrameResult(frame_index=frame_index, timestamp=timestamp, keypoints={})

        keypoints_xy = results[0].keypoints.xy[0].cpu().numpy()
        confidence = results[0].keypoints.conf[0].cpu().numpy() if results[0].keypoints.conf is not None else None
        extracted: dict[str, tuple[float, float, float]] = {}
        for name, idx in COCO_KEYPOINTS.items():
            if idx >= len(keypoints_xy):
                continue
            x, y = keypoints_xy[idx]
            score = float(confidence[idx]) if confidence is not None else 1.0
            if score < settings.yolo_conf:
                continue
            extracted[name] = (float(x), float(y), score)
        return PoseFrameResult(frame_index=frame_index, timestamp=timestamp, keypoints=extracted)


class DummyPoseEstimator:
    """Deterministic fallback used when YOLO dependencies are not installed."""

    def extract_pose_keypoints(self, frame: Any, frame_index: int, timestamp: float) -> PoseFrameResult:
        phase = (frame_index // 4) % 8
        elbow_y = 180 + min(phase, 7 - phase) * 11
        keypoints = {
            "left_shoulder": (180, 160, 0.9),
            "left_elbow": (145, elbow_y, 0.9),
            "left_wrist": (120, 250, 0.9),
            "left_hip": (280, 170, 0.9),
            "left_knee": (380, 178, 0.9),
            "left_ankle": (470, 182, 0.9),
        }
        return PoseFrameResult(frame_index=frame_index, timestamp=timestamp, keypoints=keypoints)
