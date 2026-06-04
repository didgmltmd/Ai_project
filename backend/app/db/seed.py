import asyncio

from app.db.session import AsyncSessionLocal
from app.models.comment import Comment
from app.models.feed import Feed
from app.models.message import Message
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
            bio="오늘도 푸시업 자세를 기록합니다.",
            workout_intro="AI 자세 분석으로 매일 푸시업을 개선하고 있습니다.",
            is_mock=True,
        )
        coach = User(
            id=2,
            username="coach_ai",
            email="coach@pushform.local",
            display_name="AI 코치",
            bio="자세 피드백을 남기는 코치 계정입니다.",
            workout_intro="푸시업 자세를 데이터로 점검합니다.",
            is_mock=True,
        )
        runner = User(
            id=3,
            username="daily_push",
            email="daily@pushform.local",
            display_name="데일리 푸시업",
            bio="매일 한 세트씩 기록합니다.",
            workout_intro="작은 반복을 꾸준히 쌓고 있습니다.",
            is_mock=True,
        )
        session.add_all([me, coach, runner])
        await session.flush()

        feed = Feed(
            author_id=me.id,
            video_url="/media/shortforms/sample_pushup.mp4",
            shortform_url="/media/shortforms/sample_pushup.mp4",
            exercise_type="pushup",
            rep_count=12,
            score=86,
            summary_feedback="상체 정렬은 안정적이고 후반부 깊이를 조금 더 일정하게 유지하면 좋습니다.",
            caption="오늘 푸시업 12회 분석 결과",
            hashtags=["#푸시업", "#AI자세분석", "#운동기록"],
            is_mine=True,
        )
        session.add(feed)
        await session.flush()
        session.add_all(
            [
                Comment(feed_id=feed.id, user_id=coach.id, content="팔꿈치 각도가 좋아졌어요."),
                Message(sender_id=coach.id, receiver_id=me.id, content="오늘 분석 결과를 확인해보세요."),
                UserSetting(user_id=me.id),
            ]
        )
        me.post_count = 1
        feed.comment_count = 1
        await session.commit()
        print("Seed data created.")


if __name__ == "__main__":
    asyncio.run(seed())
