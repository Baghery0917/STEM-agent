import logging
import re
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.external.emotion import describe_value
from app.models.emotion import EmotionMode
from app.models.practice import PracticeItem, PracticeSession
from app.models.question import (
    Difficulty,
    Question,
    QuestionType,
    question_knowledge_point,
)
from app.models.section import Section
from app.models.student_knowledge_summary import StudentKnowledgeSummary
from app.services.emotion import EmotionService

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class PracticeService:
    """练习流程。

    不再区分专项 / 综合：开始时按范围一次性抽满题目，学生可以在题目间自由切换，
    每题都可跳过（计 0 分、不计入档案）。计时与否只影响前端能否中途转去提问。
    """

    def __init__(self, db: AsyncSession, emotion: EmotionService | None = None) -> None:
        self.db = db
        self.emotion = emotion or EmotionService()

    # ------------------------------------------------------------------
    # 公开方法
    # ------------------------------------------------------------------

    async def count_matching(
        self,
        knowledge_point_ids: list[int],
        difficulty_range: list[str],
        question_types: list[str] | None = None,
    ) -> int:
        await self._validate_knowledge_points(knowledge_point_ids)
        stmt = self._question_filter(knowledge_point_ids, difficulty_range, question_types)
        result = await self.db.execute(select(func.count()).select_from(stmt.subquery()))
        return int(result.scalar() or 0)

    async def start_session(
        self,
        student_id: int,
        knowledge_point_ids: list[int],
        difficulty_range: list[str],
        total_count: int,
        timed: bool = False,
        question_types: list[str] | None = None,
        instant_feedback: bool = True,
    ) -> tuple[PracticeSession, list[Question]]:
        await self._validate_knowledge_points(knowledge_point_ids)
        questions = await self._draw_questions(
            knowledge_point_ids, difficulty_range, question_types, total_count,
        )
        if not questions:
            raise ValueError("No questions match the given criteria")

        session = PracticeSession(
            timed=timed,
            # 计时练习不做逐题反馈，避免看答案打断节奏
            instant_feedback=False if timed else instant_feedback,
            knowledge_point_ids=knowledge_point_ids,
            difficulty_range=difficulty_range,
            question_ids=[q.id for q in questions],
            starred_question_ids=[],
            student_id=student_id,
            total_count=len(questions),
            started_at=_utcnow(),
        )
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session, questions

    async def submit_answer(
        self,
        session_id: int,
        question_id: int,
        user_answer: str,
        duration_seconds: int | None = None,
        frame_base64: str | None = None,
    ) -> tuple[PracticeItem, bool, Question, PracticeSession]:
        session = await self._get_session_for_update(session_id)
        if not session:
            raise ValueError("Session not found")
        if session.ended_at:
            raise ValueError("Session already ended")
        if question_id not in session.question_ids:
            raise ValueError("Question does not belong to this session")

        question = await self._get_question(question_id)
        if not question:
            raise ValueError("Question not found")
        await self._ensure_not_answered(session_id, question_id)

        is_correct = self._judge_answer(question, user_answer)
        emotion_value = await self.emotion.detect_facial(frame_base64, student_id=session.student_id)

        now = _utcnow()
        item = PracticeItem(
            practice_session_id=session_id,
            student_id=session.student_id,
            question_id=question_id,
            user_answer=user_answer,
            sequence=await self._get_next_sequence(session_id),
            is_correct=is_correct,
            is_skipped=False,
            started_at=now,
            ended_at=now,
            duration_seconds=duration_seconds,
            emotion=describe_value(emotion_value) if emotion_value is not None else None,
            emotion_value=emotion_value,
        )
        self.db.add(item)
        await self.db.flush()

        # 原子递增，避免并发 lost-update
        await self.db.execute(
            update(PracticeSession)
            .where(PracticeSession.id == session_id)
            .values(
                correct_count=PracticeSession.correct_count + (1 if is_correct else 0),
                wrong_count=PracticeSession.wrong_count + (0 if is_correct else 1),
            )
        )
        await self.db.refresh(session)

        await self._update_knowledge_summary(session.student_id, question, is_correct)
        return item, is_correct, question, session

    async def skip_question(
        self,
        session_id: int,
        question_id: int,
        duration_seconds: int | None = None,
    ) -> tuple[PracticeItem, PracticeSession]:
        session = await self._get_session_for_update(session_id)
        if not session:
            raise ValueError("Session not found")
        if session.ended_at:
            raise ValueError("Session already ended")
        if question_id not in session.question_ids:
            raise ValueError("Question does not belong to this session")
        await self._ensure_not_answered(session_id, question_id)

        now = _utcnow()
        item = PracticeItem(
            practice_session_id=session_id,
            student_id=session.student_id,
            question_id=question_id,
            user_answer="",
            sequence=await self._get_next_sequence(session_id),
            is_correct=False,
            is_skipped=True,
            started_at=now,
            ended_at=now,
            duration_seconds=duration_seconds,
        )
        self.db.add(item)
        await self.db.flush()

        await self.db.execute(
            update(PracticeSession)
            .where(PracticeSession.id == session_id)
            .values(skip_count=PracticeSession.skip_count + 1)
        )
        await self.db.refresh(session)
        return item, session

    async def star_question(
        self, session_id: int, question_id: int, starred: bool,
    ) -> PracticeSession:
        session = await self._get_session_for_update(session_id)
        if not session:
            raise ValueError("Session not found")
        if question_id not in session.question_ids:
            raise ValueError("Question does not belong to this session")

        ids = list(session.starred_question_ids)
        if starred and question_id not in ids:
            ids.append(question_id)
        elif not starred and question_id in ids:
            ids.remove(question_id)
        session.starred_question_ids = ids
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def end_session(self, session_id: int) -> PracticeSession:
        session = await self._get_session(session_id)
        if not session:
            raise ValueError("Session not found")
        if session.ended_at:
            raise ValueError("Session already ended")

        session.ended_at = _utcnow()
        await self.db.flush()

        await self._skip_unanswered(session)
        await self._flow_back_emotion(session)
        from app.services.recognition import RecognitionService  # 局部导入避免循环
        await RecognitionService(self.db).on_practice_end(session)
        from app.services.badges import BadgeService
        await BadgeService(self.db).evaluate(session.student_id)
        await self.db.refresh(session)
        return session

    async def get_session(self, session_id: int) -> PracticeSession | None:
        result = await self.db.execute(
            select(PracticeSession)
            .where(PracticeSession.id == session_id)
            .options(selectinload(PracticeSession.items))
        )
        session = result.scalar_one_or_none()
        if not session:
            return None

        question_ids = set(session.question_ids) | {it.question_id for it in session.items}
        q_by_id: dict[int, Question] = {}
        if question_ids:
            q_result = await self.db.execute(
                select(Question)
                .where(Question.id.in_(question_ids))
                .options(selectinload(Question.knowledge_points))
            )
            q_by_id = {q.id: q for q in q_result.scalars().all()}
        for item in session.items:
            item.question = q_by_id.get(item.question_id)
        session.questions = [q_by_id[qid] for qid in session.question_ids if qid in q_by_id]
        return session

    async def list_sessions_by_student(
        self,
        student_id: int,
        limit: int,
        offset: int,
    ) -> list[PracticeSession]:
        result = await self.db.execute(
            select(PracticeSession)
            .where(PracticeSession.student_id == student_id)
            .order_by(
                PracticeSession.started_at.desc(),
                PracticeSession.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # 内部辅助方法
    # ------------------------------------------------------------------

    async def _validate_knowledge_points(self, ids: list[int]) -> None:
        if not ids:
            raise ValueError("knowledge_point_ids must not be empty")
        result = await self.db.execute(
            select(Section.id).where(Section.id.in_(ids))
        )
        found = set(result.scalars().all())
        missing = sorted(set(ids) - found)
        if missing:
            raise ValueError(f"Knowledge point ids not found: {missing}")

    async def _ensure_not_answered(self, session_id: int, question_id: int) -> None:
        existing = await self.db.execute(
            select(PracticeItem.id).where(
                PracticeItem.practice_session_id == session_id,
                PracticeItem.question_id == question_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise ValueError("Question already answered in this session")

    async def _get_session(self, session_id: int) -> PracticeSession | None:
        result = await self.db.execute(
            select(PracticeSession).where(PracticeSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def _get_session_for_update(self, session_id: int) -> PracticeSession | None:
        result = await self.db.execute(
            select(PracticeSession)
            .where(PracticeSession.id == session_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def _get_question(self, question_id: int) -> Question | None:
        result = await self.db.execute(
            select(Question)
            .where(Question.id == question_id)
            .options(selectinload(Question.knowledge_points))
        )
        return result.scalar_one_or_none()

    async def _get_next_sequence(self, session_id: int) -> int:
        result = await self.db.execute(
            select(func.max(PracticeItem.sequence))
            .where(PracticeItem.practice_session_id == session_id)
        )
        max_seq = result.scalar()
        return 0 if max_seq is None else max_seq + 1

    @staticmethod
    def _question_filter(
        knowledge_point_ids: list[int],
        difficulty_range: list[str],
        question_types: list[str] | None,
    ):
        subq = (
            select(question_knowledge_point.c.question_id)
            .where(question_knowledge_point.c.section_id.in_(knowledge_point_ids))
            .scalar_subquery()
        )
        stmt = select(Question).where(
            Question.difficulty.in_([Difficulty(d) for d in difficulty_range]),
            Question.id.in_(subq),
        )
        if question_types:
            stmt = stmt.where(Question.type.in_([QuestionType(t) for t in question_types]))
        return stmt

    async def _draw_questions(
        self,
        knowledge_point_ids: list[int],
        difficulty_range: list[str],
        question_types: list[str] | None,
        total_count: int,
    ) -> list[Question]:
        stmt = (
            self._question_filter(knowledge_point_ids, difficulty_range, question_types)
            .options(selectinload(Question.knowledge_points))
            .order_by(func.random())
            .limit(total_count)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    def _judge_answer(self, question: Question, user_answer: str) -> bool:
        correct = (question.answer or "").strip()
        user = (user_answer or "").strip()
        if not correct or not user:
            return False

        if question.type == QuestionType.MULTIPLE_CHOICE:
            correct_set = {c.upper() for c in re.findall(r"[A-Za-z]", correct)}
            user_set = {c.upper() for c in re.findall(r"[A-Za-z]", user)}
            return bool(correct_set) and correct_set == user_set

        if question.type == QuestionType.SINGLE_CHOICE:
            return correct.upper() == user.upper()

        # 填空/简答/计算：忽略前后空白与大小写
        return correct.lower() == user.lower()

    async def _update_knowledge_summary(
        self,
        student_id: int,
        question: Question,
        is_correct: bool,
    ) -> None:
        section_ids = [kp.id for kp in question.knowledge_points]
        if not section_ids:
            return

        existing_result = await self.db.execute(
            select(StudentKnowledgeSummary)
            .where(
                StudentKnowledgeSummary.student_id == student_id,
                StudentKnowledgeSummary.section_id.in_(section_ids),
            )
        )
        existing_by_section = {
            s.section_id: s for s in existing_result.scalars().all()
        }

        now = _utcnow()
        for section_id in section_ids:
            summary = existing_by_section.get(section_id)
            if summary:
                summary.total_practice_count += 1
                if is_correct:
                    summary.correct_count += 1
                summary.last_practice_at = now
            else:
                self.db.add(
                    StudentKnowledgeSummary(
                        student_id=student_id,
                        section_id=section_id,
                        mastery_level=0.0,
                        correct_count=1 if is_correct else 0,
                        total_practice_count=1,
                        total_teaching_count=0,
                        last_practice_at=now,
                        last_teaching_at=None,
                    )
                )

        await self.db.flush()

    async def _skip_unanswered(self, session: PracticeSession) -> None:
        """结束时把没做的题补成跳过记录，总结页与 skip_count 才一致"""
        done = set((await self.db.execute(
            select(PracticeItem.question_id).where(PracticeItem.practice_session_id == session.id)
        )).scalars().all())
        remaining = [qid for qid in session.question_ids if qid not in done]
        if not remaining:
            return
        seq = await self._get_next_sequence(session.id)
        now = session.ended_at or _utcnow()
        for i, qid in enumerate(remaining):
            self.db.add(PracticeItem(
                practice_session_id=session.id, student_id=session.student_id, question_id=qid,
                user_answer="", sequence=seq + i, is_correct=False, is_skipped=True,
                started_at=now, ended_at=now,
            ))
        await self.db.execute(
            update(PracticeSession)
            .where(PracticeSession.id == session.id)
            .values(skip_count=PracticeSession.skip_count + len(remaining))
        )
        await self.db.flush()
        await self.db.refresh(session)

    async def _flow_back_emotion(self, session: PracticeSession) -> None:
        """练习结束：作答题的面部情绪均值回流到涉及的知识点"""
        result = await self.db.execute(
            select(PracticeItem).where(
                PracticeItem.practice_session_id == session.id,
                PracticeItem.is_skipped.is_(False),
                PracticeItem.emotion_value.is_not(None),
            )
        )
        values = [it.emotion_value for it in result.scalars().all()]
        if not values:
            return
        section_result = await self.db.execute(
            select(question_knowledge_point.c.section_id)
            .where(question_knowledge_point.c.question_id.in_(session.question_ids))
            .distinct()
        )
        section_ids = list(section_result.scalars().all())
        try:
            await self.emotion.flow_back(
                self.db,
                student_id=session.student_id,
                section_ids=section_ids,
                session_id=session.id,
                instant_values=values,
                start_time=session.started_at,
                end_time=session.ended_at or _utcnow(),
                mode=EmotionMode.PRACTICE,
            )
        except Exception:
            logger.exception("Practice emotion flow-back failed for session %s", session.id)
