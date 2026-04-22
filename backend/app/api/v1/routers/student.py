from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.student import StudentCreate, StudentUpdate, StudentResponse
from app.services.student import StudentService
from app.models.student import Gender

router = APIRouter()

DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(data: StudentCreate, db: DbSession) -> StudentResponse:
    service = StudentService()
    student = await service.create(db, data)
    return StudentResponse.model_validate(student)


@router.get("", response_model=list[StudentResponse])
async def list_students(
    db: DbSession,
    skip: int = 0,
    limit: int = 20,
    gender: Gender | None = None,
) -> list[StudentResponse]:
    service = StudentService()
    students = await service.get_list(db, skip=skip, limit=limit, gender=gender)
    return [StudentResponse.model_validate(s) for s in students]


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(student_id: int, db: DbSession) -> StudentResponse:
    service = StudentService()
    student = await service.get(db, student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return StudentResponse.model_validate(student)


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(student_id: int, data: StudentUpdate, db: DbSession) -> StudentResponse:
    service = StudentService()
    student = await service.update(db, student_id, data)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return StudentResponse.model_validate(student)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(student_id: int, db: DbSession) -> None:
    service = StudentService()
    deleted = await service.delete(db, student_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
