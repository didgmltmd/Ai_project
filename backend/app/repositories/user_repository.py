from typing import Any

from sqlalchemy import and_, func, select
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


async def update_user_profile(session: AsyncSession, user_id: int, payload: dict[str, Any]) -> dict[str, Any] | None:
    user = await session.get(User, user_id)
    if not user:
        return None

    username = payload.get("username")
    if username is not None:
        username = username.strip()
        if not username:
            raise ValueError("닉네임을 입력하세요.")
        existing = (await session.execute(select(User).where(User.username == username, User.id != user.id))).scalar_one_or_none()
        if existing:
            raise ValueError("이미 사용 중인 닉네임입니다.")
        user.username = username
        user.display_name = payload.get("displayName") or username

    if payload.get("displayName") is not None:
        display_name = payload["displayName"].strip()
        if display_name:
            user.display_name = display_name
    if payload.get("profileImageUrl") is not None:
        user.profile_image_url = payload["profileImageUrl"].strip() or None
    if payload.get("bio") is not None:
        user.bio = payload["bio"].strip() or None
    if payload.get("workoutIntro") is not None:
        user.workout_intro = payload["workoutIntro"].strip() or None

    await session.commit()
    await session.refresh(user)
    return user_to_dict(user)


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
