from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import NewsItem
from app.schemas.news import NewsCreate, NewsUpdate


class NewsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list(self, *, published_only: bool, limit: int) -> list[NewsItem]:
        stmt = select(NewsItem).order_by(NewsItem.published_on.desc(), NewsItem.id.desc()).limit(limit)
        if published_only:
            stmt = stmt.where(NewsItem.published.is_(True))
        return list((await self.db.execute(stmt)).scalars().all())

    async def get(self, news_id: int) -> NewsItem | None:
        return await self.db.get(NewsItem, news_id)

    async def create(self, data: NewsCreate) -> NewsItem:
        item = NewsItem(**{**data.model_dump(), "url": str(data.url)})
        self.db.add(item)
        await self.db.flush()
        return item

    async def update(self, news_id: int, data: NewsUpdate) -> NewsItem | None:
        item = await self.get(news_id)
        if not item:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(item, key, str(value) if key == "url" else value)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def delete(self, news_id: int) -> bool:
        item = await self.get(news_id)
        if not item:
            return False
        await self.db.delete(item)
        await self.db.flush()
        return True
