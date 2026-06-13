from typing import TYPE_CHECKING

from app.schemas.analysis import Feedback, Issue, Metrics

if TYPE_CHECKING:
    from app.services.shoulder_press_evaluator import ShoulderPressMetrics


def generate_report(rep_count: int, metrics: Metrics, issues: list[Issue]) -> Feedback:
    total = metrics.depthScore + metrics.alignmentScore + metrics.consistencyScore + metrics.stabilityScore
    summary = f"총 {rep_count}회의 푸시업을 수행했으며 전체 자세 점수는 {total}점입니다."

    good: list[str] = []
    if metrics.depthScore >= 28:
        good.append("동작 깊이가 전반적으로 충분합니다.")
    if metrics.alignmentScore >= 24:
        good.append("몸통 정렬이 비교적 안정적입니다.")
    if metrics.consistencyScore >= 15:
        good.append("반복 간 리듬이 일정한 편입니다.")
    if not good:
        good.append("분석 가능한 반복을 기준으로 기본 동작 흐름을 확인했습니다.")

    improvements = [issue.message for issue in issues] or ["현재 MVP 분석 기준에서는 큰 문제 구간이 감지되지 않았습니다."]
    coaching = "반복 수를 늘리기보다 같은 깊이와 정렬을 유지하는 데 집중해 보세요."
    if rep_count == 0:
        coaching = "측면에서 전신이 보이도록 다시 촬영하고, 팔꿈치가 충분히 굽혀지는지 확인해 보세요."

    return Feedback(summary=summary, good=good, improvements=improvements, coaching=coaching)


def generate_shoulder_press_report(rep_count: int, metrics: "ShoulderPressMetrics", issues: list[Issue]) -> Feedback:
    scores = [metrics.symmetryScore, metrics.overextensionScore, metrics.alignmentScore]
    if metrics.consistencyScore is not None:
        scores.append(metrics.consistencyScore)
    avg_score = int(sum(scores) / len(scores))

    summary = f"총 {rep_count}회의 숄더 프레스를 수행했으며 전체 자세 점수는 {avg_score}점입니다."

    good: list[str] = []
    if metrics.symmetryScore >= 80:
        good.append("좌우 팔 대칭성이 양호합니다.")
    if metrics.overextensionScore >= 80:
        good.append("팔꿈치 과신전 없이 안정적으로 수행했습니다.")
    if metrics.alignmentScore >= 80:
        good.append("등 정렬이 잘 유지되었습니다.")
    if metrics.consistencyScore is not None and metrics.consistencyScore >= 80:
        good.append("반복 간 리듬이 일정한 편입니다.")
    if not good:
        good.append("분석 가능한 반복을 기준으로 기본 동작 흐름을 확인했습니다.")

    improvements = [issue.message for issue in issues] or ["현재 분석 기준에서는 큰 문제 구간이 감지되지 않았습니다."]

    coaching = "무게를 올리기보다 좌우 대칭과 등 정렬을 유지하는 데 집중해 보세요."
    if rep_count == 0:
        coaching = "정면 또는 측면에서 상체가 보이도록 다시 촬영하고, 팔꿈치가 충분히 굽혀지고 펴지는지 확인해 보세요."

    return Feedback(summary=summary, good=good, improvements=improvements, coaching=coaching)
