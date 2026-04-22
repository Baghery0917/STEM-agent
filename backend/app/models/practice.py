import enum
from datetime import datetime

from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.question import Difficulty


class PracticeMode(str, enum.Enum):
    FOCUSED = "focused"
    GENERAL = "general"


class PracticeSession(BaseModel):
    __tablename__ = "practice_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    mode: Mapped[PracticeMode] = mapped_column(Enum(PracticeMode), nullable=False)
    knowledge_point_ids: Mapped[list[int]] = mapped_column(
        ARRAY(Integer), nullable=False,
    )
    difficulty_range: Mapped[list[Difficulty]] = mapped_column(
        ARRAY(Enum(Difficulty, name="difficulty", create_type=False)),
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False,
    )
    skip_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    correct_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    wrong_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    total_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    skipped_question_ids: Mapped[list[int]] = mapped_column(
        ARRAY(Integer), default=list, server_default="{}", nullable=False,
    )

    items: Mapped[list["PracticeItem"]] = relationship(
        "PracticeItem",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="PracticeItem.sequence",
    )


class PracticeItem(BaseModel):
    __tablename__ = "practice_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False,
    )
    practice_session_id: Mapped[int] = mapped_column(
        ForeignKey("practice_sessions.id", ondelete="CASCADE"), nullable=False,
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), nullable=False,
    )
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_skipped: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    user_answer: Mapped[str] = mapped_column(Text, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    emotion: Mapped[str | None] = mapped_column(String(50), nullable=True)

    session: Mapped["PracticeSession"] = relationship(
        "PracticeSession", back_populates="items",
    )

    __table_args__ = (
        UniqueConstraint(
            "practice_session_id", "sequence",
            name="uq_practice_session_sequence",
        ),
        UniqueConstraint(
            "practice_session_id", "question_id",
            name="uq_practice_session_question",
        ),
    )
