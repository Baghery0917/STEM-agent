import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chapter import Chapter
from app.schemas.chapter import ChapterCreate, ChapterUpdate
from app.services.chapter import ChapterService
from app.services.volume import VolumeService


class TestChapterService:
    """Tests for ChapterService"""

    async def test_create_chapter(self, db_session: AsyncSession):
        """Golden path: create a chapter with valid data"""
        volume_service = VolumeService(db_session)
        volume = await volume_service.create(
            __import__("app.schemas.volume", fromlist=["VolumeCreate"]).VolumeCreate(title="Test Volume")
        )

        service = ChapterService(db_session)
        data = ChapterCreate(volume_id=volume.id, title="Test Chapter", description="A test chapter", order=1)
        chapter = await service.create(data)

        assert chapter.id is not None
        assert chapter.title == "Test Chapter"
        assert chapter.description == "A test chapter"
        assert chapter.volume_id == volume.id
        assert chapter.order == 1

    async def test_create_chapter_minimal(self, db_session: AsyncSession):
        """Edge case: create chapter with only required fields"""
        volume_service = VolumeService(db_session)
        volume = await volume_service.create(
            __import__("app.schemas.volume", fromlist=["VolumeCreate"]).VolumeCreate(title="Test Volume")
        )

        service = ChapterService(db_session)
        data = ChapterCreate(volume_id=volume.id, title="Minimal Chapter")
        chapter = await service.create(data)

        assert chapter.id is not None
        assert chapter.title == "Minimal Chapter"
        assert chapter.description is None
        assert chapter.order == 0  # default value

    async def test_create_chapter_max_title_length(self, db_session: AsyncSession):
        """Edge case: create chapter with max length title (255 chars)"""
        volume_service = VolumeService(db_session)
        volume = await volume_service.create(
            __import__("app.schemas.volume", fromlist=["VolumeCreate"]).VolumeCreate(title="Test Volume")
        )

        service = ChapterService(db_session)
        max_title = "a" * 255
        data = ChapterCreate(volume_id=volume.id, title=max_title)
        chapter = await service.create(data)

        assert chapter.title == max_title
        assert len(chapter.title) == 255

    async def test_get_by_id_existing(self, db_session: AsyncSession):
        """Golden path: get existing chapter by id"""
        volume_service = VolumeService(db_session)
        volume = await volume_service.create(
            __import__("app.schemas.volume", fromlist=["VolumeCreate"]).VolumeCreate(title="Test Volume")
        )

        service = ChapterService(db_session)
        created = await service.create(ChapterCreate(volume_id=volume.id, title="Get Test"))
        found = await service.get_by_id(created.id)

        assert found is not None
        assert found.id == created.id
        assert found.title == "Get Test"

    async def test_get_by_id_not_found(self, db_session: AsyncSession):
        """Error case: get non-existent chapter"""
        service = ChapterService(db_session)
        found = await service.get_by_id(99999)

        assert found is None

    async def test_get_all_empty(self, db_session: AsyncSession):
        """Edge case: get all chapters when none exist"""
        service = ChapterService(db_session)
        chapters = await service.get_all()

        assert chapters == []

    async def test_get_all_multiple(self, db_session: AsyncSession):
        """Golden path: get all chapters with multiple items"""
        volume_service = VolumeService(db_session)
        volume = await volume_service.create(
            __import__("app.schemas.volume", fromlist=["VolumeCreate"]).VolumeCreate(title="Test Volume")
        )

        service = ChapterService(db_session)
        await service.create(ChapterCreate(volume_id=volume.id, title="Chapter 1", order=1))
        await service.create(ChapterCreate(volume_id=volume.id, title="Chapter 2", order=2))
        await service.create(ChapterCreate(volume_id=volume.id, title="Chapter 3", order=3))

        chapters = await service.get_all()

        assert len(chapters) == 3
        assert chapters[0].title == "Chapter 1"
        assert chapters[1].title == "Chapter 2"
        assert chapters[2].title == "Chapter 3"

    async def test_get_all_with_pagination(self, db_session: AsyncSession):
        """Edge case: get all with pagination"""
        volume_service = VolumeService(db_session)
        volume = await volume_service.create(
            __import__("app.schemas.volume", fromlist=["VolumeCreate"]).VolumeCreate(title="Test Volume")
        )

        service = ChapterService(db_session)
        for i in range(5):
            await service.create(ChapterCreate(volume_id=volume.id, title=f"Chapter {i}", order=i))

        # Test limit
        chapters = await service.get_all(skip=0, limit=2)
        assert len(chapters) == 2

        # Test skip
        chapters = await service.get_all(skip=2, limit=10)
        assert len(chapters) == 3

    async def test_update_chapter(self, db_session: AsyncSession):
        """Golden path: update existing chapter"""
        volume_service = VolumeService(db_session)
        volume = await volume_service.create(
            __import__("app.schemas.volume", fromlist=["VolumeCreate"]).VolumeCreate(title="Test Volume")
        )

        service = ChapterService(db_session)
        created = await service.create(ChapterCreate(volume_id=volume.id, title="Original"))
        updated = await service.update(created.id, ChapterUpdate(title="Updated", description="New desc"))

        assert updated is not None
        assert updated.title == "Updated"
        assert updated.description == "New desc"

    async def test_update_chapter_partial(self, db_session: AsyncSession):
        """Edge case: partial update (only some fields)"""
        volume_service = VolumeService(db_session)
        volume = await volume_service.create(
            __import__("app.schemas.volume", fromlist=["VolumeCreate"]).VolumeCreate(title="Test Volume")
        )

        service = ChapterService(db_session)
        created = await service.create(
            ChapterCreate(volume_id=volume.id, title="Original", description="Original desc", order=5)
        )
        updated = await service.update(created.id, ChapterUpdate(title="New Title Only"))

        assert updated.title == "New Title Only"
        assert updated.description == "Original desc"  # unchanged
        assert updated.order == 5  # unchanged

    async def test_update_chapter_not_found(self, db_session: AsyncSession):
        """Error case: update non-existent chapter"""
        service = ChapterService(db_session)
        result = await service.update(99999, ChapterUpdate(title="Should fail"))

        assert result is None

    async def test_delete_chapter(self, db_session: AsyncSession):
        """Golden path: delete existing chapter"""
        volume_service = VolumeService(db_session)
        volume = await volume_service.create(
            __import__("app.schemas.volume", fromlist=["VolumeCreate"]).VolumeCreate(title="Test Volume")
        )

        service = ChapterService(db_session)
        created = await service.create(ChapterCreate(volume_id=volume.id, title="To Delete"))
        result = await service.delete(created.id)

        assert result is True
        # Verify it's gone
        found = await service.get_by_id(created.id)
        assert found is None

    async def test_delete_chapter_not_found(self, db_session: AsyncSession):
        """Error case: delete non-existent chapter"""
        service = ChapterService(db_session)
        result = await service.delete(99999)

        assert result is False

    async def test_get_sections_empty(self, db_session: AsyncSession):
        """Edge case: get sections for chapter with no sections"""
        volume_service = VolumeService(db_session)
        volume = await volume_service.create(
            __import__("app.schemas.volume", fromlist=["VolumeCreate"]).VolumeCreate(title="Test Volume")
        )

        service = ChapterService(db_session)
        created = await service.create(ChapterCreate(volume_id=volume.id, title="Chapter with no sections"))
        sections = await service.get_sections(created.id)

        assert sections == []

    async def test_get_sections_with_data(self, db_session: AsyncSession):
        """Golden path: get sections for chapter with sections"""
        volume_service = VolumeService(db_session)
        volume = await volume_service.create(
            __import__("app.schemas.volume", fromlist=["VolumeCreate"]).VolumeCreate(title="Test Volume")
        )

        chapter_service = ChapterService(db_session)
        chapter = await chapter_service.create(ChapterCreate(volume_id=volume.id, title="Test Chapter"))

        # Create sections directly in DB to test get_sections
        from app.models.section import Section
        section1 = Section(chapter_id=chapter.id, title="Section 1", order=1)
        section2 = Section(chapter_id=chapter.id, title="Section 2", order=2)
        db_session.add(section1)
        db_session.add(section2)
        await db_session.flush()

        sections = await chapter_service.get_sections(chapter.id)

        assert len(sections) == 2
        assert sections[0].title == "Section 1"
        assert sections[1].title == "Section 2"

    async def test_cascade_delete_with_volume(self, db_session: AsyncSession):
        """Verify chapters are deleted when parent volume is deleted"""
        volume_service = VolumeService(db_session)
        volume = await volume_service.create(
            __import__("app.schemas.volume", fromlist=["VolumeCreate"]).VolumeCreate(title="Test Volume")
        )

        chapter_service = ChapterService(db_session)
        chapter = await chapter_service.create(ChapterCreate(volume_id=volume.id, title="Test Chapter"))

        # Delete volume (should cascade delete chapter)
        await volume_service.delete(volume.id)

        # Chapter should be gone
        found = await chapter_service.get_by_id(chapter.id)
        assert found is None
