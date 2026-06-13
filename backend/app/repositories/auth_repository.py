import base64
import hashlib
import hmac
import os
import time
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.setting import UserSetting
from app.models.user import User
from app.repositories.helpers import user_to_dict

ACCESS_TOKEN_TTL_SECONDS = 60 * 15
REFRESH_TOKEN_TTL_SECONDS = 60 * 60 * 24 * 30
TOKEN_SECRET = os.getenv("AUTH_TOKEN_SECRET", "pushform-dev-token-secret").encode("utf-8")


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
    if not normalized_email or not normalized_username or not password:
        raise ValueError("이메일, 닉네임, 비밀번호를 모두 입력하세요.")

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
        follower_count=0,
        following_count=0,
        post_count=0,
        is_mock=False,
    )
    session.add(user)
    await session.flush()
    session.add(
        UserSetting(
            user_id=user.id,
            push_enabled=True,
            comment_enabled=True,
            message_enabled=True,
            public_profile=True,
            auto_play_enabled=True,
            muted_by_default=True,
            save_original_video=False,
            show_ai_feedback=True,
            post_after_analysis=False,
        )
    )
    await session.commit()
    await session.refresh(user)
    return user_to_dict(user)


async def authenticate(session: AsyncSession, email: str, password: str) -> dict[str, Any] | None:
    normalized_email = email.strip().lower()
    user = (await session.execute(select(User).where(User.email == normalized_email))).scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user_to_dict(user)


async def get_user_by_id(session: AsyncSession, user_id: int) -> dict[str, Any] | None:
    user = await session.get(User, user_id)
    return user_to_dict(user) if user else None


def _sign(payload: str) -> str:
    signature = hmac.new(TOKEN_SECRET, payload.encode("utf-8"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")


def _encode_payload(user_id: int, token_type: str, ttl_seconds: int) -> str:
    expires_at = int(time.time()) + ttl_seconds
    payload = f"{user_id}:{token_type}:{expires_at}"
    encoded_payload = base64.urlsafe_b64encode(payload.encode("utf-8")).decode("utf-8").rstrip("=")
    return f"{encoded_payload}.{_sign(payload)}"


def create_token_pair(user_id: int) -> dict[str, Any]:
    return {
        "accessToken": _encode_payload(user_id, "access", ACCESS_TOKEN_TTL_SECONDS),
        "refreshToken": _encode_payload(user_id, "refresh", REFRESH_TOKEN_TTL_SECONDS),
        "tokenType": "Bearer",
        "expiresIn": ACCESS_TOKEN_TTL_SECONDS,
    }


def verify_token(token: str, expected_type: str) -> int | None:
    try:
        payload_b64, signature = token.split(".", 1)
        padded_payload = payload_b64 + "=" * (-len(payload_b64) % 4)
        payload = base64.urlsafe_b64decode(padded_payload.encode("utf-8")).decode("utf-8")
        user_id_text, token_type, expires_at_text = payload.split(":", 2)
        expires_at = int(expires_at_text)
    except (ValueError, UnicodeDecodeError):
        return None
    if not hmac.compare_digest(signature, _sign(payload)):
        return None
    if token_type != expected_type:
        return None
    if expires_at < int(time.time()):
        return None
    return int(user_id_text)
