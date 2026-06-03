from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SavedFeed(Base):
    __tablename__ = "saved_feeds"
    __table_args__ = (UniqueConstraint("feed_id", "user_id", name="uq_saved_feeds_feed_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    feed_id: Mapped[int] = mapped_column(ForeignKey("feeds.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
