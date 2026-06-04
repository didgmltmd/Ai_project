from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserSetting(Base):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    comment_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    message_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    public_profile: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_play_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    muted_by_default: Mapped[bool] = mapped_column(Boolean, default=True)
    save_original_video: Mapped[bool] = mapped_column(Boolean, default=False)
    show_ai_feedback: Mapped[bool] = mapped_column(Boolean, default=True)
    post_after_analysis: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
