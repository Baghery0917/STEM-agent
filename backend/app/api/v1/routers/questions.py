from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.question import QuestionCreate, QuestionUpdate, QuestionResponse
from app.services.question import QuestionService
from app.models.question import QuestionType, Difficulty

router = APIRouter()

DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.post("", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_question(data: QuestionCreate, db: DbSession) -> QuestionResponse:
    service = QuestionService()
    try:
        question = await service.create(db, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return QuestionResponse.model_validate(question)


@router.get("", response_model=list[QuestionResponse])
async def list_questions(
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    type: QuestionType | None = None,
    difficulty: Difficulty | None = None,
    knowledge_point_ids: list[int] = Query(default=[]),
    volume_id: int | None = None,
    chapter_id: int | None = None,
    match_all_kps: bool = False,
) -> list[QuestionResponse]:
    service = QuestionService()
    questions = await service.get_list(
        db, skip=skip, limit=limit, type=type, difficulty=difficulty,
        knowledge_point_ids=knowledge_point_ids or None,
        volume_id=volume_id, chapter_id=chapter_id,
        match_all_kps=match_all_kps,
    )
    return [QuestionResponse.model_validate(q) for q in questions]


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(question_id: int, db: DbSession) -> QuestionResponse:
    service = QuestionService()
    question = await service.get(db, question_id)
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    return QuestionResponse.model_validate(question)


@router.put("/{question_id}", response_model=QuestionResponse)
async def update_question(question_id: int, data: QuestionUpdate, db: DbSession) -> QuestionResponse:
    service = QuestionService()
    try:
        question = await service.update(db, question_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    return QuestionResponse.model_validate(question)


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(question_id: int, db: DbSession) -> None:
    service = QuestionService()
    deleted = await service.delete(db, question_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")