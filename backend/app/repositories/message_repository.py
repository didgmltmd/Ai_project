from typing import Any

from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.models.user import User
from app.repositories.helpers import ensure_user, iso


async def list_conversations(session: AsyncSession, user_id: int) -> list[dict[str, Any]]:
    user = await ensure_user(session, user_id)
    rows = (
        await session.execute(
            select(Message).where(or_(Message.sender_id == user.id, Message.receiver_id == user.id)).order_by(desc(Message.created_at))
        )
    ).scalars().all()
    seen: set[int] = set()
    conversations = []
    for message in rows:
        other_id = message.receiver_id if message.sender_id == user.id else message.sender_id
        if other_id in seen:
            continue
        other = await session.get(User, other_id)
        if other:
            conversations.append({"userId": other.id, "username": other.username, "displayName": other.display_name, "lastMessage": message.content, "createdAt": iso(message.created_at)})
            seen.add(other_id)
    return conversations


async def list_thread(session: AsyncSession, user_id: int, other_user_id: int) -> list[dict[str, Any]]:
    user = await ensure_user(session, user_id)
    await ensure_user(session, other_user_id)
    stmt = select(Message).where(
        or_(
            and_(Message.sender_id == user.id, Message.receiver_id == other_user_id),
            and_(Message.sender_id == other_user_id, Message.receiver_id == user.id),
        )
    ).order_by(Message.created_at)
    return [message_to_dict(message) for message in (await session.execute(stmt)).scalars().all()]


async def send_message(session: AsyncSession, sender_id: int, receiver_id: int, content: str) -> dict[str, Any]:
    if sender_id == receiver_id:
        raise ValueError("자기 자신에게는 메시지를 보낼 수 없습니다.")
    if not content.strip():
        raise ValueError("메시지 내용을 입력해 주세요.")
    sender = await ensure_user(session, sender_id)
    receiver = await ensure_user(session, receiver_id)
    message = Message(sender_id=sender.id, receiver_id=receiver.id, content=content.strip())
    session.add(message)
    await session.commit()
    await session.refresh(message)
    return message_to_dict(message)


def message_to_dict(message: Message) -> dict[str, Any]:
    return {"id": message.id, "senderId": message.sender_id, "receiverId": message.receiver_id, "content": message.content, "createdAt": iso(message.created_at)}
