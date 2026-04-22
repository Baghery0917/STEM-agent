from pydantic import BaseModel, Field

from app.models.question import QuestionType, Difficulty
from app.schemas.base import BaseSchema, TimestampSchema


class QuestionBase(BaseSchema):
    type: QuestionType
    content: str = Field(..., min_length=1)
    content_image: str | None = None
    answer: str = Field(..., min_length=1)
    answer_image: str | None = None
    analysis: str | None = None
    analysis_image: str | None = None
    difficulty: Difficulty = Difficulty.MEDIUM
    knowledge_point_ids: list[int] = Field(default_factory=list)


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(BaseModel):
    type: QuestionType | None = None
    content: str | None = Field(None, min_length=1)
    content_image: str | None = None
    answer: str | None = Field(None, min_length=1)
    answer_image: str | None = None
    analysis: str | None = None
    analysis_image: str | None = None
    difficulty: Difficulty | None = None
    knowledge_point_ids: list[int] | None = None


class QuestionResponse(QuestionBase, TimestampSchema):
    """管理端题目详情。包含 answer/analysis，不要直接返回给学生端。"""
    id: int


class QuestionPublicResponse(TimestampSchema):
    """学生端抽题使用。不含 answer/analysis 以防作弊。"""
    id: int
    type: QuestionType
    content: str
    content_image: str | None = None
    difficulty: Difficulty
    knowledge_point_ids: list[int] = Field(default_factory=list)
