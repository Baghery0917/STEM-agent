from typing import Annotated

from pydantic import BaseModel, Field

from app.models.student import ExplainStyle, Gender, Persona
from app.schemas.base import BaseSchema, TimestampSchema


# 只接受 M/L/Q 命令和数字，避免把任意文本当路径存进来
SignaturePath = Annotated[str, Field(min_length=3, max_length=20000, pattern=r"^[MLQ0-9.\s-]+$")]


class StudentBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    gender: Gender


class StudentCreate(StudentBase):
    signature: SignaturePath | None = None


class StudentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    gender: Gender | None = None
    explain_style: ExplainStyle | None = None
    persona: Persona | None = None
    signature: SignaturePath | None = None


class StudentResponse(StudentBase, TimestampSchema):
    id: int
    explain_style: ExplainStyle | None = None
    persona: Persona | None = None
    signature: str | None = None
