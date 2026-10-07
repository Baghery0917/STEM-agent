from pydantic import BaseModel, Field

from app.models.student import ExplainStyle, Gender
from app.schemas.base import BaseSchema, TimestampSchema


class StudentBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    gender: Gender


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    gender: Gender | None = None
    explain_style: ExplainStyle | None = None


class StudentResponse(StudentBase, TimestampSchema):
    id: int
    explain_style: ExplainStyle | None = None
