import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.section import Section
from app.schemas.chapter import ChapterCreate
from app.schemas.section import SectionCreate, SectionUpdate
from app.schemas.volume import VolumeCreate
from app.services.chapter import ChapterService
from app.services.section import SectionService
from app.services.volume import VolumeService


async def create_test_volume(db_session: AsyncSession) -> VolumeCreate:
    """Helper to create a test volume"""
    volume_service = VolumeService(db_session)
    return await volume_service.create(VolumeCreate(title="Test Volume"))


async def create_test_chapter(db_session: AsyncSession, volume_id: int) -> ChapterCreate:
    """Helper to create a test chapter"""
    chapter_service = ChapterService(db_session)
    return await chapter_service.create(ChapterCreate(volume_id=volume_id, title="Test Chapter"))


class TestSectionService:
    """Tests for SectionService"""

    async def test_create_section(self, db_session: AsyncSession):
        """Golden path: create a section with valid data"""
        volume = await create_test_volume(db_session)
        chapter = await create_test_chapter(db_session, volume.id)

        service = SectionService(db_session)
        data = SectionCreate(chapter_id=chapter.id, title="Test Section", content="Test content", order=1)
        section = await service.create(data)

        assert section.id is not None
        assert section.title == "Test Section"
        assert section.content == "Test content"
        assert section.chapter_id == chapter.id
        assert section.order == 1

    async def test_create_section_minimal(self, db_session: AsyncSession):
        """Edge case: create section with only required fields"""
        volume = await create_test_volume(db_session)
        chapter = await create_test_chapter(db_session, volume.id)

        service = SectionService(db_session)
        data = SectionCreate(chapter_id=chapter.id, title="Minimal Section")
        section = await service.create(data)

        assert section.id is not None
        assert section.title == "Minimal Section"
        assert section.content is None
        assert section.order == 0  # default value

    async def test_create_section_max_title_length(self, db_session: AsyncSession):
        """Edge case: create section with max length title (255 chars)"""
        volume = await create_test_volume(db_session)
        chapter = await create_test_chapter(db_session, volume.id)

        service = SectionService(db_session)
        max_title = "a" * 255
        data = SectionCreate(chapter_id=chapter.id, title=max_title)
        section = await service.create(data)

        assert section.title == max_title
        assert len(section.title) == 255

    async def test_get_by_id_existing(self, db_session: AsyncSession):
        """Golden path: get existing section by id"""
        volume = await create_test_volume(db_session)
        chapter = await create_test_chapter(db_session, volume.id)

        service = SectionService(db_session)
        created = await service.create(SectionCreate(chapter_id=chapter.id, title="Get Test"))
        found = await service.get_by_id(created.id)

        assert found is not None
        assert found.id == created.id
        assert found.title == "Get Test"

    async def test_get_by_id_not_found(self, db_session: AsyncSession):
        """Error case: get non-existent section"""
        service = SectionService(db_session)
        found = await service.get_by_id(99999)

        assert found is None

    async def test_get_all_empty(self, db_session: AsyncSession):
        """Edge case: get all sections when none exist"""
        service = SectionService(db_session)
        sections = await service.get_all()

        assert sections == []

    async def test_get_all_multiple(self, db_session: AsyncSession):
        """Golden path: get all sections with multiple items"""
        volume = await create_test_volume(db_session)
        chapter = await create_test_chapter(db_session, volume.id)

        service = SectionService(db_session)
        await service.create(SectionCreate(chapter_id=chapter.id, title="Section 1", order=1))
        await service.create(SectionCreate(chapter_id=chapter.id, title="Section 2", order=2))
        await service.create(SectionCreate(chapter_id=chapter.id, title="Section 3", order=3))

        sections = await service.get_all()

        assert len(sections) == 3
        assert sections[0].title == "Section 1"
        assert sections[1].title == "Section 2"
        assert sections[2].title == "Section 3"

    async def test_get_all_with_pagination(self, db_session: AsyncSession):
        """Edge case: get all with pagination"""
        volume = await create_test_volume(db_session)
        chapter = await create_test_chapter(db_session, volume.id)

        service = SectionService(db_session)
        for i in range(5):
            await service.create(SectionCreate(chapter_id=chapter.id, title=f"Section {i}", order=i))

        # Test limit
        sections = await service.get_all(skip=0, limit=2)
        assert len(sections) == 2

        # Test skip
        sections = await service.get_all(skip=2, limit=10)
        assert len(sections) == 3

    async def test_update_section(self, db_session: AsyncSession):
        """Golden path: update existing section"""
        volume = await create_test_volume(db_session)
        chapter = await create_test_chapter(db_session, volume.id)

        service = SectionService(db_session)
        created = await service.create(SectionCreate(chapter_id=chapter.id, title="Original"))
        updated = await service.update(created.id, SectionUpdate(title="Updated", content="New content"))

        assert updated is not None
        assert updated.title == "Updated"
        assert updated.content == "New content"

    async def test_update_section_partial(self, db_session: AsyncSession):
        """Edge case: partial update (only some fields)"""
        volume = await create_test_volume(db_session)
        chapter = await create_test_chapter(db_session, volume.id)

        service = SectionService(db_session)
        created = await service.create(
            SectionCreate(chapter_id=chapter.id, title="Original", content="Original content", order=5)
        )
        updated = await service.update(created.id, SectionUpdate(title="New Title Only"))

        assert updated.title == "New Title Only"
        assert updated.content == "Original content"  # unchanged
        assert updated.order == 5  # unchanged

    async def test_update_section_not_found(self, db_session: AsyncSession):
        """Error case: update non-existent section"""
        service = SectionService(db_session)
        result = await service.update(99999, SectionUpdate(title="Should fail"))

        assert result is None

    async def test_delete_section(self, db_session: AsyncSession):
        """Golden path: delete existing section"""
        volume = await create_test_volume(db_session)
        chapter = await create_test_chapter(db_session, volume.id)

        service = SectionService(db_session)
        created = await service.create(SectionCreate(chapter_id=chapter.id, title="To Delete"))
        result = await service.delete(created.id)

        assert result is True
        # Verify it's gone
        found = await service.get_by_id(created.id)
        assert found is None

    async def test_delete_section_not_found(self, db_session: AsyncSession):
        """Error case: delete non-existent section"""
        service = SectionService(db_session)
        result = await service.delete(99999)

        assert result is False

    async def test_cascade_delete_with_chapter(self, db_session: AsyncSession):
        """Verify sections are deleted when parent chapter is deleted"""
        volume = await create_test_volume(db_session)
        chapter = await create_test_chapter(db_session, volume.id)

        section_service = SectionService(db_session)
        chapter_service = ChapterService(db_session)
        section = await section_service.create(SectionCreate(chapter_id=chapter.id, title="Test Section"))

        # Delete chapter (should cascade delete section)
        await chapter_service.delete(chapter.id)

        # Section should be gone
        found = await section_service.get_by_id(section.id)
        assert found is None
