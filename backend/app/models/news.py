from datetime import date

from sqlalchemy import Boolean, Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class NewsItem(BaseModel):
    """落地页「物理界的新闻」。管理台维护，公开接口只返回 published 的"""

    __tablename__ = "news_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    tag: Mapped[str] = mapped_column(String(40), nullable=False)
    source: Mapped[str] = mapped_column(String(120), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    published_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
