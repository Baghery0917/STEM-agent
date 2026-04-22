from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.base import BaseSchema, TimestampSchema


class ChapterBase(BaseSchema):
    volume_id: int
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    order: int = Field(default=0, ge=0)


class ChapterCreate(ChapterBase):
    pass


class ChapterUpdate(BaseModel):
    volume_id: int | None = None
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    order: int | None = Field(None, ge=0)


class ChapterResponse(ChapterBase, TimestampSchema):
    id: int
