import json
import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, get_db_context
from app.models.teaching import TeachingSessionStatus
from app.schemas.teaching import (
    ChatRequest,
    EndSessionRequest,
    RateMessageRequest,
    SubmitQuestionRequest,
    TeachingChatResponse,
    TeachingSessionDetailResponse,
    TeachingMessageResponse,
    TeachingSessionSummaryResponse,
)
from app.services.teaching import TeachingService

logger = logging.getLogger(__name__)

router = APIRouter()
DbSession = Annotated[AsyncSession, Depends(get_db)]


async def _run_pipeline_bg(
    session_id: int,
    question_content: str,
    question_image: str | None,
    frame_base64: str | None,
) -> None:
    async with get_db_context() as db:
        service = TeachingService(db)
        try:
            await service.run_pipeline(session_id, question_content, question_image, frame_base64)
        except Exception:
            logger.exception("Teaching pipeline background task failed for session %s", session_id)


@router.post(
    "/sessions",
    response_model=TeachingSessionDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_session(
    data: SubmitQuestionRequest,
    background_tasks: BackgroundTasks,
    db: DbSession,
) -> TeachingSessionDetailResponse:
    service = TeachingService(db)
    try:
        session = await service.create_session_shell(
            student_id=data.student_id,
            question_content=data.question_content,
            question_image=data.question_image,
            source_practice_session_id=data.source_practice_session_id,
            source_question_ids=data.source_question_ids,
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    await db.commit()
    detail = await service.get_session(session.id)
    # 流水线用的题目文本：练习转来时取拼好的第一条消息
    pipeline_content = detail.messages[0].content if detail.messages else data.question_content

    background_tasks.add_task(
        _run_pipeline_bg,
        session.id,
        pipeline_content,
        data.question_image,
        data.frame_base64,
    )
    return TeachingSessionDetailResponse.model_validate(detail)


@router.post("/sessions/rate", response_model=TeachingMessageResponse)
async def rate_message(data: RateMessageRequest, db: DbSession) -> TeachingMessageResponse:
    """学生对某条 AI 回复的掌握度自评（选填，可取消）"""
    service = TeachingService(db)
    try:
        msg = await service.rate_message(
            session_id=data.session_id, message_id=data.message_id, rating=data.rating,
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return TeachingMessageResponse.model_validate(msg)


@router.post("/sessions/chat", response_model=TeachingChatResponse)
async def chat(data: ChatRequest, db: DbSession) -> TeachingChatResponse:
    service = TeachingService(db)
    try:
        assistant_msg, _ = await service.chat(
            session_id=data.session_id,
            user_message=data.message,
            frame_base64=data.frame_base64,
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return TeachingChatResponse(
        session_id=data.session_id,
        assistant_message=TeachingMessageResponse.model_validate(assistant_msg),
    )


@router.post("/sessions/chat/stream")
async def chat_stream(data: ChatRequest, db: DbSession) -> StreamingResponse:
    service = TeachingService(db)
    session = await service.get_session(data.session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.status != TeachingSessionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Session is not active (status={session.status.value})",
        )
    await db.rollback()

    async def event_gen():
        async with get_db_context() as inner_db:
            inner_service = TeachingService(inner_db)
            try:
                async for delta in inner_service.chat_stream(
                    data.session_id, data.message, data.frame_base64,
                ):
                    yield f"data: {json.dumps({'delta': delta}, ensure_ascii=False)}\n\n"
                yield "event: done\ndata: {}\n\n"
            except Exception as exc:
                logger.exception("chat stream failed for session %s", data.session_id)
                yield f"event: error\ndata: {json.dumps({'detail': str(exc)})}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/sessions/end", response_model=TeachingSessionDetailResponse)
async def end_session(
    data: EndSessionRequest, db: DbSession,
) -> TeachingSessionDetailResponse:
    service = TeachingService(db)
    try:
        session = await service.end_session(
            session_id=data.session_id,
            mastery_level_delta=data.mastery_level_delta,
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return TeachingSessionDetailResponse.model_validate(session)


@router.post(
    "/sessions/{session_id}/cancel", response_model=TeachingSessionDetailResponse,
)
async def cancel_session(
    session_id: int, db: DbSession,
) -> TeachingSessionDetailResponse:
    service = TeachingService(db)
    try:
        session = await service.cancel_session(session_id=session_id)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return TeachingSessionDetailResponse.model_validate(session)


@router.get("/sessions", response_model=list[TeachingSessionSummaryResponse])
async def list_sessions(
    db: DbSession,
    student_id: int = Query(..., ge=1),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[TeachingSessionSummaryResponse]:
    service = TeachingService(db)
    rows = await service.list_sessions_by_student(
        student_id=student_id, limit=limit, offset=offset,
    )
    return [
        TeachingSessionSummaryResponse(
            id=session.id,
            student_id=session.student_id,
            status=session.status,
            pipeline_status=session.pipeline_status,
            strategy=session.strategy,
            ended_at=session.ended_at,
            source_practice_session_id=session.source_practice_session_id,
            source_question_ids=session.source_question_ids,
            created_at=session.created_at,
            updated_at=session.updated_at,
            preview=preview,
            message_count=count,
        )
        for session, preview, count in rows
    ]


@router.get("/sessions/{session_id}", response_model=TeachingSessionDetailResponse)
async def get_session(
    session_id: int, db: DbSession,
) -> TeachingSessionDetailResponse:
    service = TeachingService(db)
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found",
        )
    return TeachingSessionDetailResponse.model_validate(session)
