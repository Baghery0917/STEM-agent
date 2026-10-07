from datetime import date

from pydantic import BaseModel, Field, HttpUrl

from app.schemas.base import TimestampSchema


class NewsBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    summary: str = Field(..., min_length=1)
    tag: str = Field(..., min_length=1, max_length=40)
    source: str = Field(..., min_length=1, max_length=120)
    url: HttpUrl
    published_on: date
    published: bool = True


class NewsCreate(NewsBase):
    pass


class NewsUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    summary: str | None = Field(None, min_length=1)
    tag: str | None = Field(None, min_length=1, max_length=40)
    source: str | None = Field(None, min_length=1, max_length=120)
    url: HttpUrl | None = None
    published_on: date | None = None
    published: bool | None = None


class NewsResponse(TimestampSchema):
    id: int
    title: str
    summary: str
    tag: str
    source: str
    url: str
    published_on: date
    published: bool

    model_config = {"from_attributes": True}
