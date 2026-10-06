from datetime import datetime

from pydantic import BaseModel, Field

from app.models.teaching import (
    MessageRole,
    MessageType,
    PipelineStatus,
    SessionEndReason,
    TeachingSessionStatus,
)
from app.schemas.base import BaseSchema, TimestampSchema


class TeachingSessionBase(BaseSchema):
    student_id: int
    status: TeachingSessionStatus = TeachingSessionStatus.ACTIVE
    pipeline_status: PipelineStatus = PipelineStatus.PENDING
    strategy: str | None = None
    ended_at: datetime | None = None
    end_reason: SessionEndReason | None = None
    # 从练习转来时的来源，前端据此渲染「来自练习第 N 题」卡片
    source_practice_session_id: int | None = None
    source_question_ids: list[int] | None = None


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
    facial_value: float | None = None
    text_value: float | None = None
    emotion_value: float | None = None
    self_rating: int | None = None


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

# frame_base64：发送瞬间的摄像头单帧 jpeg（data URL 或裸 base64），只转发给面部识别，不落库
class SubmitQuestionRequest(BaseModel):
    student_id: int = Field(..., ge=1)
    question_content: str = Field(..., min_length=1)
    question_image: str | None = None
    frame_base64: str | None = Field(None, max_length=2_000_000)
    # 从练习转来：后端会把题干、学生作答与正确答案拼进第一条消息
    source_practice_session_id: int | None = Field(None, ge=1)
    source_question_ids: list[int] | None = None


class RateMessageRequest(BaseModel):
    """学生对某条 AI 回复的掌握度自评；rating 为空表示取消"""

    session_id: int = Field(..., ge=1)
    message_id: int = Field(..., ge=1)
    rating: int | None = Field(None, ge=0, le=3)


class ChatRequest(BaseModel):
    session_id: int = Field(..., ge=1)
    message: str = Field(..., min_length=1)
    frame_base64: str | None = Field(None, max_length=2_000_000)


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
