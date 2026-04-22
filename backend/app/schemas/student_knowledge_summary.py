from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.base import BaseSchema, TimestampSchema


class StudentKnowledgeSummaryBase(BaseSchema):
    student_id: int
    section_id: int
    mastery_level: float = Field(..., ge=0.0, le=1.0)
    correct_count: int = Field(..., ge=0)
    total_practice_count: int = Field(..., ge=0)
    total_teaching_count: int = Field(..., ge=0)
    last_practice_at: datetime | None = None
    last_teaching_at: datetime | None = None


class StudentKnowledgeSummaryCreate(StudentKnowledgeSummaryBase):
    pass


class StudentKnowledgeSummaryUpdate(BaseModel):
    mastery_level: float | None = Field(None, ge=0.0, le=1.0)
    correct_count: int | None = Field(None, ge=0)
    total_practice_count: int | None = Field(None, ge=0)
    total_teaching_count: int | None = Field(None, ge=0)
    last_practice_at: datetime | None = None
    last_teaching_at: datetime | None = None


class StudentKnowledgeSummaryResponse(StudentKnowledgeSummaryBase, TimestampSchema):
    id: int
