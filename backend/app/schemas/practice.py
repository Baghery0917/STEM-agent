from datetime import datetime

from pydantic import BaseModel, Field

from app.models.practice import PracticeMode
from app.models.question import Difficulty
from app.schemas.base import BaseSchema, TimestampSchema
from app.schemas.question import QuestionPublicResponse, QuestionResponse


class PracticeSessionBase(BaseSchema):
    mode: PracticeMode
    knowledge_point_ids: list[int]
    difficulty_range: list[Difficulty]
    student_id: int
    total_count: int


class PracticeSessionCreate(BaseModel):
    student_id: int = Field(..., ge=1)
    knowledge_point_ids: list[int] = Field(..., min_length=1)
    difficulty_range: list[Difficulty] = Field(..., min_length=1)
    total_count: int = Field(0, ge=0)


class PracticeSessionUpdate(BaseModel):
    ended_at: datetime | None = None
    skip_count: int | None = None
    correct_count: int | None = None
    wrong_count: int | None = None
    total_count: int | None = None
    skipped_question_ids: list[int] | None = None


class PracticeSessionResponse(PracticeSessionBase, TimestampSchema):
    id: int
    started_at: datetime
    ended_at: datetime | None
    skip_count: int
    correct_count: int
    wrong_count: int
    skipped_question_ids: list[int]


class PracticeItemBase(BaseSchema):
    practice_session_id: int
    question_id: int
    user_answer: str
    sequence: int
    is_correct: bool
    is_skipped: bool
    started_at: datetime
    ended_at: datetime | None
    emotion: str | None


class PracticeItemCreate(BaseModel):
    question_id: int = Field(..., ge=1)
    user_answer: str = Field(..., min_length=1)
    emotion: str | None = None


class PracticeItemResponse(PracticeItemBase, TimestampSchema):
    id: int
    student_id: int


class PracticeItemWithQuestionResponse(PracticeItemResponse):
    question: QuestionResponse | None = None


# ---------------------------------------------------------------------------
# 请求/响应 schema（练习流程使用）
# ---------------------------------------------------------------------------

class StartFocusedRequest(BaseModel):
    student_id: int = Field(..., ge=1)
    knowledge_point_ids: list[int] = Field(..., min_length=1)
    difficulty_range: list[Difficulty] = Field(..., min_length=1)
    total_count: int = Field(..., ge=1, le=100)


class StartGeneralRequest(BaseModel):
    student_id: int = Field(..., ge=1)
    knowledge_point_ids: list[int] = Field(..., min_length=1)
    difficulty_range: list[Difficulty] = Field(..., min_length=1)


class SubmitAnswerRequest(BaseModel):
    question_id: int = Field(..., ge=1)
    user_answer: str = Field(..., min_length=1)
    emotion: str | None = None


class SkipQuestionRequest(BaseModel):
    question_id: int = Field(..., ge=1)


class StartSessionResponse(BaseModel):
    session: PracticeSessionResponse
    question: QuestionPublicResponse


class SubmitAnswerResponse(BaseModel):
    item: PracticeItemResponse
    is_correct: bool
    next_question: QuestionPublicResponse | None = None


class NextQuestionResponse(BaseModel):
    question: QuestionPublicResponse | None = None


class PracticeSessionDetailResponse(PracticeSessionResponse):
    items: list[PracticeItemWithQuestionResponse] = []
