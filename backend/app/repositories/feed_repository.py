from typing import Any

from sqlalchemy import and_, delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment
from app.models.feed import Feed
from app.models.like import FeedLike
from app.models.save import SavedFeed
from app.models.user import User
from app.repositories.helpers import ensure_user, iso


async def list_feeds(session: AsyncSession, current_user_id: int | None, limit: int, offset: int) -> list[dict[str, Any]]:
    current_user = await ensure_user(session, current_user_id)
    stmt = select(Feed, User).join(User, Feed.author_id == User.id).order_by(desc(Feed.created_at)).limit(limit).offset(offset)
    rows = (await session.execute(stmt)).all()
    return [await feed_to_dict(session, feed, author, current_user.id) for feed, author in rows]


async def get_feed(session: AsyncSession, feed_id: int, current_user_id: int | None) -> dict[str, Any] | None:
    current_user = await ensure_user(session, current_user_id)
    row = (await session.execute(select(Feed, User).join(User, Feed.author_id == User.id).where(Feed.id == feed_id))).first()
    if not row:
        return None
    return await feed_to_dict(session, row[0], row[1], current_user.id)


async def list_saved(session: AsyncSession, user_id: int) -> list[dict[str, Any]]:
    user = await ensure_user(session, user_id)
    stmt = (
        select(Feed, User)
        .join(SavedFeed, SavedFeed.feed_id == Feed.id)
        .join(User, Feed.author_id == User.id)
        .where(SavedFeed.user_id == user.id)
        .order_by(desc(SavedFeed.created_at))
    )
    rows = (await session.execute(stmt)).all()
    return [await feed_to_dict(session, feed, author, user.id) for feed, author in rows]


async def list_mine(session: AsyncSession, user_id: int) -> list[dict[str, Any]]:
    user = await ensure_user(session, user_id)
    rows = (await session.execute(select(Feed, User).join(User).where(Feed.author_id == user.id).order_by(desc(Feed.created_at)))).all()
    return [await feed_to_dict(session, feed, author, user.id) for feed, author in rows]


async def toggle_like(session: AsyncSession, feed_id: int, user_id: int) -> dict[str, Any] | None:
    user = await ensure_user(session, user_id)
    feed = await session.get(Feed, feed_id)
    if not feed:
        return None
    existing = (await session.execute(select(FeedLike).where(and_(FeedLike.feed_id == feed_id, FeedLike.user_id == user.id)))).scalar_one_or_none()
    if existing:
        await session.delete(existing)
        feed.like_count = max(feed.like_count - 1, 0)
        liked = False
    else:
        session.add(FeedLike(feed_id=feed_id, user_id=user.id))
        feed.like_count += 1
        liked = True
    await session.commit()
    return {"feedId": feed_id, "liked": liked, "likeCount": feed.like_count}


async def toggle_save(session: AsyncSession, feed_id: int, user_id: int) -> dict[str, Any] | None:
    user = await ensure_user(session, user_id)
    feed = await session.get(Feed, feed_id)
    if not feed:
        return None
    existing = (await session.execute(select(SavedFeed).where(and_(SavedFeed.feed_id == feed_id, SavedFeed.user_id == user.id)))).scalar_one_or_none()
    if existing:
        await session.delete(existing)
        feed.save_count = max(feed.save_count - 1, 0)
        saved = False
    else:
        session.add(SavedFeed(feed_id=feed_id, user_id=user.id))
        feed.save_count += 1
        saved = True
    await session.commit()
    return {"feedId": feed_id, "saved": saved, "saveCount": feed.save_count}


async def list_comments(session: AsyncSession, feed_id: int) -> list[dict[str, Any]] | None:
    if not await session.get(Feed, feed_id):
        return None
    stmt = select(Comment, User).join(User, Comment.user_id == User.id).where(Comment.feed_id == feed_id).order_by(Comment.created_at)
    rows = (await session.execute(stmt)).all()
    return [
        {
            "id": comment.id,
            "feedId": comment.feed_id,
            "userId": comment.user_id,
            "username": user.username,
            "displayName": user.display_name,
            "content": comment.content,
            "createdAt": iso(comment.created_at),
        }
        for comment, user in rows
    ]


async def add_comment(session: AsyncSession, feed_id: int, user_id: int, content: str) -> dict[str, Any] | None:
    if not content.strip():
        raise ValueError("댓글 내용을 입력해 주세요.")
    user = await ensure_user(session, user_id)
    feed = await session.get(Feed, feed_id)
    if not feed:
        return None
    comment = Comment(feed_id=feed_id, user_id=user.id, content=content.strip())
    feed.comment_count += 1
    session.add(comment)
    await session.commit()
    await session.refresh(comment)
    return {
        "id": comment.id,
        "feedId": feed_id,
        "userId": user.id,
        "username": user.username,
        "displayName": user.display_name,
        "content": comment.content,
        "createdAt": iso(comment.created_at),
    }


async def feed_to_dict(session: AsyncSession, feed: Feed, author: User, current_user_id: int) -> dict[str, Any]:
    liked = (await session.execute(select(func.count()).select_from(FeedLike).where(and_(FeedLike.feed_id == feed.id, FeedLike.user_id == current_user_id)))).scalar_one() > 0
    saved = (await session.execute(select(func.count()).select_from(SavedFeed).where(and_(SavedFeed.feed_id == feed.id, SavedFeed.user_id == current_user_id)))).scalar_one() > 0
    return {
        "id": feed.id,
        "authorId": author.id,
        "username": author.username,
        "displayName": author.display_name,
        "profileImageUrl": author.profile_image_url,
        "videoUrl": feed.video_url,
        "thumbnailUrl": feed.thumbnail_url,
        "shortformUrl": feed.shortform_url,
        "exerciseType": feed.exercise_type,
        "repCount": feed.rep_count,
        "score": feed.score,
        "summaryFeedback": feed.summary_feedback,
        "caption": feed.caption,
        "hashtags": feed.hashtags or [],
        "likeCount": feed.like_count,
        "commentCount": feed.comment_count,
        "saveCount": feed.save_count,
        "liked": liked,
        "saved": saved,
        "isMine": feed.author_id == current_user_id,
        "createdAt": iso(feed.created_at),
    }
