from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chapter import Chapter
from app.schemas.chapter import ChapterCreate, ChapterUpdate


class ChapterService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: ChapterCreate) -> Chapter:
        chapter = Chapter(**data.model_dump())
        self.db.add(chapter)
        await self.db.flush()
        await self.db.refresh(chapter)
        return chapter

    async def get_by_id(self, chapter_id: int) -> Chapter | None:
        result = await self.db.execute(select(Chapter).where(Chapter.id == chapter_id))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Chapter]:
        result = await self.db.execute(select(Chapter).offset(skip).limit(limit).order_by(Chapter.order))
        return list(result.scalars().all())

    async def update(self, chapter_id: int, data: ChapterUpdate) -> Chapter | None:
        chapter = await self.get_by_id(chapter_id)
        if not chapter:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(chapter, key, value)
        await self.db.flush()
        await self.db.refresh(chapter)
        return chapter

    async def delete(self, chapter_id: int) -> bool:
        chapter = await self.get_by_id(chapter_id)
        if not chapter:
            return False
        await self.db.delete(chapter)
        return True

    async def get_sections(self, chapter_id: int) -> list["Section"]:
        from app.models.section import Section
        result = await self.db.execute(
            select(Section).where(Section.chapter_id == chapter_id).order_by(Section.order)
        )
        return list(result.scalars().all())


from app.models.section import Section  # noqa: E402
