import asyncio

from app.db.session import AsyncSessionLocal
from app.models.setting import UserSetting
from app.models.user import User
from app.repositories.auth_repository import hash_password


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        existing = await session.get(User, 1)
        if existing:
            print("Seed data already exists.")
            return

        me = User(
            id=1,
            username="me",
            email="me@pushform.local",
            password_hash=hash_password("pushform"),
            display_name="나",
            bio="AI 자세 분석으로 매일 푸시업을 기록 중",
            workout_intro="푸시업 자세를 꾸준히 개선하고 있습니다.",
            is_mock=False,
        )
        session.add(me)
        await session.flush()
        session.add(UserSetting(user_id=me.id))
        await session.commit()
        print("Seed user created without mock feed/message data.")


if __name__ == "__main__":
    asyncio.run(seed())
