from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.student import Student
from app.schemas.student import StudentCreate, StudentUpdate


class StudentService:
    async def create(self, db: AsyncSession, obj_in: StudentCreate) -> Student:
        db_obj = Student(**obj_in.model_dump())
        db.add(db_obj)
        await db.flush()
        return db_obj

    async def get(self, db: AsyncSession, student_id: int) -> Student | None:
        stmt = select(Student).where(Student.id == student_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_list(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        gender: str | None = None,
    ) -> list[Student]:
        stmt = select(Student)

        if gender:
            stmt = stmt.where(Student.gender == gender)

        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def update(self, db: AsyncSession, student_id: int, obj_in: StudentUpdate) -> Student | None:
        db_obj = await self.get(db, student_id)
        if not db_obj:
            return None

        update_data = obj_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_obj, key, value)

        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, student_id: int) -> bool:
        db_obj = await self.get(db, student_id)
        if not db_obj:
            return False
        await db.delete(db_obj)
        await db.flush()
        return True
