from datetime import datetime

from pydantic import BaseModel, Field

from app.models.teaching import MessageRole, MessageType, PipelineStatus, TeachingSessionStatus
from app.schemas.base import BaseSchema, TimestampSchema


class TeachingSessionBase(BaseSchema):
    student_id: int
    status: TeachingSessionStatus = TeachingSessionStatus.ACTIVE
    pipeline_status: PipelineStatus = PipelineStatus.PENDING
    strategy: str | None = None
    ended_at: datetime | None = None


class TeachingSessionCreate(TeachingSessionBase):
    pass


class TeachingSessionUpdate(BaseModel):
    status: TeachingSessionStatus | None = None
    strategy: str | None = None
    ended_at: datetime | None = None


class TeachingSessionResponse(TeachingSessionBase, TimestampSchema):
    id: int


class TeachingSessionSummaryResponse(TeachingSessionResponse):
    preview: str | None = None
    message_count: int = 0


class TeachingMessageBase(BaseSchema):
    session_id: int
    role: MessageRole
    content: str
    message_type: MessageType
    sequence: int = Field(..., ge=0)


class TeachingMessageCreate(TeachingMessageBase):
    pass


class TeachingMessageUpdate(BaseModel):
    content: str | None = None


class TeachingMessageResponse(TeachingMessageBase, TimestampSchema):
    id: int


class TeachingReferenceBase(BaseSchema):
    message_id: int
    question_id: int
    similarity_score: float | None = Field(None, ge=0.0, le=1.0)


class TeachingReferenceCreate(TeachingReferenceBase):
    pass


class TeachingReferenceResponse(TeachingReferenceBase, TimestampSchema):
    id: int


# ---------------------------------------------------------------------------
# 请求/响应 schema（教学流程使用）
# ---------------------------------------------------------------------------

class SubmitQuestionRequest(BaseModel):
    student_id: int = Field(..., ge=1)
    question_content: str = Field(..., min_length=1)
    question_image: str | None = None


class ChatRequest(BaseModel):
    session_id: int = Field(..., ge=1)
    message: str = Field(..., min_length=1)


class EndSessionRequest(BaseModel):
    session_id: int = Field(..., ge=1)
    mastery_level_delta: float | None = Field(None, ge=-1.0, le=1.0)


class TeachingReferenceDetailResponse(TeachingReferenceResponse):
    pass


class TeachingMessageDetailResponse(TeachingMessageResponse):
    references: list[TeachingReferenceDetailResponse] = []


class TeachingSessionDetailResponse(TeachingSessionResponse):
    messages: list[TeachingMessageDetailResponse] = []


class TeachingChatResponse(BaseModel):
    session_id: int
    assistant_message: TeachingMessageResponse
