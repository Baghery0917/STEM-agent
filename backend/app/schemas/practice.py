from datetime import datetime

from pydantic import BaseModel, Field

from app.models.question import Difficulty, QuestionType
from app.schemas.base import BaseSchema, TimestampSchema
from app.schemas.question import QuestionPublicResponse, QuestionResponse


class PracticeSessionBase(BaseSchema):
    timed: bool
    instant_feedback: bool
    knowledge_point_ids: list[int]
    difficulty_range: list[Difficulty]
    student_id: int
    total_count: int


class PracticeSessionResponse(PracticeSessionBase, TimestampSchema):
    id: int
    question_ids: list[int]
    starred_question_ids: list[int]
    started_at: datetime
    ended_at: datetime | None
    skip_count: int
    correct_count: int
    wrong_count: int


class PracticeItemBase(BaseSchema):
    practice_session_id: int
    question_id: int
    user_answer: str
    sequence: int
    is_correct: bool
    is_skipped: bool
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int | None = None
    emotion: str | None = None
    emotion_value: float | None = None


class PracticeItemResponse(PracticeItemBase, TimestampSchema):
    id: int
    student_id: int


class PracticeItemWithQuestionResponse(PracticeItemResponse):
    question: QuestionResponse | None = None


# ---------------------------------------------------------------------------
# 请求/响应 schema（练习流程使用）
# ---------------------------------------------------------------------------

class StartPracticeRequest(BaseModel):
    student_id: int = Field(..., ge=1)
    knowledge_point_ids: list[int] = Field(..., min_length=1)
    difficulty_range: list[Difficulty] = Field(..., min_length=1)
    question_types: list[QuestionType] | None = None
    total_count: int = Field(10, ge=1, le=100)
    timed: bool = False
    # 计时模式下忽略此项并强制为 False
    instant_feedback: bool = True


class PracticeMatchRequest(BaseModel):
    """开始前预估：按范围能抽到多少题"""

    knowledge_point_ids: list[int] = Field(..., min_length=1)
    difficulty_range: list[Difficulty] = Field(..., min_length=1)
    question_types: list[QuestionType] | None = None


class PracticeMatchResponse(BaseModel):
    matched_count: int


class SubmitAnswerRequest(BaseModel):
    question_id: int = Field(..., ge=1)
    user_answer: str = Field(..., min_length=1)
    duration_seconds: int | None = Field(None, ge=0)
    # 提交瞬间的摄像头单帧，只转发给面部识别，不落库
    frame_base64: str | None = Field(None, max_length=2_000_000)


class SkipQuestionRequest(BaseModel):
    question_id: int = Field(..., ge=1)
    duration_seconds: int | None = Field(None, ge=0)


class StarQuestionRequest(BaseModel):
    question_id: int = Field(..., ge=1)
    starred: bool = True


class StartSessionResponse(BaseModel):
    session: PracticeSessionResponse
    questions: list[QuestionPublicResponse]


class SubmitAnswerResponse(BaseModel):
    """提交结果。instant_feedback=False 时 is_correct / correct_answer / analysis 为空，做完统一看"""

    item: PracticeItemResponse
    is_correct: bool | None = None
    correct_answer: str | None = None
    analysis: str | None = None
    analysis_image: str | None = None
    session: PracticeSessionResponse


class SkipQuestionResponse(BaseModel):
    item: PracticeItemResponse
    session: PracticeSessionResponse


class PracticeSessionDetailResponse(PracticeSessionResponse):
    questions: list[QuestionPublicResponse] = []
    items: list[PracticeItemWithQuestionResponse] = []
