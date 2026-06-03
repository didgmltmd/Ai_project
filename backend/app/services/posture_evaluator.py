from statistics import pstdev

from app.schemas.analysis import Issue, Metrics
from app.services.pushup_counter import CounterResult


def evaluate_posture(counter_result: CounterResult) -> tuple[Metrics, list[Issue], dict[int, list[str]]]:
    reps = counter_result.reps
    if not reps:
        return (
            Metrics(depthScore=0, alignmentScore=10, consistencyScore=0, stabilityScore=8),
            [Issue(type="no_valid_rep", reps=[], message="유효한 푸시업 반복을 찾지 못했습니다.")],
            {},
        )

    issues: list[Issue] = []
    rep_issues: dict[int, list[str]] = {rep.rep: [] for rep in reps}

    shallow_reps = [rep.rep for rep in reps if rep.minElbowAngle > 105]
    if shallow_reps:
        issues.append(
            Issue(
                type="shallow_depth",
                reps=shallow_reps,
                message="일부 반복에서 팔꿈치 굽힘 깊이가 충분하지 않습니다.",
            )
        )
        for rep in shallow_reps:
            rep_issues[rep].append("shallow_depth")

    durations = [max(rep.endTime - rep.startTime, 0.01) for rep in reps]
    duration_std = pstdev(durations) if len(durations) > 1 else 0.0

    depth_score = max(0, 35 - len(shallow_reps) * 5)
    alignment_score = 26
    consistency_score = max(8, int(20 - duration_std * 4))
    stability_score = 12

    if duration_std > 1.0:
        issues.append(
            Issue(
                type="inconsistent_tempo",
                reps=[rep.rep for rep in reps],
                message="반복 간 동작 속도 차이가 큽니다.",
            )
        )

    return (
        Metrics(
            depthScore=depth_score,
            alignmentScore=alignment_score,
            consistencyScore=consistency_score,
            stabilityScore=stability_score,
        ),
        issues,
        rep_issues,
    )
