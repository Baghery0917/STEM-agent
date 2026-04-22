from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Gender, Student
from app.schemas.student import StudentCreate, StudentUpdate
from app.services.student import StudentService


class TestStudentService:
    """Tests for StudentService"""

    async def test_create_student(self, db_session: AsyncSession):
        """Golden path: create a student"""
        service = StudentService()
        data = StudentCreate(name="Alice", gender=Gender.FEMALE)
        student = await service.create(db_session, data)

        assert student.id is not None
        assert student.name == "Alice"
        assert student.gender == Gender.FEMALE

    async def test_get_student_by_id(self, db_session: AsyncSession):
        """Golden path: get a student by id"""
        service = StudentService()
        created = await service.create(db_session, StudentCreate(name="Bob", gender=Gender.MALE))

        found = await service.get(db_session, created.id)

        assert found is not None
        assert found.id == created.id
        assert found.name == "Bob"
        assert found.gender == Gender.MALE

    async def test_get_list_all_students(self, db_session: AsyncSession):
        """Golden path: list all students"""
        service = StudentService()
        await service.create(db_session, StudentCreate(name="Alice", gender=Gender.FEMALE))
        await service.create(db_session, StudentCreate(name="Bob", gender=Gender.MALE))

        students = await service.get_list(db_session)

        assert len(students) == 2

    async def test_get_list_filtered_by_gender(self, db_session: AsyncSession):
        """Golden path: list students filtered by gender"""
        service = StudentService()
        await service.create(db_session, StudentCreate(name="Alice", gender=Gender.FEMALE))
        await service.create(db_session, StudentCreate(name="Bob", gender=Gender.MALE))
        await service.create(db_session, StudentCreate(name="Charlie", gender=Gender.MALE))

        males = await service.get_list(db_session, gender=Gender.MALE.value)

        assert len(males) == 2
        assert all(s.gender == Gender.MALE for s in males)

    async def test_get_list_pagination(self, db_session: AsyncSession):
        """Golden path: list students with pagination"""
        service = StudentService()
        for i in range(5):
            await service.create(db_session, StudentCreate(name=f"Student{i}", gender=Gender.OTHER))

        first_page = await service.get_list(db_session, skip=0, limit=2)
        assert len(first_page) == 2

        second_page = await service.get_list(db_session, skip=2, limit=2)
        assert len(second_page) == 2

        remainder = await service.get_list(db_session, skip=4, limit=10)
        assert len(remainder) == 1

    async def test_update_student(self, db_session: AsyncSession):
        """Golden path: update a student"""
        service = StudentService()
        created = await service.create(db_session, StudentCreate(name="Old Name", gender=Gender.MALE))

        updated = await service.update(db_session, created.id, StudentUpdate(name="New Name", gender=Gender.FEMALE))

        assert updated is not None
        assert updated.name == "New Name"
        assert updated.gender == Gender.FEMALE

    async def test_partial_update_student(self, db_session: AsyncSession):
        """Golden path: partial update (only name)"""
        service = StudentService()
        created = await service.create(db_session, StudentCreate(name="Original", gender=Gender.MALE))

        updated = await service.update(db_session, created.id, StudentUpdate(name="Updated"))

        assert updated is not None
        assert updated.name == "Updated"
        assert updated.gender == Gender.MALE

    async def test_delete_student(self, db_session: AsyncSession):
        """Golden path: delete a student"""
        service = StudentService()
        created = await service.create(db_session, StudentCreate(name="ToDelete", gender=Gender.OTHER))

        result = await service.delete(db_session, created.id)

        assert result is True
        found = await service.get(db_session, created.id)
        assert found is None

    async def test_create_student_with_max_length_name(self, db_session: AsyncSession):
        """Edge case: create student with 100-character name (boundary)"""
        service = StudentService()
        long_name = "A" * 100
        student = await service.create(db_session, StudentCreate(name=long_name, gender=Gender.FEMALE))

        assert student.name == long_name

    async def test_get_list_with_skip_beyond_total(self, db_session: AsyncSession):
        """Edge case: skip beyond total count returns empty list"""
        service = StudentService()
        await service.create(db_session, StudentCreate(name="Only", gender=Gender.MALE))

        results = await service.get_list(db_session, skip=100, limit=10)

        assert results == []

    async def test_get_list_with_limit_zero(self, db_session: AsyncSession):
        """Edge case: limit of zero returns empty list"""
        service = StudentService()
        await service.create(db_session, StudentCreate(name="Only", gender=Gender.MALE))

        results = await service.get_list(db_session, skip=0, limit=0)

        assert results == []

    async def test_get_list_filtered_by_gender_no_matches(self, db_session: AsyncSession):
        """Edge case: gender filter with no matches returns empty list"""
        service = StudentService()
        await service.create(db_session, StudentCreate(name="Alice", gender=Gender.FEMALE))

        results = await service.get_list(db_session, gender=Gender.MALE.value)

        assert results == []

    async def test_get_nonexistent_student(self, db_session: AsyncSession):
        """Error case: get non-existent student returns None"""
        service = StudentService()
        found = await service.get(db_session, 99999)

        assert found is None

    async def test_update_nonexistent_student(self, db_session: AsyncSession):
        """Error case: update non-existent student returns None"""
        service = StudentService()
        result = await service.update(db_session, 99999, StudentUpdate(name="Nope"))

        assert result is None

    async def test_delete_nonexistent_student(self, db_session: AsyncSession):
        """Error case: delete non-existent student returns False"""
        service = StudentService()
        result = await service.delete(db_session, 99999)

        assert result is False
