from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.message import MessageCreateRequest
from app.services import message_service

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("")
async def get_conversations(userId: int, session: AsyncSession = Depends(get_db)):
    return await message_service.list_conversations(session, userId)


@router.get("/{other_user_id}")
async def get_thread(other_user_id: int, userId: int, session: AsyncSession = Depends(get_db)):
    return await message_service.list_thread(session, userId, other_user_id)


@router.post("", status_code=201)
async def create_message(payload: MessageCreateRequest, session: AsyncSession = Depends(get_db)):
    if payload.senderId == payload.receiverId:
        raise HTTPException(status_code=400, detail="자기 자신에게 메시지를 보낼 수 없습니다.")
    try:
        return await message_service.send_message(session, payload.senderId, payload.receiverId, payload.content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
