from dataclasses import dataclass

from app.services.pose_estimator import PoseFrameResult
from app.utils.geometry import angle_degrees

UP_ANGLE_THRESHOLD = 155
DOWN_ANGLE_THRESHOLD = 75
MIN_HOLD_FRAMES = 2
MIN_CONFIDENCE = 0.3


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
    """Compute effective elbow angle for shoulder press.

    - Both sides valid: return average of left and right elbow angles.
    - One side valid: return that side's angle.
    - Neither valid: return None (frame skipped).

    A side is valid when all three keypoints (shoulder, elbow, wrist)
    exist and each has confidence >= MIN_CONFIDENCE.
    """
    points = frame.keypoints
    angles: list[float] = []

    for side in ("left", "right"):
        shoulder = points.get(f"{side}_shoulder")
        elbow = points.get(f"{side}_elbow")
        wrist = points.get(f"{side}_wrist")
        if (
            shoulder
            and elbow
            and wrist
            and shoulder[2] >= MIN_CONFIDENCE
            and elbow[2] >= MIN_CONFIDENCE
            and wrist[2] >= MIN_CONFIDENCE
        ):
            angle = angle_degrees(shoulder[:2], elbow[:2], wrist[:2])
            angles.append(angle)

    if not angles:
        return None
    return sum(angles) / len(angles)


def count_shoulder_press(frames: list[PoseFrameResult]) -> CounterResult:
    """Count shoulder press reps using a DOWN→UP state machine.

    State machine:
    - Initial state: DOWN
    - DOWN → UP (angle >= UP_ANGLE_THRESHOLD for 2 consecutive frames): counts a rep
    - UP → DOWN (angle <= DOWN_ANGLE_THRESHOLD for 2 consecutive frames)
    - Angles in (75, 155) exclusive: no transition, reset hold counter
    """
    state = "DOWN"
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

        if state == "DOWN":
            if angle >= UP_ANGLE_THRESHOLD:
                hold_frames += 1
                if hold_frames >= MIN_HOLD_FRAMES:
                    rep_no = len(reps) + 1
                    rep_start_time = features[-MIN_HOLD_FRAMES]["timestamp"]
                    reps.append(
                        RepEvent(
                            rep=rep_no,
                            startTime=rep_start_time,
                            bottomTime=bottom_time if bottom_time > 0 else features[0]["timestamp"],
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
        elif state == "UP":
            if angle <= DOWN_ANGLE_THRESHOLD:
                hold_frames += 1
                if hold_frames >= MIN_HOLD_FRAMES:
                    state = "DOWN"
                    bottom_time = frame.timestamp
                    hold_frames = 0
            else:
                hold_frames = 0

    return CounterResult(rep_count=len(reps), reps=reps, frame_features=features)
