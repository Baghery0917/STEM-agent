from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Volume(BaseModel):
    __tablename__ = "volumes"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order: Mapped[int] = mapped_column(default=0)

    chapters: Mapped[list["Chapter"]] = relationship("Chapter", back_populates="volume", cascade="all, delete-orphan")


from app.models.chapter import Chapter  # noqa: E402
