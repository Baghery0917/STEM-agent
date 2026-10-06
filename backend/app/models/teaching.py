import enum
from datetime import datetime

from sqlalchemy import (
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


class TeachingSessionStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PipelineStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class SessionEndReason(str, enum.Enum):
    USER = "user"
    IDLE = "idle"


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(str, enum.Enum):
    QUESTION_SUBMIT = "question_submit"
    LLM_ANALYSIS = "llm_analysis"
    STUDENT_DATA = "student_data"
    STRATEGY = "strategy"
    REFERENCE_SEARCH = "reference_search"
    CHAT = "chat"


class TeachingSession(BaseModel):
    __tablename__ = "teaching_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False,
    )
    status: Mapped[TeachingSessionStatus] = mapped_column(
        Enum(TeachingSessionStatus), nullable=False, default=TeachingSessionStatus.ACTIVE,
    )
    pipeline_status: Mapped[PipelineStatus] = mapped_column(
        Enum(PipelineStatus), nullable=False, default=PipelineStatus.PENDING,
    )
    strategy: Mapped[str | None] = mapped_column(Text, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    end_reason: Mapped[SessionEndReason | None] = mapped_column(
        Enum(SessionEndReason), nullable=True,
    )

    messages: Mapped[list["TeachingMessage"]] = relationship(
        "TeachingMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="TeachingMessage.sequence",
    )


class TeachingMessage(BaseModel):
    __tablename__ = "teaching_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("teaching_sessions.id", ondelete="CASCADE"), nullable=False,
    )
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[MessageType] = mapped_column(Enum(MessageType), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # 即时情绪，仅 user 消息有值；1=自信 … 5=非常受挫
    facial_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    text_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    emotion_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    session: Mapped["TeachingSession"] = relationship(
        "TeachingSession", back_populates="messages",
    )
    references: Mapped[list["TeachingReference"]] = relationship(
        "TeachingReference",
        back_populates="message",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("session_id", "sequence", name="uq_session_sequence"),
    )


class TeachingReference(BaseModel):
    __tablename__ = "teaching_references"

    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int] = mapped_column(
        ForeignKey("teaching_messages.id", ondelete="CASCADE"), nullable=False,
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), nullable=False,
    )
    similarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    message: Mapped["TeachingMessage"] = relationship(
        "TeachingMessage", back_populates="references",
    )
