from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.setting import UserSetting
from app.repositories.helpers import ensure_user, iso


async def get_settings(session: AsyncSession, user_id: int) -> dict[str, Any]:
    user = await ensure_user(session, user_id)
    setting = (await session.execute(select(UserSetting).where(UserSetting.user_id == user.id))).scalar_one_or_none()
    if not setting:
        setting = UserSetting(user_id=user.id)
        session.add(setting)
        await session.commit()
        await session.refresh(setting)
    return setting_to_dict(setting)


async def update_settings(session: AsyncSession, user_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    await ensure_user(session, user_id)
    setting = (await session.execute(select(UserSetting).where(UserSetting.user_id == user_id))).scalar_one_or_none()
    if not setting:
        setting = UserSetting(user_id=user_id)
        session.add(setting)
    fields = {
        "pushEnabled": "push_enabled",
        "commentEnabled": "comment_enabled",
        "messageEnabled": "message_enabled",
        "publicProfile": "public_profile",
        "autoPlayEnabled": "auto_play_enabled",
        "mutedByDefault": "muted_by_default",
        "saveOriginalVideo": "save_original_video",
        "showAiFeedback": "show_ai_feedback",
        "postAfterAnalysis": "post_after_analysis",
    }
    for key, attr in fields.items():
        if key in payload and payload[key] is not None:
            setattr(setting, attr, bool(payload[key]))
    await session.commit()
    await session.refresh(setting)
    return setting_to_dict(setting)


def setting_to_dict(setting: UserSetting) -> dict[str, Any]:
    return {
        "userId": setting.user_id,
        "pushEnabled": setting.push_enabled,
        "commentEnabled": setting.comment_enabled,
        "messageEnabled": setting.message_enabled,
        "publicProfile": setting.public_profile,
        "autoPlayEnabled": setting.auto_play_enabled,
        "mutedByDefault": setting.muted_by_default,
        "saveOriginalVideo": setting.save_original_video,
        "showAiFeedback": setting.show_ai_feedback,
        "postAfterAnalysis": setting.post_after_analysis,
        "updatedAt": iso(setting.updated_at),
    }
