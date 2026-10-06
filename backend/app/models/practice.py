from datetime import datetime

from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.question import Difficulty


class PracticeSession(BaseModel):
    """一次练习。开始时按范围一次性抽满 question_ids，之后前端可在题目间自由前后切换。"""

    __tablename__ = "practice_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    # 是否计时：计时中不能中途转去提问，只能先星标；不计时随时可转
    timed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    knowledge_point_ids: Mapped[list[int]] = mapped_column(
        ARRAY(Integer), nullable=False,
    )
    difficulty_range: Mapped[list[Difficulty]] = mapped_column(
        ARRAY(Enum(Difficulty, name="difficulty", create_type=False)),
        nullable=False,
    )
    # 本次练习的全部题目，按出题顺序
    question_ids: Mapped[list[int]] = mapped_column(
        ARRAY(Integer), default=list, server_default="{}", nullable=False,
    )
    # 做题过程中星标的题，做完后可一键转教学会话
    starred_question_ids: Mapped[list[int]] = mapped_column(
        ARRAY(Integer), default=list, server_default="{}", nullable=False,
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

    items: Mapped[list["PracticeItem"]] = relationship(
        "PracticeItem",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="PracticeItem.sequence",
    )


class PracticeItem(BaseModel):
    """一题一行。跳过也写一行（is_skipped=True，不计入学生档案）。"""

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
    # 前端上报的本题用时（秒），不计时模式可为空
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    user_answer: Mapped[str] = mapped_column(Text, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    # 提交瞬间的面部情绪标签（1=自信 … 5=非常受挫 对应的中文），未配置识别服务则为空
    emotion: Mapped[str | None] = mapped_column(String(50), nullable=True)
    emotion_value: Mapped[float | None] = mapped_column(Float, nullable=True)

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
