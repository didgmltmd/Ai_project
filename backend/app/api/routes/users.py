from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.user import FollowRequest
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}")
async def get_user(user_id: int, session: AsyncSession = Depends(get_db)):
    user = await user_service.get_user_profile(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return user


@router.get("/{user_id}/profile")
async def get_profile(user_id: int, currentUserId: int | None = None, session: AsyncSession = Depends(get_db)):
    user = await user_service.get_user_profile(session, user_id, currentUserId)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return user


@router.post("/{user_id}/follow")
async def follow_user(user_id: int, payload: FollowRequest, session: AsyncSession = Depends(get_db)):
    try:
        result = await user_service.toggle_follow(session, user_id, payload.currentUserId)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not result:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return result


@router.get("/{user_id}/followers")
async def get_followers(user_id: int, session: AsyncSession = Depends(get_db)):
    return await user_service.list_followers(session, user_id)


@router.get("/{user_id}/following")
async def get_following(user_id: int, session: AsyncSession = Depends(get_db)):
    return await user_service.list_following(session, user_id)


@router.get("/{user_id}/workout-summary")
async def get_workout_summary(user_id: int, session: AsyncSession = Depends(get_db)):
    return await user_service.workout_summary(session, user_id)
