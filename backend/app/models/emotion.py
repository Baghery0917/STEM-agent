import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class EmotionMode(str, enum.Enum):
    TEACHING = "teaching"
    PRACTICE = "practice"


class StudentKpEmotion(BaseModel):
    """学生对某知识点的历史总体情绪，会话结束后以指数平滑回流更新"""

    __tablename__ = "student_kp_emotions"
    __table_args__ = (
        UniqueConstraint("student_id", "section_id", name="uq_student_kp_emotion"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False,
    )
    section_id: Mapped[int] = mapped_column(
        ForeignKey("sections.id", ondelete="CASCADE"), nullable=False,
    )
    emotion_value: Mapped[float] = mapped_column(Float, nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class EmotionLog(BaseModel):
    """情绪图谱流水：教学模式一个 session 一行（按知识点拆分），练习模式一题一行"""

    __tablename__ = "emotion_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False,
    )
    section_id: Mapped[int] = mapped_column(
        ForeignKey("sections.id", ondelete="CASCADE"), nullable=False,
    )
    mode: Mapped[EmotionMode] = mapped_column(Enum(EmotionMode), nullable=False)
    session_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    emotion_value: Mapped[float] = mapped_column(Float, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
