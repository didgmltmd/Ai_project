from dataclasses import dataclass
from statistics import pstdev

from app.schemas.analysis import Issue
from app.services.pose_estimator import PoseFrameResult
from app.services.shoulder_press_counter import CounterResult, RepEvent
from app.utils.geometry import angle_degrees

MIN_CONFIDENCE = 0.3


@dataclass
class ShoulderPressMetrics:
    symmetryScore: int  # 0-100
    overextensionScore: int  # 0-100
    alignmentScore: int  # 0-100
    consistencyScore: int | None  # 0-100 or None if < 2 reps


def _frames_in_rep(pose_frames: list[PoseFrameResult], rep: RepEvent) -> list[PoseFrameResult]:
    """Return pose frames whose timestamp falls within the rep's time window."""
    return [f for f in pose_frames if rep.startTime <= f.timestamp <= rep.endTime]


def _left_right_elbow_angles(frame: PoseFrameResult) -> tuple[float | None, float | None]:
    """Compute left and right elbow angles from a single frame.

    Returns (left_angle, right_angle). Either may be None if keypoints
    are missing or below confidence threshold.
    """
    kp = frame.keypoints
    left_angle: float | None = None
    right_angle: float | None = None

    # Left elbow angle: left_shoulder -> left_elbow -> left_wrist
    ls = kp.get("left_shoulder")
    le = kp.get("left_elbow")
    lw = kp.get("left_wrist")
    if (
        ls and le and lw
        and ls[2] >= MIN_CONFIDENCE
        and le[2] >= MIN_CONFIDENCE
        and lw[2] >= MIN_CONFIDENCE
    ):
        left_angle = angle_degrees(ls[:2], le[:2], lw[:2])

    # Right elbow angle: right_shoulder -> right_elbow -> right_wrist
    rs = kp.get("right_shoulder")
    re = kp.get("right_elbow")
    rw = kp.get("right_wrist")
    if (
        rs and re and rw
        and rs[2] >= MIN_CONFIDENCE
        and re[2] >= MIN_CONFIDENCE
        and rw[2] >= MIN_CONFIDENCE
    ):
        right_angle = angle_degrees(rs[:2], re[:2], rw[:2])

    return left_angle, right_angle


def _evaluate_symmetry(
    reps: list[RepEvent],
    pose_frames: list[PoseFrameResult],
    rep_issues: dict[int, list[str]],
) -> tuple[int, list[Issue]]:
    """Evaluate left/right elbow angle symmetry per rep.

    Asymmetry issue if left/right difference > 15° for a rep.
    """
    issues: list[Issue] = []
    asymmetry_reps: list[int] = []

    for rep in reps:
        frames = _frames_in_rep(pose_frames, rep)
        differences: list[float] = []

        for frame in frames:
            left_angle, right_angle = _left_right_elbow_angles(frame)
            if left_angle is not None and right_angle is not None:
                differences.append(abs(left_angle - right_angle))

        if differences:
            max_diff = max(differences)
            if max_diff > 15.0:
                asymmetry_reps.append(rep.rep)
                rep_issues[rep.rep].append("asymmetry")

    if asymmetry_reps:
        issues.append(
            Issue(
                type="asymmetry",
                reps=asymmetry_reps,
                message="일부 반복에서 좌우 팔꿈치 각도 차이가 15도를 초과합니다.",
            )
        )

    # Score: 100 if no asymmetry reps, deduct per asymmetry rep
    if not reps:
        score = 100
    else:
        score = max(0, 100 - int((len(asymmetry_reps) / len(reps)) * 100))

    return score, issues


def _evaluate_overextension(
    reps: list[RepEvent],
    pose_frames: list[PoseFrameResult],
    rep_issues: dict[int, list[str]],
) -> tuple[int, list[Issue]]:
    """Evaluate overextension in UP state.

    Overextension issue if elbow angle > 175° during UP phase of a rep.
    We check frames near the end of the rep (UP state) for max angle.
    """
    issues: list[Issue] = []
    overextension_reps: list[int] = []

    for rep in reps:
        frames = _frames_in_rep(pose_frames, rep)
        has_overextension = False

        for frame in frames:
            left_angle, right_angle = _left_right_elbow_angles(frame)
            # Check if either arm exceeds 175° (overextension)
            if left_angle is not None and left_angle > 175.0:
                has_overextension = True
            if right_angle is not None and right_angle > 175.0:
                has_overextension = True

        if has_overextension:
            overextension_reps.append(rep.rep)
            rep_issues[rep.rep].append("overextension")

    if overextension_reps:
        issues.append(
            Issue(
                type="overextension",
                reps=overextension_reps,
                message="일부 반복에서 팔꿈치가 과도하게 펴졌습니다 (175도 초과).",
            )
        )

    if not reps:
        score = 100
    else:
        score = max(0, 100 - int((len(overextension_reps) / len(reps)) * 100))

    return score, issues


def _evaluate_alignment(
    reps: list[RepEvent],
    pose_frames: list[PoseFrameResult],
    rep_issues: dict[int, list[str]],
) -> tuple[int, list[Issue]]:
    """Evaluate back alignment (shoulder-hip vertical deviation).

    Excessive arch issue if vertical distance between average shoulder
    keypoints (5,6) and average hip keypoints (11,12) > 30px.
    """
    issues: list[Issue] = []
    arch_reps: list[int] = []

    for rep in reps:
        frames = _frames_in_rep(pose_frames, rep)
        has_excessive_arch = False

        for frame in frames:
            kp = frame.keypoints
            ls = kp.get("left_shoulder")
            rs = kp.get("right_shoulder")
            lh = kp.get("left_hip")
            rh = kp.get("right_hip")

            # Need at least one shoulder and one hip with sufficient confidence
            shoulder_points: list[tuple[float, float]] = []
            if ls and ls[2] >= MIN_CONFIDENCE:
                shoulder_points.append((ls[0], ls[1]))
            if rs and rs[2] >= MIN_CONFIDENCE:
                shoulder_points.append((rs[0], rs[1]))

            hip_points: list[tuple[float, float]] = []
            if lh and lh[2] >= MIN_CONFIDENCE:
                hip_points.append((lh[0], lh[1]))
            if rh and rh[2] >= MIN_CONFIDENCE:
                hip_points.append((rh[0], rh[1]))

            if not shoulder_points or not hip_points:
                continue

            avg_shoulder_x = sum(p[0] for p in shoulder_points) / len(shoulder_points)
            avg_hip_x = sum(p[0] for p in hip_points) / len(hip_points)

            # Vertical deviation = horizontal distance in image coordinates
            # (x-axis represents the horizontal/vertical alignment of torso)
            # Actually, "수직 정렬 편차" means vertical deviation:
            # shoulder and hip should be vertically aligned, so we measure
            # horizontal (x) offset between them
            vertical_deviation = abs(avg_shoulder_x - avg_hip_x)

            if vertical_deviation > 30.0:
                has_excessive_arch = True
                break

        if has_excessive_arch:
            arch_reps.append(rep.rep)
            rep_issues[rep.rep].append("excessive_arch")

    if arch_reps:
        issues.append(
            Issue(
                type="excessive_arch",
                reps=arch_reps,
                message="일부 반복에서 등이 과도하게 젖혀졌습니다 (어깨-엉덩이 편차 30px 초과).",
            )
        )

    if not reps:
        score = 100
    else:
        score = max(0, 100 - int((len(arch_reps) / len(reps)) * 100))

    return score, issues


def _evaluate_consistency(reps: list[RepEvent]) -> tuple[int | None, list[Issue]]:
    """Evaluate rep duration consistency.

    Inconsistent tempo issue if standard deviation of rep durations > 1.0s.
    Returns None score if < 2 reps.
    """
    if len(reps) < 2:
        return None, []

    durations = [max(rep.endTime - rep.startTime, 0.01) for rep in reps]
    duration_std = pstdev(durations)

    issues: list[Issue] = []
    if duration_std > 1.0:
        issues.append(
            Issue(
                type="inconsistent_tempo",
                reps=[rep.rep for rep in reps],
                message="반복 간 동작 속도 차이가 큽니다.",
            )
        )

    # Score: 100 if std is 0, linearly decrease as std increases
    score = max(0, min(100, int(100 - duration_std * 50)))

    return score, issues


def evaluate_shoulder_press(
    counter_result: CounterResult,
    pose_frames: list[PoseFrameResult],
) -> tuple[ShoulderPressMetrics, list[Issue], dict[int, list[str]]]:
    """Evaluate shoulder press form and return metrics, issues, and per-rep issue mapping.

    Args:
        counter_result: Result from shoulder press counter with rep events.
        pose_frames: Full list of pose frame results for bilateral analysis.

    Returns:
        Tuple of (ShoulderPressMetrics, list of Issues, per-rep issue mapping).
    """
    reps = counter_result.reps

    if not reps:
        return (
            ShoulderPressMetrics(
                symmetryScore=100,
                overextensionScore=100,
                alignmentScore=100,
                consistencyScore=None,
            ),
            [Issue(type="no_valid_rep", reps=[], message="유효한 숄더 프레스 반복을 찾지 못했습니다.")],
            {},
        )

    rep_issues: dict[int, list[str]] = {rep.rep: [] for rep in reps}
    all_issues: list[Issue] = []

    # 1. Symmetry evaluation
    symmetry_score, symmetry_issues = _evaluate_symmetry(reps, pose_frames, rep_issues)
    all_issues.extend(symmetry_issues)

    # 2. Overextension evaluation
    overextension_score, overextension_issues = _evaluate_overextension(reps, pose_frames, rep_issues)
    all_issues.extend(overextension_issues)

    # 3. Back alignment evaluation
    alignment_score, alignment_issues = _evaluate_alignment(reps, pose_frames, rep_issues)
    all_issues.extend(alignment_issues)

    # 4. Consistency evaluation
    consistency_score, consistency_issues = _evaluate_consistency(reps)
    all_issues.extend(consistency_issues)

    metrics = ShoulderPressMetrics(
        symmetryScore=symmetry_score,
        overextensionScore=overextension_score,
        alignmentScore=alignment_score,
        consistencyScore=consistency_score,
    )

    return metrics, all_issues, rep_issues
