from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.setting import SettingsUpdateRequest
from app.services import setting_service

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/{user_id}")
async def get_settings(user_id: int, session: AsyncSession = Depends(get_db)):
    return await setting_service.get_settings(session, user_id)


@router.patch("/{user_id}")
async def patch_settings(user_id: int, payload: SettingsUpdateRequest, session: AsyncSession = Depends(get_db)):
    return await setting_service.update_settings(session, user_id, payload.model_dump())
