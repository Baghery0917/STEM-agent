from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.section import Section
from app.schemas.section import SectionCreate, SectionUpdate


class SectionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: SectionCreate) -> Section:
        section = Section(**data.model_dump())
        self.db.add(section)
        await self.db.flush()
        await self.db.refresh(section)
        return section

    async def get_by_id(self, section_id: int) -> Section | None:
        result = await self.db.execute(select(Section).where(Section.id == section_id))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Section]:
        result = await self.db.execute(select(Section).offset(skip).limit(limit).order_by(Section.order))
        return list(result.scalars().all())

    async def update(self, section_id: int, data: SectionUpdate) -> Section | None:
        section = await self.get_by_id(section_id)
        if not section:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(section, key, value)
        await self.db.flush()
        await self.db.refresh(section)
        return section

    async def delete(self, section_id: int) -> bool:
        section = await self.get_by_id(section_id)
        if not section:
            return False
        await self.db.delete(section)
        return True
