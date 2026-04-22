from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Section(BaseModel):
    __tablename__ = "sections"

    id: Mapped[int] = mapped_column(primary_key=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    order: Mapped[int] = mapped_column(default=0)

    chapter: Mapped["Chapter"] = relationship("Chapter", back_populates="sections")
    questions: Mapped[list["Question"]] = relationship(
        "Question",
        secondary="question_knowledge_points",
        back_populates="knowledge_points",
    )


from app.models.chapter import Chapter  # noqa: E402
