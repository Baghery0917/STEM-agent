from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.practice import (
    NextQuestionResponse,
    PracticeItemResponse,
    PracticeSessionDetailResponse,
    PracticeSessionResponse,
    SkipQuestionRequest,
    StartFocusedRequest,
    StartGeneralRequest,
    StartSessionResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)
from app.schemas.question import QuestionPublicResponse
from app.services.practice import PracticeService

router = APIRouter()
DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.post(
    "/sessions/focused",
    response_model=StartSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_focused_session(
    data: StartFocusedRequest, db: DbSession,
) -> StartSessionResponse:
    service = PracticeService(db)
    try:
        session, question = await service.start_focused_session(
            student_id=data.student_id,
            knowledge_point_ids=data.knowledge_point_ids,
            difficulty_range=data.difficulty_range,
            total_count=data.total_count,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e),
        )
    return StartSessionResponse(
        session=PracticeSessionResponse.model_validate(session),
        question=QuestionPublicResponse.model_validate(question),
    )


@router.post(
    "/sessions/general",
    response_model=StartSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_general_session(
    data: StartGeneralRequest, db: DbSession,
) -> StartSessionResponse:
    service = PracticeService(db)
    try:
        session, question = await service.start_general_session(
            student_id=data.student_id,
            knowledge_point_ids=data.knowledge_point_ids,
            difficulty_range=data.difficulty_range,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e),
        )
    return StartSessionResponse(
        session=PracticeSessionResponse.model_validate(session),
        question=QuestionPublicResponse.model_validate(question),
    )


@router.post(
    "/sessions/{session_id}/submit",
    response_model=SubmitAnswerResponse,
)
async def submit_answer(
    session_id: int,
    data: SubmitAnswerRequest,
    db: DbSession,
) -> SubmitAnswerResponse:
    service = PracticeService(db)
    try:
        item, is_correct, next_question = await service.submit_answer(
            session_id=session_id,
            question_id=data.question_id,
            user_answer=data.user_answer,
            emotion=data.emotion,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e),
        )
    return SubmitAnswerResponse(
        item=PracticeItemResponse.model_validate(item),
        is_correct=is_correct,
        next_question=QuestionPublicResponse.model_validate(next_question) if next_question else None,
    )


@router.post(
    "/sessions/{session_id}/skip",
    response_model=NextQuestionResponse,
)
async def skip_question(
    session_id: int,
    data: SkipQuestionRequest,
    db: DbSession,
) -> NextQuestionResponse:
    service = PracticeService(db)
    try:
        question = await service.skip_question(
            session_id=session_id,
            question_id=data.question_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e),
        )
    return NextQuestionResponse(
        question=QuestionPublicResponse.model_validate(question) if question else None,
    )


@router.post(
    "/sessions/{session_id}/next",
    response_model=NextQuestionResponse,
)
async def next_question(
    session_id: int, db: DbSession,
) -> NextQuestionResponse:
    service = PracticeService(db)
    try:
        question = await service.next_question(session_id=session_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e),
        )
    return NextQuestionResponse(
        question=QuestionPublicResponse.model_validate(question) if question else None,
    )


@router.post(
    "/sessions/{session_id}/end",
    response_model=PracticeSessionResponse,
)
async def end_session(
    session_id: int, db: DbSession,
) -> PracticeSessionResponse:
    service = PracticeService(db)
    try:
        session = await service.end_session(session_id=session_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e),
        )
    return PracticeSessionResponse.model_validate(session)


@router.get(
    "/sessions",
    response_model=list[PracticeSessionResponse],
)
async def list_sessions(
    db: DbSession,
    student_id: int = Query(..., ge=1),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[PracticeSessionResponse]:
    service = PracticeService(db)
    sessions = await service.list_sessions_by_student(
        student_id=student_id, limit=limit, offset=offset,
    )
    return [PracticeSessionResponse.model_validate(s) for s in sessions]


@router.get(
    "/sessions/{session_id}",
    response_model=PracticeSessionDetailResponse,
)
async def get_session(
    session_id: int, db: DbSession,
) -> PracticeSessionDetailResponse:
    service = PracticeService(db)
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found",
        )
    return PracticeSessionDetailResponse.model_validate(session)
