import enum

from sqlalchemy import (
    String,
    Text,
    Integer,
    ForeignKey,
    Enum,
    Index,
    Table,
    Column,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.database import Base
from app.models.base import BaseModel


class QuestionType(str, enum.Enum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_BLANK = "fill_blank"
    SHORT_ANSWER = "short_answer"
    CALCULATION = "calculation"


class Difficulty(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


question_knowledge_point = Table(
    "question_knowledge_points",
    Base.metadata,
    Column("question_id", Integer, ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True),
    Column("section_id", Integer, ForeignKey("sections.id", ondelete="CASCADE"), primary_key=True),
)


class Question(BaseModel):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[QuestionType] = mapped_column(Enum(QuestionType), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    answer_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1024), nullable=True)
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty), nullable=False, default=Difficulty.MEDIUM)

    knowledge_points: Mapped[list["Section"]] = relationship(
        "Section",
        secondary=question_knowledge_point,
        back_populates="questions",
    )

    @property
    def knowledge_point_ids(self) -> list[int]:
        return [kp.id for kp in self.knowledge_points]

    __table_args__ = (
        Index("ix_questions_type", "type"),
        Index("ix_questions_difficulty", "difficulty"),
    )


from app.models.section import Section  # noqa: E402