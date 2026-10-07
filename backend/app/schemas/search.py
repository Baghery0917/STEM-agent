from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class SessionSearchHit(BaseModel):
    kind: Literal["teaching", "practice"]
    id: int
    title: str
    snippet: str
    at: datetime
    status: str


class SessionSearchResponse(BaseModel):
    q: str
    hits: list[SessionSearchHit]
