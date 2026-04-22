from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.base import BaseSchema, TimestampSchema


class SectionBase(BaseSchema):
    chapter_id: int
    title: str = Field(..., min_length=1, max_length=255)
    content: str | None = None
    order: int = Field(default=0, ge=0)


class SectionCreate(SectionBase):
    pass


class SectionUpdate(BaseModel):
    chapter_id: int | None = None
    title: str | None = Field(None, min_length=1, max_length=255)
    content: str | None = None
    order: int | None = Field(None, ge=0)


class SectionResponse(SectionBase, TimestampSchema):
    id: int
