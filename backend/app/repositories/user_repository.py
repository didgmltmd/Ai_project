from typing import Any

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import Analysis
from app.models.follow import Follow
from app.models.user import User
from app.repositories.helpers import ensure_user, user_to_dict


async def get_user_profile(session: AsyncSession, user_id: int, current_user_id: int | None = None) -> dict[str, Any] | None:
    current_user = await ensure_user(session, current_user_id)
    user = await session.get(User, user_id)
    if not user:
        return None
    is_following = (
        await session.execute(select(func.count()).select_from(Follow).where(and_(Follow.follower_id == current_user.id, Follow.following_id == user.id)))
    ).scalar_one() > 0
    return user_to_dict(user, is_following=is_following)


async def toggle_follow(session: AsyncSession, user_id: int, current_user_id: int) -> dict[str, Any] | None:
    if user_id == current_user_id:
        raise ValueError("자기 자신은 팔로우할 수 없습니다.")
    user = await session.get(User, user_id)
    current_user = await ensure_user(session, current_user_id)
    if not user:
        return None
    existing = (await session.execute(select(Follow).where(and_(Follow.follower_id == current_user.id, Follow.following_id == user.id)))).scalar_one_or_none()
    if existing:
        await session.delete(existing)
        user.follower_count = max(user.follower_count - 1, 0)
        current_user.following_count = max(current_user.following_count - 1, 0)
        following = False
    else:
        session.add(Follow(follower_id=current_user.id, following_id=user.id))
        user.follower_count += 1
        current_user.following_count += 1
        following = True
    await session.commit()
    return {"userId": user.id, "currentUserId": current_user.id, "isFollowing": following, "followerCount": user.follower_count}


async def list_followers(session: AsyncSession, user_id: int) -> list[dict[str, Any]]:
    stmt = select(User).join(Follow, Follow.follower_id == User.id).where(Follow.following_id == user_id)
    return [user_to_dict(user) for user in (await session.execute(stmt)).scalars().all()]


async def list_following(session: AsyncSession, user_id: int) -> list[dict[str, Any]]:
    stmt = select(User).join(Follow, Follow.following_id == User.id).where(Follow.follower_id == user_id)
    return [user_to_dict(user) for user in (await session.execute(stmt)).scalars().all()]


async def workout_summary(session: AsyncSession, user_id: int) -> dict[str, Any]:
    await ensure_user(session, user_id)
    row = (
        await session.execute(
            select(func.count(Analysis.id), func.coalesce(func.sum(Analysis.rep_count), 0), func.coalesce(func.avg(Analysis.total_score), 0)).where(Analysis.user_id == user_id)
        )
    ).one()
    return {"userId": user_id, "analysisCount": row[0], "totalReps": int(row[1]), "averageScore": round(float(row[2]), 1)}
