from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.volume import Volume
from app.schemas.volume import VolumeCreate, VolumeUpdate


class VolumeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: VolumeCreate) -> Volume:
        volume = Volume(**data.model_dump())
        self.db.add(volume)
        await self.db.flush()
        await self.db.refresh(volume)
        return volume

    async def get_by_id(self, volume_id: int) -> Volume | None:
        result = await self.db.execute(select(Volume).where(Volume.id == volume_id))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Volume]:
        result = await self.db.execute(select(Volume).offset(skip).limit(limit).order_by(Volume.order))
        return list(result.scalars().all())

    async def update(self, volume_id: int, data: VolumeUpdate) -> Volume | None:
        volume = await self.get_by_id(volume_id)
        if not volume:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(volume, key, value)
        await self.db.flush()
        await self.db.refresh(volume)
        return volume

    async def delete(self, volume_id: int) -> bool:
        volume = await self.get_by_id(volume_id)
        if not volume:
            return False
        await self.db.delete(volume)
        return True

    async def get_chapters(self, volume_id: int) -> list["Chapter"]:
        from app.models.chapter import Chapter
        result = await self.db.execute(
            select(Chapter).where(Chapter.volume_id == volume_id).order_by(Chapter.order)
        )
        return list(result.scalars().all())


from app.models.chapter import Chapter  # noqa: E402
