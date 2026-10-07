from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.practice import (
    PracticeItemResponse,
    PracticeMatchRequest,
    PracticeMatchResponse,
    PracticeSessionDetailResponse,
    PracticeSessionResponse,
    SkipQuestionRequest,
    SkipQuestionResponse,
    StarQuestionRequest,
    StartPracticeRequest,
    StartSessionResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)
from app.schemas.question import QuestionPublicResponse
from app.services.practice import PracticeService

router = APIRouter()
DbSession = Annotated[AsyncSession, Depends(get_db)]


def _bad_request(e: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/match", response_model=PracticeMatchResponse)
async def match_questions(data: PracticeMatchRequest, db: DbSession) -> PracticeMatchResponse:
    """开始前预估题库里符合范围的题数，前端展示「题库匹配 N 题」"""
    service = PracticeService(db)
    try:
        count = await service.count_matching(
            knowledge_point_ids=data.knowledge_point_ids,
            difficulty_range=data.difficulty_range,
            question_types=data.question_types,
        )
    except ValueError as e:
        raise _bad_request(e)
    return PracticeMatchResponse(matched_count=count)


@router.post(
    "/sessions",
    response_model=StartSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_session(data: StartPracticeRequest, db: DbSession) -> StartSessionResponse:
    service = PracticeService(db)
    try:
        session, questions = await service.start_session(
            student_id=data.student_id,
            knowledge_point_ids=data.knowledge_point_ids,
            difficulty_range=data.difficulty_range,
            total_count=data.total_count,
            timed=data.timed,
            question_types=data.question_types,
            instant_feedback=data.instant_feedback,
        )
    except ValueError as e:
        raise _bad_request(e)
    return StartSessionResponse(
        session=PracticeSessionResponse.model_validate(session),
        questions=[QuestionPublicResponse.model_validate(q) for q in questions],
    )


@router.post("/sessions/{session_id}/submit", response_model=SubmitAnswerResponse)
async def submit_answer(
    session_id: int, data: SubmitAnswerRequest, db: DbSession,
) -> SubmitAnswerResponse:
    service = PracticeService(db)
    try:
        item, is_correct, question, session = await service.submit_answer(
            session_id=session_id,
            question_id=data.question_id,
            user_answer=data.user_answer,
            duration_seconds=data.duration_seconds,
            frame_base64=data.frame_base64,
        )
    except ValueError as e:
        raise _bad_request(e)
    item_resp = PracticeItemResponse.model_validate(item)
    if not session.instant_feedback:
        # 统一批改：提交阶段不透露对错与答案
        item_resp.is_correct = False
        return SubmitAnswerResponse(
            item=item_resp, session=PracticeSessionResponse.model_validate(session),
        )
    return SubmitAnswerResponse(
        item=item_resp,
        is_correct=is_correct,
        correct_answer=question.answer,
        analysis=question.analysis,
        analysis_image=question.analysis_image,
        session=PracticeSessionResponse.model_validate(session),
    )


@router.post("/sessions/{session_id}/skip", response_model=SkipQuestionResponse)
async def skip_question(
    session_id: int, data: SkipQuestionRequest, db: DbSession,
) -> SkipQuestionResponse:
    service = PracticeService(db)
    try:
        item, session = await service.skip_question(
            session_id=session_id,
            question_id=data.question_id,
            duration_seconds=data.duration_seconds,
        )
    except ValueError as e:
        raise _bad_request(e)
    return SkipQuestionResponse(
        item=PracticeItemResponse.model_validate(item),
        session=PracticeSessionResponse.model_validate(session),
    )


@router.post("/sessions/{session_id}/star", response_model=PracticeSessionResponse)
async def star_question(
    session_id: int, data: StarQuestionRequest, db: DbSession,
) -> PracticeSessionResponse:
    service = PracticeService(db)
    try:
        session = await service.star_question(
            session_id=session_id, question_id=data.question_id, starred=data.starred,
        )
    except ValueError as e:
        raise _bad_request(e)
    return PracticeSessionResponse.model_validate(session)


@router.post("/sessions/{session_id}/end", response_model=PracticeSessionResponse)
async def end_session(session_id: int, db: DbSession) -> PracticeSessionResponse:
    service = PracticeService(db)
    try:
        session = await service.end_session(session_id=session_id)
    except ValueError as e:
        raise _bad_request(e)
    return PracticeSessionResponse.model_validate(session)


@router.get("/sessions", response_model=list[PracticeSessionResponse])
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


@router.get("/sessions/{session_id}", response_model=PracticeSessionDetailResponse)
async def get_session(session_id: int, db: DbSession) -> PracticeSessionDetailResponse:
    service = PracticeService(db)
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return PracticeSessionDetailResponse.model_validate(session)
