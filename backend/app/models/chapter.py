from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Chapter(BaseModel):
    __tablename__ = "chapters"

    id: Mapped[int] = mapped_column(primary_key=True)
    volume_id: Mapped[int] = mapped_column(ForeignKey("volumes.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order: Mapped[int] = mapped_column(default=0)

    volume: Mapped["Volume"] = relationship("Volume", back_populates="chapters")
    sections: Mapped[list["Section"]] = relationship("Section", back_populates="chapter", cascade="all, delete-orphan")


from app.models.section import Section  # noqa: E402
