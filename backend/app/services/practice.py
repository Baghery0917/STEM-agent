import re
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.practice import PracticeItem, PracticeMode, PracticeSession
from app.models.question import (
    Difficulty,
    Question,
    QuestionType,
    question_knowledge_point,
)
from app.models.section import Section
from app.models.student_knowledge_summary import StudentKnowledgeSummary


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class PracticeService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # 公开方法
    # ------------------------------------------------------------------

    async def start_focused_session(
        self,
        student_id: int,
        knowledge_point_ids: list[int],
        difficulty_range: list[str],
        total_count: int,
    ) -> tuple[PracticeSession, Question]:
        await self._validate_knowledge_points(knowledge_point_ids)
        session = PracticeSession(
            mode=PracticeMode.FOCUSED,
            knowledge_point_ids=knowledge_point_ids,
            difficulty_range=difficulty_range,
            student_id=student_id,
            total_count=total_count,
            started_at=_utcnow(),
        )
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)

        question = await self._draw_next_question(session)
        if not question:
            await self.db.delete(session)
            await self.db.flush()
            raise ValueError("No questions match the given criteria")

        return session, question

    async def start_general_session(
        self,
        student_id: int,
        knowledge_point_ids: list[int],
        difficulty_range: list[str],
    ) -> tuple[PracticeSession, Question]:
        await self._validate_knowledge_points(knowledge_point_ids)
        session = PracticeSession(
            mode=PracticeMode.GENERAL,
            knowledge_point_ids=knowledge_point_ids,
            difficulty_range=difficulty_range,
            student_id=student_id,
            total_count=0,
            started_at=_utcnow(),
        )
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)

        question = await self._draw_next_question(session)
        if not question:
            await self.db.delete(session)
            await self.db.flush()
            raise ValueError("No questions match the given criteria")

        return session, question

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

    async def submit_answer(
        self,
        session_id: int,
        question_id: int,
        user_answer: str,
        emotion: str | None = None,
    ) -> tuple[PracticeItem, bool, Question | None]:
        session = await self._get_session_for_update(session_id)
        if not session:
            raise ValueError("Session not found")
        if session.ended_at:
            raise ValueError("Session already ended")

        question = await self._get_question(question_id)
        if not question:
            raise ValueError("Question not found")

        existing = await self.db.execute(
            select(PracticeItem.id).where(
                PracticeItem.practice_session_id == session_id,
                PracticeItem.question_id == question_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise ValueError("Question already answered in this session")

        is_correct = self._judge_answer(question, user_answer)

        next_seq = await self._get_next_sequence(session_id)
        now = _utcnow()

        item = PracticeItem(
            practice_session_id=session_id,
            student_id=session.student_id,
            question_id=question_id,
            user_answer=user_answer,
            sequence=next_seq,
            is_correct=is_correct,
            is_skipped=False,
            started_at=now,
            ended_at=now,
            emotion=emotion,
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

        await self._update_knowledge_summary(
            session.student_id, question, is_correct,
        )

        next_question = None
        if session.mode == PracticeMode.FOCUSED:
            done_count = session.correct_count + session.wrong_count
            if done_count < session.total_count:
                next_question = await self._draw_next_question(session)

        return item, is_correct, next_question

    async def skip_question(
        self,
        session_id: int,
        question_id: int,
    ) -> Question | None:
        session = await self._get_session_for_update(session_id)
        if not session:
            raise ValueError("Session not found")
        if session.ended_at:
            raise ValueError("Session already ended")
        if session.mode != PracticeMode.GENERAL:
            raise ValueError("Skip is only allowed in general mode")

        question = await self._get_question(question_id)
        if not question:
            raise ValueError("Question not found")

        already_answered = await self.db.execute(
            select(PracticeItem.id).where(
                PracticeItem.practice_session_id == session_id,
                PracticeItem.question_id == question_id,
            )
        )
        if already_answered.scalar_one_or_none() is not None:
            raise ValueError("Question already answered in this session")

        if question_id in session.skipped_question_ids:
            await self.db.execute(
                update(PracticeSession)
                .where(PracticeSession.id == session_id)
                .values(skip_count=PracticeSession.skip_count + 1)
            )
        else:
            await self.db.execute(
                update(PracticeSession)
                .where(PracticeSession.id == session_id)
                .values(
                    skip_count=PracticeSession.skip_count + 1,
                    skipped_question_ids=func.array_append(
                        PracticeSession.skipped_question_ids, question_id,
                    ),
                )
            )
        await self.db.refresh(session)

        return await self._draw_next_question(session)

    async def next_question(
        self,
        session_id: int,
    ) -> Question | None:
        session = await self._get_session(session_id)
        if not session:
            raise ValueError("Session not found")
        if session.ended_at:
            raise ValueError("Session already ended")

        return await self._draw_next_question(session)

    async def end_session(self, session_id: int) -> PracticeSession:
        session = await self._get_session(session_id)
        if not session:
            raise ValueError("Session not found")
        if session.ended_at:
            raise ValueError("Session already ended")

        session.ended_at = _utcnow()
        # general 模式下 total_count 记录实际作答数
        if session.mode == PracticeMode.GENERAL:
            session.total_count = session.correct_count + session.wrong_count
        await self.db.flush()
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

        question_ids = [it.question_id for it in session.items]
        if question_ids:
            q_result = await self.db.execute(
                select(Question)
                .where(Question.id.in_(question_ids))
                .options(selectinload(Question.knowledge_points))
            )
            q_by_id = {q.id: q for q in q_result.scalars().all()}
            for item in session.items:
                item.question = q_by_id.get(item.question_id)
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

    async def _get_session(
        self, session_id: int,
    ) -> PracticeSession | None:
        result = await self.db.execute(
            select(PracticeSession).where(PracticeSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def _get_session_for_update(
        self, session_id: int,
    ) -> PracticeSession | None:
        result = await self.db.execute(
            select(PracticeSession)
            .where(PracticeSession.id == session_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def _get_question(self, question_id: int) -> Question | None:
        result = await self.db.execute(
            select(Question).where(Question.id == question_id)
        )
        return result.scalar_one_or_none()

    async def _get_next_sequence(self, session_id: int) -> int:
        result = await self.db.execute(
            select(func.max(PracticeItem.sequence))
            .where(PracticeItem.practice_session_id == session_id)
        )
        max_seq = result.scalar()
        return 0 if max_seq is None else max_seq + 1

    async def _draw_next_question(
        self,
        session: PracticeSession,
    ) -> Question | None:
        # 排除已作答和已跳过的题目
        result = await self.db.execute(
            select(PracticeItem.question_id)
            .where(PracticeItem.practice_session_id == session.id)
        )
        exclude_ids: list[int] = list(result.scalars().all())
        exclude_ids.extend(session.skipped_question_ids)

        stmt = (
            select(Question)
            .where(
                Question.difficulty.in_(
                    [Difficulty(d) for d in session.difficulty_range]
                ),
            )
        )

        if exclude_ids:
            stmt = stmt.where(Question.id.notin_(exclude_ids))

        subq = (
            select(question_knowledge_point.c.question_id)
            .where(
                question_knowledge_point.c.section_id.in_(
                    session.knowledge_point_ids
                ),
            )
            .scalar_subquery()
        )
        stmt = (
            stmt.where(Question.id.in_(subq))
            .options(selectinload(Question.knowledge_points))
            .order_by(func.random())
            .limit(1)
        )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

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
        result = await self.db.execute(
            select(Section.id)
            .join(
                question_knowledge_point,
                Section.id == question_knowledge_point.c.section_id,
            )
            .where(question_knowledge_point.c.question_id == question.id)
        )
        section_ids: list[int] = list(result.scalars().all())
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
