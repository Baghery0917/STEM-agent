from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ScoreEvent(BaseModel):
    """认可值流水。按 (source_type, source_id) 唯一，钩子重复触发不会重复计分。"""

    __tablename__ = "score_events"
    __table_args__ = (
        UniqueConstraint("source_type", "source_id", name="uq_score_event_source"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    points: Mapped[float] = mapped_column(Float, nullable=False)


class StudentCard(BaseModel):
    """认可卡。card_key 与 Persona 值一致，Leonard 不需要卡。"""

    __tablename__ = "student_cards"
    __table_args__ = (
        UniqueConstraint("student_id", "card_key", name="uq_student_card"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    card_key: Mapped[str] = mapped_column(String(20), nullable=False)
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
