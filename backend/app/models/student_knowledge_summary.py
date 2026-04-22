from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class StudentKnowledgeSummary(BaseModel):
    __tablename__ = "student_knowledge_summaries"

    __table_args__ = (
        UniqueConstraint("student_id", "section_id", name="uq_student_section"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False,
    )
    section_id: Mapped[int] = mapped_column(
        ForeignKey("sections.id", ondelete="CASCADE"), nullable=False,
    )
    mastery_level: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False,
    )
    correct_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
    )
    total_practice_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
    )
    total_teaching_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
    )
    last_practice_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    last_teaching_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
