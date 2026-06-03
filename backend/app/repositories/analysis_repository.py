from typing import Any

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.analysis import Analysis
from app.models.feed import Feed
from app.repositories.helpers import ensure_user


async def persist_completed_analysis(
    result: dict[str, Any],
    original_video_url: str | None,
    user_id: int | None = None,
    caption: str | None = None,
    publish_to_feed: bool = False,
) -> None:
    async with AsyncSessionLocal() as session:
        user = await ensure_user(session, user_id)
        metrics = result.get("metrics") or {}
        feedback = result.get("feedback") or {}
        analysis_id = result["analysisId"]
        existing = (await session.execute(select(Analysis).where(Analysis.analysis_id == analysis_id))).scalar_one_or_none()
        if existing:
            return

        feed: Feed | None = None
        if publish_to_feed:
            feed = Feed(
                author_id=user.id,
                video_url=result.get("shortformUrl") or original_video_url,
                shortform_url=result.get("shortformUrl"),
                exercise_type=result.get("exercise") or "pushup",
                rep_count=result.get("repCount") or 0,
                score=result.get("totalScore") or 0,
                summary_feedback=feedback.get("summary"),
                caption=caption or "AI 자세 분석 결과",
                hashtags=["#푸시업", "#AI자세분석", "#운동기록"],
                is_mine=True,
            )
            session.add(feed)
            await session.flush()
            user.post_count += 1

        analysis = Analysis(
            analysis_id=analysis_id,
            user_id=user.id,
            feed_id=feed.id if feed else None,
            exercise=result.get("exercise") or "pushup",
            rep_count=result.get("repCount") or 0,
            total_score=result.get("totalScore") or 0,
            depth_score=metrics.get("depthScore") or 0,
            alignment_score=metrics.get("alignmentScore") or 0,
            consistency_score=metrics.get("consistencyScore") or 0,
            stability_score=metrics.get("stabilityScore") or 0,
            issues=result.get("issues") or [],
            feedback=feedback,
            original_video_url=original_video_url,
            shortform_url=result.get("shortformUrl"),
        )
        session.add(analysis)
        await session.commit()
