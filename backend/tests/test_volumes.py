import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.volume import VolumeCreate, VolumeUpdate
from app.services.volume import VolumeService


class TestVolumeService:
    """Tests for VolumeService"""

    async def test_create_volume(self, db_session: AsyncSession):
        """Golden path: create a volume with valid data"""
        service = VolumeService(db_session)
        data = VolumeCreate(title="Test Volume", description="A test volume", order=1)
        volume = await service.create(data)

        assert volume.id is not None
        assert volume.title == "Test Volume"
        assert volume.description == "A test volume"
        assert volume.order == 1

    async def test_create_volume_minimal(self, db_session: AsyncSession):
        """Edge case: create volume with only required fields"""
        service = VolumeService(db_session)
        data = VolumeCreate(title="Minimal Volume")
        volume = await service.create(data)

        assert volume.id is not None
        assert volume.title == "Minimal Volume"
        assert volume.description is None
        assert volume.order == 0  # default value

    async def test_create_volume_max_title_length(self, db_session: AsyncSession):
        """Edge case: create volume with max length title (255 chars)"""
        service = VolumeService(db_session)
        max_title = "a" * 255
        data = VolumeCreate(title=max_title)
        volume = await service.create(data)

        assert volume.title == max_title
        assert len(volume.title) == 255

    async def test_get_by_id_existing(self, db_session: AsyncSession):
        """Golden path: get existing volume by id"""
        service = VolumeService(db_session)
        created = await service.create(VolumeCreate(title="Get Test"))
        found = await service.get_by_id(created.id)

        assert found is not None
        assert found.id == created.id
        assert found.title == "Get Test"

    async def test_get_by_id_not_found(self, db_session: AsyncSession):
        """Error case: get non-existent volume"""
        service = VolumeService(db_session)
        found = await service.get_by_id(99999)

        assert found is None

    async def test_get_all_empty(self, db_session: AsyncSession):
        """Edge case: get all volumes when none exist"""
        service = VolumeService(db_session)
        volumes = await service.get_all()

        assert volumes == []

    async def test_get_all_multiple(self, db_session: AsyncSession):
        """Golden path: get all volumes with multiple items"""
        service = VolumeService(db_session)
        await service.create(VolumeCreate(title="Volume 1", order=1))
        await service.create(VolumeCreate(title="Volume 2", order=2))
        await service.create(VolumeCreate(title="Volume 3", order=3))

        volumes = await service.get_all()

        assert len(volumes) == 3
        # ordered by order field
        assert volumes[0].title == "Volume 1"
        assert volumes[1].title == "Volume 2"
        assert volumes[2].title == "Volume 3"

    async def test_get_all_with_pagination(self, db_session: AsyncSession):
        """Edge case: get all with pagination"""
        service = VolumeService(db_session)
        for i in range(5):
            await service.create(VolumeCreate(title=f"Volume {i}", order=i))

        # Test limit
        volumes = await service.get_all(skip=0, limit=2)
        assert len(volumes) == 2

        # Test skip
        volumes = await service.get_all(skip=2, limit=10)
        assert len(volumes) == 3

    async def test_update_volume(self, db_session: AsyncSession):
        """Golden path: update existing volume"""
        service = VolumeService(db_session)
        created = await service.create(VolumeCreate(title="Original"))
        updated = await service.update(created.id, VolumeUpdate(title="Updated", description="New desc"))

        assert updated is not None
        assert updated.title == "Updated"
        assert updated.description == "New desc"

    async def test_update_volume_partial(self, db_session: AsyncSession):
        """Edge case: partial update (only some fields)"""
        service = VolumeService(db_session)
        created = await service.create(VolumeCreate(title="Original", description="Original desc", order=5))
        updated = await service.update(created.id, VolumeUpdate(title="New Title Only"))

        assert updated.title == "New Title Only"
        assert updated.description == "Original desc"  # unchanged
        assert updated.order == 5  # unchanged

    async def test_update_volume_not_found(self, db_session: AsyncSession):
        """Error case: update non-existent volume"""
        service = VolumeService(db_session)
        result = await service.update(99999, VolumeUpdate(title="Should fail"))

        assert result is None

    async def test_delete_volume(self, db_session: AsyncSession):
        """Golden path: delete existing volume"""
        service = VolumeService(db_session)
        created = await service.create(VolumeCreate(title="To Delete"))
        result = await service.delete(created.id)

        assert result is True
        # Verify it's gone
        found = await service.get_by_id(created.id)
        assert found is None

    async def test_delete_volume_not_found(self, db_session: AsyncSession):
        """Error case: delete non-existent volume"""
        service = VolumeService(db_session)
        result = await service.delete(99999)

        assert result is False

    async def test_get_chapters_empty(self, db_session: AsyncSession):
        """Edge case: get chapters for volume with no chapters"""
        service = VolumeService(db_session)
        created = await service.create(VolumeCreate(title="Volume with no chapters"))
        chapters = await service.get_chapters(created.id)

        assert chapters == []

    async def test_get_chapters_with_data(self, db_session: AsyncSession):
        """Golden path: get chapters for volume with chapters"""
        from app.schemas.chapter import ChapterCreate

        volume_service = VolumeService(db_session)
        chapter_service = db_session  # Will use service directly

        # Create volume
        volume = await volume_service.create(VolumeCreate(title="Test Volume"))

        # Create chapters directly in DB to test get_chapters
        from app.models.chapter import Chapter
        chapter1 = Chapter(volume_id=volume.id, title="Chapter 1", order=1)
        chapter2 = Chapter(volume_id=volume.id, title="Chapter 2", order=2)
        db_session.add(chapter1)
        db_session.add(chapter2)
        await db_session.flush()

        chapters = await volume_service.get_chapters(volume.id)

        assert len(chapters) == 2
        assert chapters[0].title == "Chapter 1"
        assert chapters[1].title == "Chapter 2"
