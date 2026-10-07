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
