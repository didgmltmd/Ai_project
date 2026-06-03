from dataclasses import dataclass

from app.services.pose_estimator import PoseFrameResult
from app.utils.geometry import angle_degrees

UP_ANGLE_THRESHOLD = 150
DOWN_ANGLE_THRESHOLD = 95
MIN_HOLD_FRAMES = 2


@dataclass
class RepEvent:
    rep: int
    startTime: float
    bottomTime: float
    endTime: float
    minElbowAngle: float
    maxElbowAngle: float


@dataclass
class CounterResult:
    rep_count: int
    reps: list[RepEvent]
    frame_features: list[dict]


def _elbow_angle(frame: PoseFrameResult) -> float | None:
    points = frame.keypoints
    for side in ("left", "right"):
        shoulder = points.get(f"{side}_shoulder")
        elbow = points.get(f"{side}_elbow")
        wrist = points.get(f"{side}_wrist")
        if shoulder and elbow and wrist:
            return angle_degrees(shoulder[:2], elbow[:2], wrist[:2])
    return None


def count_pushups(frames: list[PoseFrameResult]) -> CounterResult:
    state = "UP"
    hold_frames = 0
    rep_start_time = 0.0
    bottom_time = 0.0
    min_angle = 180.0
    max_angle = 0.0
    reps: list[RepEvent] = []
    features: list[dict] = []

    for frame in frames:
        angle = _elbow_angle(frame)
        if angle is None:
            continue

        min_angle = min(min_angle, angle)
        max_angle = max(max_angle, angle)
        features.append(
            {
                "frameIndex": frame.frame_index,
                "timestamp": frame.timestamp,
                "elbowAngle": angle,
                "state": state,
            }
        )

        if state == "UP":
            if angle <= DOWN_ANGLE_THRESHOLD:
                hold_frames += 1
                if hold_frames >= MIN_HOLD_FRAMES:
                    state = "DOWN"
                    bottom_time = frame.timestamp
                    rep_start_time = features[-MIN_HOLD_FRAMES]["timestamp"]
                    hold_frames = 0
            else:
                hold_frames = 0
        elif state == "DOWN":
            if angle >= UP_ANGLE_THRESHOLD:
                hold_frames += 1
                if hold_frames >= MIN_HOLD_FRAMES:
                    rep_no = len(reps) + 1
                    reps.append(
                        RepEvent(
                            rep=rep_no,
                            startTime=rep_start_time,
                            bottomTime=bottom_time,
                            endTime=frame.timestamp,
                            minElbowAngle=min_angle,
                            maxElbowAngle=max_angle,
                        )
                    )
                    state = "UP"
                    hold_frames = 0
                    min_angle = 180.0
                    max_angle = 0.0
            else:
                hold_frames = 0

    return CounterResult(rep_count=len(reps), reps=reps, frame_features=features)
