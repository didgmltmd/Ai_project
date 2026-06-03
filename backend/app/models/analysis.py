from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    feed_id: Mapped[int | None] = mapped_column(ForeignKey("feeds.id", ondelete="SET NULL"))
    exercise: Mapped[str] = mapped_column(String(40), default="pushup")
    rep_count: Mapped[int] = mapped_column(Integer, default=0)
    total_score: Mapped[int] = mapped_column(Integer, default=0)
    depth_score: Mapped[int] = mapped_column(Integer, default=0)
    alignment_score: Mapped[int] = mapped_column(Integer, default=0)
    consistency_score: Mapped[int] = mapped_column(Integer, default=0)
    stability_score: Mapped[int] = mapped_column(Integer, default=0)
    issues: Mapped[list[dict]] = mapped_column(JSON, default=list)
    feedback: Mapped[dict] = mapped_column(JSON, default=dict)
    original_video_url: Mapped[str | None] = mapped_column(Text)
    shortform_url: Mapped[str | None] = mapped_column(Text)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
