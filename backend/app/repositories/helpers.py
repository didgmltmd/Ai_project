from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

DEFAULT_USER_ID = 1


async def ensure_user(session: AsyncSession, user_id: int | None = None) -> User:
    target_id = user_id or DEFAULT_USER_ID
    user = await session.get(User, target_id)
    if user:
        return user

    user = User(
        id=target_id,
        username="me" if target_id == DEFAULT_USER_ID else f"user{target_id}",
        email="me@pushform.local" if target_id == DEFAULT_USER_ID else f"user{target_id}@pushform.local",
        display_name="나" if target_id == DEFAULT_USER_ID else f"사용자 {target_id}",
        profile_image_url=None,
        bio="푸시업 자세를 기록하고 공유합니다.",
        workout_intro="AI 자세 분석으로 매일 푸시업을 개선하고 있습니다.",
        is_mock=False,
    )
    session.add(user)
    await session.flush()
    return user


async def get_required_user(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


def iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def user_to_dict(user: User, *, is_following: bool | None = None) -> dict[str, Any]:
    payload = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "displayName": user.display_name,
        "profileImageUrl": user.profile_image_url,
        "bio": user.bio,
        "workoutIntro": user.workout_intro,
        "followerCount": user.follower_count,
        "followingCount": user.following_count,
        "postCount": user.post_count,
        "isMock": user.is_mock,
    }
    if is_following is not None:
        payload["isFollowing"] = is_following
    return payload
