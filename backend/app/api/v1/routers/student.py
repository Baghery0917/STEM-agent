from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
import logging

from app.external.evaluation import EvaluationClient
from app.schemas.evaluation import StudentEvaluation
from app.schemas.report import StudentReport
from app.schemas.search import SessionSearchHit, SessionSearchResponse
from app.services.search import SessionSearchService
from app.schemas.student import StudentCreate, StudentUpdate, StudentResponse
from app.services.report import ReportService
from app.services.student import StudentService
from app.models.student import Gender, Persona
from app.schemas.recognition import StudentCardResponse, StudentCardsResponse
from app.services.recognition import RecognitionService

logger = logging.getLogger(__name__)

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


@router.get("/{student_id}/report", response_model=StudentReport)
async def get_student_report(
    student_id: int,
    db: DbSession,
    mode: str = Query("recent", pattern="^(recent|all)$"),
    summary: bool = Query(True, description="是否让 LLM 生成一段话总结"),
) -> StudentReport:
    """学习报告：知识点掌握度、练习/教学统计、情绪趋势与流水"""
    student = await StudentService().get(db, student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return await ReportService(db).build(student_id, mode, with_summary=summary)


@router.get("/{student_id}/evaluation", response_model=StudentEvaluation)
async def get_student_evaluation(student_id: int, db: DbSession) -> StudentEvaluation:
    """评价处对学生的评价：经 MCP 调外部服务，只传 student_id，数据由评价服务自行读库"""
    student = await StudentService().get(db, student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    client = EvaluationClient()
    if not client.is_configured():
        return StudentEvaluation(student_id=student_id, source="unavailable", detail="评价处未配置")
    try:
        result = await client.get_evaluation(student_id)
    except Exception as exc:
        logger.warning("Evaluation MCP failed for student %s: %s", student_id, exc)
        return StudentEvaluation(student_id=student_id, source="unavailable", detail=str(exc))
    return StudentEvaluation(
        student_id=student_id, evaluation=result.evaluation, highlights=result.highlights, source="mcp",
    )


@router.get("/{student_id}/sessions/search", response_model=SessionSearchResponse)
async def search_sessions(
    student_id: int,
    db: DbSession,
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(20, ge=1, le=50),
) -> SessionSearchResponse:
    """左侧会话栏搜索：教学按消息内容，练习按知识点名"""
    hits = await SessionSearchService(db).search(student_id, q, limit)
    return SessionSearchResponse(q=q, hits=[SessionSearchHit(**h) for h in hits])


@router.get("/{student_id}/cards", response_model=StudentCardsResponse)
async def get_student_cards(student_id: int, db: DbSession) -> StudentCardsResponse:
    if not await StudentService().get(db, student_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    rec = RecognitionService(db)
    return StudentCardsResponse(
        cards=[StudentCardResponse.model_validate(c) for c in await rec.cards(student_id)],
        unlocked=await rec.unlocked_personas(student_id),
    )


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(student_id: int, data: StudentUpdate, db: DbSession) -> StudentResponse:
    service = StudentService()
    if data.persona is not None and data.persona != Persona.LEONARD:
        unlocked = await RecognitionService(db).unlocked_personas(student_id)
        if data.persona not in unlocked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Persona not unlocked")
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
