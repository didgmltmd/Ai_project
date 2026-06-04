import base64
import hashlib
import hmac
import os
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.setting import UserSetting
from app.models.user import User
from app.repositories.helpers import user_to_dict


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return f"pbkdf2_sha256${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, stored_hash: str | None) -> bool:
    if not stored_hash:
        return False
    try:
        algorithm, salt_b64, digest_b64 = stored_hash.split("$", 2)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    salt = base64.b64decode(salt_b64)
    expected = base64.b64decode(digest_b64)
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return hmac.compare_digest(candidate, expected)


async def create_user(session: AsyncSession, username: str, email: str, password: str) -> dict[str, Any]:
    normalized_email = email.strip().lower()
    normalized_username = username.strip()
    existing = (
        await session.execute(
            select(User).where(or_(User.email == normalized_email, User.username == normalized_username))
        )
    ).scalar_one_or_none()
    if existing:
        raise ValueError("이미 사용 중인 이메일 또는 닉네임입니다.")

    user = User(
        username=normalized_username,
        email=normalized_email,
        password_hash=hash_password(password),
        display_name=normalized_username,
        bio="AI 자세 분석으로 매일 푸시업을 기록 중",
        workout_intro="푸시업 자세를 꾸준히 개선하고 있습니다.",
        is_mock=False,
    )
    session.add(user)
    await session.flush()
    session.add(UserSetting(user_id=user.id))
    await session.commit()
    await session.refresh(user)
    return user_to_dict(user)


async def authenticate(session: AsyncSession, email: str, password: str) -> dict[str, Any] | None:
    normalized_email = email.strip().lower()
    user = (await session.execute(select(User).where(User.email == normalized_email))).scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user_to_dict(user)


def make_mock_token(user_id: int) -> str:
    return f"mock-user-{user_id}"
