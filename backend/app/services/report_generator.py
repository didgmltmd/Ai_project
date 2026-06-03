from app.schemas.analysis import Feedback, Issue, Metrics


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
