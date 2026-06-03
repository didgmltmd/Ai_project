from pathlib import Path

from app.core.config import settings
from app.services.analysis_repository import analysis_repository
from app.services.frame_extractor import extract_frames
from app.services.pose_estimator import DummyPoseEstimator, YoloPoseEstimator
from app.services.posture_evaluator import evaluate_posture
from app.services.pushup_counter import count_pushups
from app.services.report_generator import generate_report
from app.services.shortform_generator import generate_shortform


def run_pushup_analysis(analysis_id: str, video_path: Path) -> None:
    analysis_repository.update(
        analysis_id,
        status="processing",
        progressStage="영상 프레임 추출 중",
        progressPercent=8,
        currentFrame=0,
        totalFrames=0,
    )
    try:
        frame_payloads = extract_frames(video_path, sample_fps=settings.sample_fps)
        total_frames = len(frame_payloads)
        analysis_repository.update(
            analysis_id,
            progressStage="YOLO Pose 관절 추정 중",
            progressPercent=22,
            currentFrame=0,
            totalFrames=total_frames,
        )

        estimator = _build_pose_estimator()
        pose_frames = []
        for index, item in enumerate(frame_payloads, start=1):
            pose_frames.append(estimator.extract_pose_keypoints(item["image"], item["frameIndex"], item["timestamp"]))
            if index == total_frames or index % 5 == 0:
                percent = 22 + int((index / max(total_frames, 1)) * 36)
                analysis_repository.update(
                    analysis_id,
                    progressStage="YOLO Pose 관절 추정 중",
                    progressPercent=min(percent, 58),
                    currentFrame=index,
                    totalFrames=total_frames,
                )

        analysis_repository.update(
            analysis_id,
            progressStage="푸시업 반복 횟수 계산 중",
            progressPercent=66,
            currentFrame=total_frames,
            totalFrames=total_frames,
        )
        counter_result = count_pushups(pose_frames)

        analysis_repository.update(
            analysis_id,
            progressStage="자세 점수와 피드백 생성 중",
            progressPercent=78,
            currentFrame=total_frames,
            totalFrames=total_frames,
        )
        metrics, issues, rep_issues = evaluate_posture(counter_result)
        feedback = generate_report(counter_result.rep_count, metrics, issues)

        result = {
            "analysisId": analysis_id,
            "status": "completed",
            "exercise": "pushup",
            "repCount": counter_result.rep_count,
            "totalScore": metrics.depthScore
            + metrics.alignmentScore
            + metrics.consistencyScore
            + metrics.stabilityScore,
            "metrics": metrics.model_dump(),
            "issues": [issue.model_dump() for issue in issues],
            "repIssues": rep_issues,
            "feedback": feedback.model_dump(),
            "report": {
                "summary": feedback.summary,
                "strengths": feedback.good,
                "improvements": feedback.improvements,
                "coaching": feedback.coaching,
            },
        }

        analysis_repository.update(
            analysis_id,
            progressStage="분석 숏폼 생성 중",
            progressPercent=92,
            currentFrame=total_frames,
            totalFrames=total_frames,
        )
        shortform_url = generate_shortform(analysis_id, video_path, result)
        result["shortformUrl"] = shortform_url
        result["progressStage"] = "분석 완료"
        result["progressPercent"] = 100
        result["currentFrame"] = total_frames
        result["totalFrames"] = total_frames
        analysis_repository.update(analysis_id, **result)
    except Exception as exc:
        analysis_repository.update(
            analysis_id,
            status="failed",
            progressStage="분석 실패",
            error=f"{type(exc).__name__}: {exc}",
        )


def _build_pose_estimator() -> YoloPoseEstimator | DummyPoseEstimator:
    try:
        import ultralytics  # noqa: F401
    except ImportError:
        return DummyPoseEstimator()
    return YoloPoseEstimator()
