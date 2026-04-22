from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.base import BaseSchema, TimestampSchema


class VolumeBase(BaseSchema):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    order: int = Field(default=0, ge=0)


class VolumeCreate(VolumeBase):
    pass


class VolumeUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    order: int | None = Field(None, ge=0)


class VolumeResponse(VolumeBase, TimestampSchema):
    id: int
