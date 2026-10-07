import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.external.emotion import describe_value
from app.llm.client import LLMClient
from app.models.emotion import EmotionLog
from app.models.practice import PracticeItem, PracticeSession
from app.models.section import Section
from app.models.student_knowledge_summary import StudentKnowledgeSummary
from app.models.teaching import TeachingSession
from app.schemas.report import (
    EmotionDay,
    EmotionLogEntry,
    KnowledgePointMastery,
    StudentReport,
)

logger = logging.getLogger(__name__)

RECENT_DAYS = 7


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ReportService:
    def __init__(self, db: AsyncSession, llm: LLMClient | None = None) -> None:
        self.db = db
        self.llm = llm or LLMClient()

    async def build(self, student_id: int, mode: str, with_summary: bool = True) -> StudentReport:
        now = _utcnow()
        start = now - timedelta(days=RECENT_DAYS) if mode == "recent" else datetime(1970, 1, 1)

        summaries = await self._knowledge_points(student_id, mode, start)
        practice_count, answered, correct = await self._practice_stats(student_id, start)
        teaching_count = await self._teaching_count(student_id, start)
        logs = await self._emotion_logs(student_id, start)
        days = self._emotion_days(logs, start if mode == "recent" else now - timedelta(days=RECENT_DAYS), now)

        report = StudentReport(
            mode=mode,
            range_start=start,
            range_end=now,
            practice_count=practice_count,
            teaching_count=teaching_count,
            answered_count=answered,
            correct_count=correct,
            knowledge_points=summaries,
            emotion_days=days,
            emotion_logs=logs[:20],
        )
        if with_summary:
            report.summary = await self._summarize(report)
        return report

    # ------------------------------------------------------------------

    async def _knowledge_points(
        self, student_id: int, mode: str, start: datetime,
    ) -> list[KnowledgePointMastery]:
        result = await self.db.execute(
            select(StudentKnowledgeSummary, Section.title)
            .join(Section, Section.id == StudentKnowledgeSummary.section_id)
            .where(StudentKnowledgeSummary.student_id == student_id)
        )
        rows = result.all()
        if mode == "recent":
            rows = [
                (s, t) for s, t in rows
                if (s.last_practice_at and _naive(s.last_practice_at) >= start)
                or (s.last_teaching_at and _naive(s.last_teaching_at) >= start)
            ]

        recent_practice = await self._recent_practice_by_section(student_id, start)
        recent_teaching = await self._recent_teaching_by_section(student_id, start)

        points = [
            KnowledgePointMastery(
                section_id=s.section_id,
                section_title=title,
                mastery_level=s.mastery_level,
                correct_count=s.correct_count,
                total_practice_count=s.total_practice_count,
                total_teaching_count=s.total_teaching_count,
                last_practice_at=s.last_practice_at,
                last_teaching_at=s.last_teaching_at,
                recent_practice_count=recent_practice.get(s.section_id, 0),
                recent_teaching_count=recent_teaching.get(s.section_id, 0),
            )
            for s, title in rows
        ]
        points.sort(key=lambda p: (-(p.recent_practice_count + p.recent_teaching_count), p.mastery_level))
        return points

    async def _recent_practice_by_section(self, student_id: int, start: datetime) -> dict[int, int]:
        from app.models.question import question_knowledge_point

        result = await self.db.execute(
            select(question_knowledge_point.c.section_id, func.count(PracticeItem.id))
            .join(PracticeItem, PracticeItem.question_id == question_knowledge_point.c.question_id)
            .where(
                PracticeItem.student_id == student_id,
                PracticeItem.is_skipped.is_(False),
                PracticeItem.created_at >= start,
            )
            .group_by(question_knowledge_point.c.section_id)
        )
        return {sid: int(c) for sid, c in result.all()}

    async def _recent_teaching_by_section(self, student_id: int, start: datetime) -> dict[int, int]:
        result = await self.db.execute(
            select(EmotionLog.section_id, func.count(EmotionLog.id))
            .where(
                EmotionLog.student_id == student_id,
                EmotionLog.mode == "TEACHING",
                EmotionLog.created_at >= start,
            )
            .group_by(EmotionLog.section_id)
        )
        return {sid: int(c) for sid, c in result.all()}

    async def _practice_stats(self, student_id: int, start: datetime) -> tuple[int, int, int]:
        sessions = await self.db.execute(
            select(func.count(PracticeSession.id)).where(
                PracticeSession.student_id == student_id,
                PracticeSession.started_at >= start,
            )
        )
        items = await self.db.execute(
            select(
                func.count(PracticeItem.id),
                func.coalesce(func.sum(case((PracticeItem.is_correct.is_(True), 1), else_=0)), 0),
            ).where(
                PracticeItem.student_id == student_id,
                PracticeItem.is_skipped.is_(False),
                PracticeItem.created_at >= start,
            )
        )
        answered, correct = items.one()
        return int(sessions.scalar() or 0), int(answered or 0), int(correct or 0)

    async def _teaching_count(self, student_id: int, start: datetime) -> int:
        result = await self.db.execute(
            select(func.count(TeachingSession.id)).where(
                TeachingSession.student_id == student_id,
                TeachingSession.created_at >= start,
            )
        )
        return int(result.scalar() or 0)

    async def _emotion_logs(self, student_id: int, start: datetime) -> list[EmotionLogEntry]:
        result = await self.db.execute(
            select(EmotionLog, Section.title)
            .join(Section, Section.id == EmotionLog.section_id)
            .where(EmotionLog.student_id == student_id, EmotionLog.created_at >= start)
            .order_by(EmotionLog.created_at.desc())
            .limit(200)
        )
        return [
            EmotionLogEntry(
                section_id=log.section_id,
                section_title=title,
                mode=log.mode.value,
                session_id=log.session_id,
                emotion_value=log.emotion_value,
                emotion=describe_value(log.emotion_value),
                created_at=log.created_at,
            )
            for log, title in result.all()
        ]

    @staticmethod
    def _emotion_days(logs: list[EmotionLogEntry], start: datetime, end: datetime) -> list[EmotionDay]:
        by_day: dict[str, list[float]] = defaultdict(list)
        for log in logs:
            by_day[_naive(log.created_at).date().isoformat()].append(log.emotion_value)
        days: list[EmotionDay] = []
        cursor = start.date()
        while cursor <= end.date():
            key = cursor.isoformat()
            values = by_day.get(key, [])
            days.append(EmotionDay(
                date=key,
                value=round(sum(values) / len(values), 2) if values else None,
                count=len(values),
            ))
            cursor += timedelta(days=1)
        return days[-RECENT_DAYS:]

    async def _summarize(self, report: StudentReport) -> str | None:
        if report.practice_count == 0 and report.teaching_count == 0:
            return None
        kp_lines = "\n".join(
            f"- {p.section_title}: 掌握度 {p.mastery_level:.0%}，练 {p.recent_practice_count} 题，讲 {p.recent_teaching_count} 次"
            for p in report.knowledge_points[:8]
        ) or "- 无"
        emo_lines = "\n".join(
            f"- {d.date}: {describe_value(d.value) if d.value is not None else '无记录'}"
            for d in report.emotion_days
        )
        prompt = (
            "你是一名物理辅导老师，请用两到三句中文口语化地总结学生这段时间的学习情况，"
            "点出进步最大的知识点、最需要补的知识点，以及情绪状态对学习的影响，并给一条具体建议。"
            "不要用列表，不要超过 120 字。\n\n"
            f"统计区间：{'近 7 天' if report.mode == 'recent' else '全部'}\n"
            f"练习 {report.practice_count} 次，作答 {report.answered_count} 题，正确 {report.correct_count} 题；"
            f"教学会话 {report.teaching_count} 次。\n"
            f"知识点：\n{kp_lines}\n情绪（1 自信 … 5 非常受挫）：\n{emo_lines}"
        )
        try:
            text = await self.llm.chat([{"role": "user", "content": prompt}], temperature=0.4)
            return text.strip() or None
        except Exception as exc:
            logger.warning("Report summary LLM failed: %s", exc)
            return None


def _naive(dt: datetime) -> datetime:
    return dt.replace(tzinfo=None) if dt.tzinfo else dt
