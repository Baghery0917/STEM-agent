import enum

from sqlalchemy import (
    BigInteger,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class LLMCallType(str, enum.Enum):
    CHAT = "chat"
    VISION = "vision"
    EMBED = "embed"


class LLMCallStatus(str, enum.Enum):
    SUCCESS = "success"
    ERROR = "error"


class LLMCallLog(BaseModel):
    __tablename__ = "llm_call_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    call_type: Mapped[LLMCallType] = mapped_column(Enum(LLMCallType), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    base_url: Mapped[str] = mapped_column(String(512), nullable=False)

    request_payload: Mapped[dict | list] = mapped_column(JSONB, nullable=False)
    request_params: Mapped[dict] = mapped_column(JSONB, nullable=False)

    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    status: Mapped[LLMCallStatus] = mapped_column(Enum(LLMCallStatus), nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)

    teaching_session_id: Mapped[int | None] = mapped_column(
        ForeignKey("teaching_sessions.id", ondelete="SET NULL"), nullable=True,
    )
    student_id: Mapped[int | None] = mapped_column(
        ForeignKey("students.id", ondelete="SET NULL"), nullable=True,
    )

    __table_args__ = (
        Index("ix_llm_call_logs_call_type_created_at", "call_type", "created_at"),
        Index("ix_llm_call_logs_status_created_at", "status", "created_at"),
        Index("ix_llm_call_logs_teaching_session_id", "teaching_session_id"),
        Index("ix_llm_call_logs_student_id", "student_id"),
    )
