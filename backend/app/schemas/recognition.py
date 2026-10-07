from datetime import datetime

from pydantic import BaseModel

from app.models.student import Persona


class StudentCardResponse(BaseModel):
    card_key: Persona
    acquired_at: datetime

    model_config = {"from_attributes": True}


class StudentCardsResponse(BaseModel):
    cards: list[StudentCardResponse]
    unlocked: list[Persona]


class StudentBadgeResponse(BaseModel):
    badge_key: str
    acquired_at: datetime

    model_config = {"from_attributes": True}


class BadgeProgress(BaseModel):
    badge_key: str
    metric: str
    threshold: float
    value: float


class StudentCollectionResponse(StudentCardsResponse):
    """认可卡 + 徽章 + 各徽章进度，一次返回给收藏页"""

    badges: list[StudentBadgeResponse]
    badge_progress: list[BadgeProgress]


class CheckinResponse(BaseModel):
    login_count: int
    new_badges: list[StudentBadgeResponse]


class StudentBadgeResponse(BaseModel):
    badge_key: str
    acquired_at: datetime

    model_config = {"from_attributes": True}


class BadgeProgress(BaseModel):
    badge_key: str
    metric: str
    threshold: float
    value: float


class StudentCollectionResponse(StudentCardsResponse):
    """认可卡 + 徽章 + 各徽章进度，一次返回给收藏页"""

    badges: list[StudentBadgeResponse]
    badge_progress: list[BadgeProgress]


class CheckinResponse(BaseModel):
    login_count: int
    new_badges: list[StudentBadgeResponse]
