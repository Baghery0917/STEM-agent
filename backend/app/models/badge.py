from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class StudentLogin(BaseModel):
    """每次打开应用记一行；登录次数与连续天数都从这里算"""

    __tablename__ = "student_logins"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True,
    )


class StudentBadge(BaseModel):
    """物理学家徽章。badge_key 见 services/badges.py"""

    __tablename__ = "student_badges"
    __table_args__ = (
        UniqueConstraint("student_id", "badge_key", name="uq_student_badge"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    badge_key: Mapped[str] = mapped_column(String(30), nullable=False)
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
