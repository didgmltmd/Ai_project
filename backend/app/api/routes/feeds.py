from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.feed import CommentCreateRequest, UserActionRequest
from app.services import feed_service

router = APIRouter(prefix="/feeds", tags=["feeds"])


@router.get("")
async def get_feeds(
    currentUserId: int | None = Query(default=None),
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
):
    return await feed_service.list_feeds(session, currentUserId, limit, offset)


@router.get("/saved")
async def get_saved_feeds(userId: int, session: AsyncSession = Depends(get_db)):
    return await feed_service.list_saved(session, userId)


@router.get("/mine")
async def get_my_feeds(userId: int, session: AsyncSession = Depends(get_db)):
    return await feed_service.list_mine(session, userId)


@router.get("/{feed_id}")
async def get_feed(feed_id: int, currentUserId: int | None = None, session: AsyncSession = Depends(get_db)):
    feed = await feed_service.get_feed(session, feed_id, currentUserId)
    if not feed:
        raise HTTPException(status_code=404, detail="피드를 찾을 수 없습니다.")
    return feed


@router.post("/{feed_id}/like")
async def like_feed(feed_id: int, payload: UserActionRequest, session: AsyncSession = Depends(get_db)):
    result = await feed_service.toggle_like(session, feed_id, payload.userId or 1)
    if not result:
        raise HTTPException(status_code=404, detail="피드를 찾을 수 없습니다.")
    return result


@router.post("/{feed_id}/save")
async def save_feed(feed_id: int, payload: UserActionRequest, session: AsyncSession = Depends(get_db)):
    result = await feed_service.toggle_save(session, feed_id, payload.userId or 1)
    if not result:
        raise HTTPException(status_code=404, detail="피드를 찾을 수 없습니다.")
    return result


@router.get("/{feed_id}/comments")
async def get_comments(feed_id: int, session: AsyncSession = Depends(get_db)):
    comments = await feed_service.list_comments(session, feed_id)
    if comments is None:
        raise HTTPException(status_code=404, detail="피드를 찾을 수 없습니다.")
    return comments


@router.post("/{feed_id}/comments", status_code=201)
async def create_comment(feed_id: int, payload: CommentCreateRequest, session: AsyncSession = Depends(get_db)):
    try:
        comment = await feed_service.add_comment(session, feed_id, payload.userId or 1, payload.content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not comment:
        raise HTTPException(status_code=404, detail="피드를 찾을 수 없습니다.")
    return comment
