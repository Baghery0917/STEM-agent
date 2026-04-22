import pytest
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.practice import PracticeItem, PracticeMode, PracticeSession
from app.models.question import Difficulty, Question, QuestionType, question_knowledge_point
from app.models.student import Gender, Student
from app.models.student_knowledge_summary import StudentKnowledgeSummary
from app.schemas.chapter import ChapterCreate
from app.schemas.section import SectionCreate
from app.schemas.student import StudentCreate
from app.schemas.volume import VolumeCreate
from app.services.chapter import ChapterService
from app.services.practice import PracticeService
from app.services.section import SectionService
from app.services.student import StudentService
from app.services.volume import VolumeService


async def create_test_student(db: AsyncSession, name: str = "Test Student"):
    service = StudentService()
    return await service.create(db, StudentCreate(name=name, gender=Gender.MALE))


async def create_test_volume(db: AsyncSession):
    service = VolumeService(db)
    return await service.create(VolumeCreate(title="Test Volume"))


async def create_test_chapter(db: AsyncSession, volume_id: int):
    service = ChapterService(db)
    return await service.create(ChapterCreate(volume_id=volume_id, title="Test Chapter"))


async def create_test_section(db: AsyncSession, chapter_id: int, title: str = "Test Section"):
    service = SectionService(db)
    return await service.create(SectionCreate(chapter_id=chapter_id, title=title))


async def create_knowledge_chain(db: AsyncSession, section_title: str = "Test Section"):
    volume = await create_test_volume(db)
    chapter = await create_test_chapter(db, volume.id)
    section = await create_test_section(db, chapter.id, title=section_title)
    return volume, chapter, section


async def create_test_question(
    db: AsyncSession,
    section: "Section",
    content: str = "What is 2+2?",
    answer: str = "4",
    difficulty: Difficulty = Difficulty.EASY,
) -> Question:
    question = Question(
        type=QuestionType.SINGLE_CHOICE,
        content=content,
        answer=answer,
        difficulty=difficulty,
    )
    db.add(question)
    await db.flush()
    await db.refresh(question)

    await db.execute(
        question_knowledge_point.insert().values(
            question_id=question.id,
            section_id=section.id,
        )
    )
    await db.flush()
    return question


class TestPracticeServiceFocused:
    """Tests for PracticeService focused mode"""

    @pytest.mark.asyncio
    async def test_start_focused_session(self, db_session: AsyncSession):
        """Golden path: start a focused practice session"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        question = await create_test_question(
            db_session, section, content="Q1", answer="A",
        )

        service = PracticeService(db_session)
        session, first_question = await service.start_focused_session(
            student_id=student.id,
            knowledge_point_ids=[section.id],
            difficulty_range=["easy"],
            total_count=3,
        )

        assert session.id is not None
        assert session.mode == PracticeMode.FOCUSED
        assert session.student_id == student.id
        assert session.total_count == 3
        assert session.correct_count == 0
        assert session.wrong_count == 0
        assert session.skip_count == 0
        assert first_question is not None
        assert first_question.id == question.id

    @pytest.mark.asyncio
    async def test_submit_answer_correct(self, db_session: AsyncSession):
        """Golden path: submit correct answer in focused mode"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        q1 = await create_test_question(db_session, section, content="Q1", answer="A")
        q2 = await create_test_question(db_session, section, content="Q2", answer="B")

        service = PracticeService(db_session)
        session, _ = await service.start_focused_session(
            student_id=student.id,
            knowledge_point_ids=[section.id],
            difficulty_range=["easy"],
            total_count=2,
        )

        item, is_correct, next_q = await service.submit_answer(
            session_id=session.id,
            question_id=q1.id,
            user_answer="A",
        )

        assert is_correct is True
        assert item.is_correct is True
        assert item.is_skipped is False
        assert item.user_answer == "A"
        assert next_q is not None

        await db_session.refresh(session)
        assert session.correct_count == 1
        assert session.wrong_count == 0

    @pytest.mark.asyncio
    async def test_submit_answer_wrong(self, db_session: AsyncSession):
        """Golden path: submit wrong answer in focused mode"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        q1 = await create_test_question(db_session, section, content="Q1", answer="A")
        q2 = await create_test_question(db_session, section, content="Q2", answer="B")

        service = PracticeService(db_session)
        session, _ = await service.start_focused_session(
            student_id=student.id,
            knowledge_point_ids=[section.id],
            difficulty_range=["easy"],
            total_count=2,
        )

        item, is_correct, next_q = await service.submit_answer(
            session_id=session.id,
            question_id=q1.id,
            user_answer="X",
        )

        assert is_correct is False
        assert item.is_correct is False
        assert next_q is not None

        await db_session.refresh(session)
        assert session.correct_count == 0
        assert session.wrong_count == 1

    @pytest.mark.asyncio
    async def test_focused_no_next_question_after_all_answered(self, db_session: AsyncSession):
        """Edge case: after answering all focused questions, no next question"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        q1 = await create_test_question(db_session, section, content="Q1", answer="A")

        service = PracticeService(db_session)
        session, _ = await service.start_focused_session(
            student_id=student.id,
            knowledge_point_ids=[section.id],
            difficulty_range=["easy"],
            total_count=1,
        )

        item, is_correct, next_q = await service.submit_answer(
            session_id=session.id,
            question_id=q1.id,
            user_answer="A",
        )

        assert is_correct is True
        assert next_q is None

    @pytest.mark.asyncio
    async def test_end_session_focused(self, db_session: AsyncSession):
        """Golden path: end a focused session"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        await create_test_question(db_session, section, content="Q1", answer="A")

        service = PracticeService(db_session)
        session, _ = await service.start_focused_session(
            student_id=student.id,
            knowledge_point_ids=[section.id],
            difficulty_range=["easy"],
            total_count=1,
        )

        ended = await service.end_session(session_id=session.id)

        assert ended.ended_at is not None
        assert ended.total_count == 1

    @pytest.mark.asyncio
    async def test_get_session(self, db_session: AsyncSession):
        """Golden path: get session with items"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        q1 = await create_test_question(db_session, section, content="Q1", answer="A")

        service = PracticeService(db_session)
        session, _ = await service.start_focused_session(
            student_id=student.id,
            knowledge_point_ids=[section.id],
            difficulty_range=["easy"],
            total_count=1,
        )
        await service.submit_answer(
            session_id=session.id,
            question_id=q1.id,
            user_answer="A",
        )

        result = await service.get_session(session_id=session.id)

        assert result is not None
        assert result.id == session.id
        assert len(result.items) == 1
        assert result.items[0].question_id == q1.id

    @pytest.mark.asyncio
    async def test_get_session_items_include_question(
        self, db_session: AsyncSession,
    ):
        """Golden path: get_session attaches full Question on each item"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        q1 = await create_test_question(
            db_session, section, content="Q1 content", answer="A",
        )
        q1.analysis = "Because A is correct."
        await db_session.flush()

        service = PracticeService(db_session)
        session, _ = await service.start_focused_session(
            student_id=student.id,
            knowledge_point_ids=[section.id],
            difficulty_range=["easy"],
            total_count=1,
        )
        await service.submit_answer(
            session_id=session.id,
            question_id=q1.id,
            user_answer="A",
        )

        result = await service.get_session(session_id=session.id)

        assert result is not None
        assert len(result.items) == 1
        attached = result.items[0].question
        assert attached is not None
        assert attached.id == q1.id
        assert attached.content == "Q1 content"
        assert attached.answer == "A"
        assert attached.analysis == "Because A is correct."

    @pytest.mark.asyncio
    async def test_submit_answer_updates_knowledge_summary(self, db_session: AsyncSession):
        """Golden path: submitting answer creates knowledge summary"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        q1 = await create_test_question(db_session, section, content="Q1", answer="A")

        service = PracticeService(db_session)
        session, _ = await service.start_focused_session(
            student_id=student.id,
            knowledge_point_ids=[section.id],
            difficulty_range=["easy"],
            total_count=1,
        )
        await service.submit_answer(
            session_id=session.id,
            question_id=q1.id,
            user_answer="A",
        )

        result = await db_session.execute(
            select(StudentKnowledgeSummary)
            .where(
                StudentKnowledgeSummary.student_id == student.id,
                StudentKnowledgeSummary.section_id == section.id,
            )
        )
        summary = result.scalar_one_or_none()

        assert summary is not None
        assert summary.correct_count == 1
        assert summary.total_practice_count == 1
        assert summary.mastery_level == 0.0


class TestPracticeServiceGeneral:
    """Tests for PracticeService general mode"""

    @pytest.mark.asyncio
    async def test_start_general_session(self, db_session: AsyncSession):
        """Golden path: start a general practice session"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        question = await create_test_question(
            db_session, section, content="Q1", answer="A",
        )

        service = PracticeService(db_session)
        session, first_question = await service.start_general_session(
            student_id=student.id,
            knowledge_point_ids=[section.id],
            difficulty_range=["easy"],
        )

        assert session.id is not None
        assert session.mode == PracticeMode.GENERAL
        assert session.total_count == 0
        assert first_question is not None
        assert first_question.id == question.id

    @pytest.mark.asyncio
    async def test_submit_answer_general(self, db_session: AsyncSession):
        """Golden path: submit answer in general mode"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        q1 = await create_test_question(db_session, section, content="Q1", answer="A")

        service = PracticeService(db_session)
        session, _ = await service.start_general_session(
            student_id=student.id,
            knowledge_point_ids=[section.id],
            difficulty_range=["easy"],
        )

        item, is_correct, next_q = await service.submit_answer(
            session_id=session.id,
            question_id=q1.id,
            user_answer="A",
            emotion="happy",
        )

        assert is_correct is True
        assert item.emotion == "happy"
        assert next_q is None

        await db_session.refresh(session)
        assert session.correct_count == 1
        assert session.wrong_count == 0

    @pytest.mark.asyncio
    async def test_skip_question_general(self, db_session: AsyncSession):
        """Golden path: skip question in general mode"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        q1 = await create_test_question(db_session, section, content="Q1", answer="A")
        q2 = await create_test_question(db_session, section, content="Q2", answer="B")

        service = PracticeService(db_session)
        session, _ = await service.start_general_session(
            student_id=student.id,
            knowledge_point_ids=[section.id],
            difficulty_range=["easy"],
        )

        next_q = await service.skip_question(
            session_id=session.id,
            question_id=q1.id,
        )

        assert next_q is not None

        await db_session.refresh(session)
        assert session.skip_count == 1
        assert q1.id in session.skipped_question_ids

        # No PracticeItem created for skipped question
        result = await db_session.execute(
            select(PracticeItem)
            .where(
                PracticeItem.practice_session_id == session.id,
                PracticeItem.question_id == q1.id,
            )
        )
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_next_question_general(self, db_session: AsyncSession):
        """Golden path: get next question in general mode"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        q1 = await create_test_question(db_session, section, content="Q1", answer="A")
        q2 = await create_test_question(db_session, section, content="Q2", answer="B")

        service = PracticeService(db_session)
        session, first_q = await service.start_general_session(
            student_id=student.id,
            knowledge_point_ids=[section.id],
            difficulty_range=["easy"],
        )

        # Answer first question to exclude it
        await service.submit_answer(
            session_id=session.id,
            question_id=first_q.id,
            user_answer="A" if first_q.answer == "A" else "B",
        )

        next_q = await service.next_question(session_id=session.id)

        assert next_q is not None
        assert next_q.id != first_q.id

    @pytest.mark.asyncio
    async def test_end_session_general(self, db_session: AsyncSession):
        """Golden path: end general session records total_count"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        q1 = await create_test_question(db_session, section, content="Q1", answer="A")

        service = PracticeService(db_session)
        session, _ = await service.start_general_session(
            student_id=student.id,
            knowledge_point_ids=[section.id],
            difficulty_range=["easy"],
        )
        await service.submit_answer(
            session_id=session.id,
            question_id=q1.id,
            user_answer="A",
        )

        ended = await service.end_session(session_id=session.id)

        assert ended.ended_at is not None
        assert ended.total_count == 1


class TestPracticeServiceErrors:
    """Tests for error and boundary cases"""

    @pytest.mark.asyncio
    async def test_start_focused_no_matching_questions(self, db_session: AsyncSession):
        """Error case: no questions match criteria"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)

        service = PracticeService(db_session)
        with pytest.raises(ValueError, match="No questions match the given criteria"):
            await service.start_focused_session(
                student_id=student.id,
                knowledge_point_ids=[section.id],
                difficulty_range=["easy"],
                total_count=3,
            )

    @pytest.mark.asyncio
    async def test_submit_answer_to_ended_session(self, db_session: AsyncSession):
        """Error case: submit answer to ended session"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        q1 = await create_test_question(db_session, section, content="Q1", answer="A")

        service = PracticeService(db_session)
        session, _ = await service.start_focused_session(
            student_id=student.id,
            knowledge_point_ids=[section.id],
            difficulty_range=["easy"],
            total_count=1,
        )
        await service.end_session(session_id=session.id)

        with pytest.raises(ValueError, match="Session already ended"):
            await service.submit_answer(
                session_id=session.id,
                question_id=q1.id,
                user_answer="A",
            )

    @pytest.mark.asyncio
    async def test_skip_question_in_focused_mode(self, db_session: AsyncSession):
        """Error case: skip question in focused mode is not allowed"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        q1 = await create_test_question(db_session, section, content="Q1", answer="A")

        service = PracticeService(db_session)
        session, _ = await service.start_focused_session(
            student_id=student.id,
            knowledge_point_ids=[section.id],
            difficulty_range=["easy"],
            total_count=1,
        )

        with pytest.raises(ValueError, match="Skip is only allowed in general mode"):
            await service.skip_question(
                session_id=session.id,
                question_id=q1.id,
            )

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, db_session: AsyncSession):
        """Error case: get non-existent session returns None"""
        service = PracticeService(db_session)
        result = await service.get_session(99999)
        assert result is None

    @pytest.mark.asyncio
    async def test_end_session_already_ended(self, db_session: AsyncSession):
        """Error case: end an already ended session"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        await create_test_question(db_session, section, content="Q1", answer="A")

        service = PracticeService(db_session)
        session, _ = await service.start_focused_session(
            student_id=student.id,
            knowledge_point_ids=[section.id],
            difficulty_range=["easy"],
            total_count=1,
        )
        await service.end_session(session_id=session.id)

        with pytest.raises(ValueError, match="Session already ended"):
            await service.end_session(session_id=session.id)

    @pytest.mark.asyncio
    async def test_skip_question_already_ended(self, db_session: AsyncSession):
        """Error case: skip question in ended session"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        q1 = await create_test_question(db_session, section, content="Q1", answer="A")

        service = PracticeService(db_session)
        session, _ = await service.start_general_session(
            student_id=student.id,
            knowledge_point_ids=[section.id],
            difficulty_range=["easy"],
        )
        await service.end_session(session_id=session.id)

        with pytest.raises(ValueError, match="Session already ended"):
            await service.skip_question(
                session_id=session.id,
                question_id=q1.id,
            )


class TestPracticeServiceListSessions:
    """Tests for PracticeService.list_sessions_by_student"""

    @pytest.mark.asyncio
    async def test_list_sessions_scopes_to_student_and_orders_desc(
        self, db_session: AsyncSession,
    ):
        """Golden path: returns only the student's sessions, ordered by started_at DESC"""
        student_a = await create_test_student(db_session, name="A")
        student_b = await create_test_student(db_session, name="B")

        base = datetime(2026, 4, 1, 10, 0, 0)
        # Interleave so filtering + ordering are both exercised
        s_a_old = PracticeSession(
            mode=PracticeMode.FOCUSED,
            knowledge_point_ids=[],
            difficulty_range=[Difficulty.EASY],
            student_id=student_a.id,
            total_count=0,
            started_at=base,
        )
        s_b = PracticeSession(
            mode=PracticeMode.FOCUSED,
            knowledge_point_ids=[],
            difficulty_range=[Difficulty.EASY],
            student_id=student_b.id,
            total_count=0,
            started_at=base.replace(hour=11),
        )
        s_a_new = PracticeSession(
            mode=PracticeMode.GENERAL,
            knowledge_point_ids=[],
            difficulty_range=[Difficulty.EASY],
            student_id=student_a.id,
            total_count=0,
            started_at=base.replace(hour=12),
        )
        db_session.add_all([s_a_old, s_b, s_a_new])
        await db_session.flush()

        service = PracticeService(db_session)
        sessions = await service.list_sessions_by_student(
            student_id=student_a.id, limit=20, offset=0,
        )

        assert [s.id for s in sessions] == [s_a_new.id, s_a_old.id]
        assert all(s.student_id == student_a.id for s in sessions)

    @pytest.mark.asyncio
    async def test_list_sessions_pagination(self, db_session: AsyncSession):
        """Edge case: limit/offset paginate correctly, including empty boundary"""
        student = await create_test_student(db_session)

        base = datetime(2026, 4, 1, 9, 0, 0)
        sessions = []
        for i in range(5):
            s = PracticeSession(
                mode=PracticeMode.FOCUSED,
                knowledge_point_ids=[],
                difficulty_range=[Difficulty.EASY],
                student_id=student.id,
                total_count=0,
                started_at=base.replace(hour=9 + i),
            )
            sessions.append(s)
        db_session.add_all(sessions)
        await db_session.flush()

        service = PracticeService(db_session)

        page1 = await service.list_sessions_by_student(
            student_id=student.id, limit=2, offset=0,
        )
        page2 = await service.list_sessions_by_student(
            student_id=student.id, limit=2, offset=2,
        )
        page3 = await service.list_sessions_by_student(
            student_id=student.id, limit=2, offset=4,
        )

        assert [s.id for s in page1] == [sessions[4].id, sessions[3].id]
        assert [s.id for s in page2] == [sessions[2].id, sessions[1].id]
        assert [s.id for s in page3] == [sessions[0].id]

        empty = await service.list_sessions_by_student(
            student_id=student.id, limit=10, offset=100,
        )
        assert empty == []

    @pytest.mark.asyncio
    async def test_list_sessions_empty_student(self, db_session: AsyncSession):
        """Edge case: student with no sessions returns empty list"""
        student = await create_test_student(db_session)
        service = PracticeService(db_session)
        sessions = await service.list_sessions_by_student(
            student_id=student.id, limit=10, offset=0,
        )
        assert sessions == []


class TestPracticeRouter:
    """Tests for practice API endpoints"""

    @pytest.mark.asyncio
    async def test_start_focused_session_endpoint(self, client, db_session: AsyncSession):
        """Golden path: POST /sessions/focused"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        await create_test_question(db_session, section, content="Q1", answer="A")

        response = await client.post(
            "/api/v1/practice/sessions/focused",
            json={
                "student_id": student.id,
                "knowledge_point_ids": [section.id],
                "difficulty_range": ["easy"],
                "total_count": 2,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["session"]["mode"] == "focused"
        assert data["session"]["total_count"] == 2
        assert data["question"]["content"] == "Q1"

    @pytest.mark.asyncio
    async def test_start_general_session_endpoint(self, client, db_session: AsyncSession):
        """Golden path: POST /sessions/general"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        await create_test_question(db_session, section, content="Q1", answer="A")

        response = await client.post(
            "/api/v1/practice/sessions/general",
            json={
                "student_id": student.id,
                "knowledge_point_ids": [section.id],
                "difficulty_range": ["easy"],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["session"]["mode"] == "general"
        assert data["session"]["total_count"] == 0

    @pytest.mark.asyncio
    async def test_submit_answer_endpoint(self, client, db_session: AsyncSession):
        """Golden path: POST /sessions/{id}/submit"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        q1 = await create_test_question(db_session, section, content="Q1", answer="A")

        service = PracticeService(db_session)
        session, _ = await service.start_focused_session(
            student_id=student.id,
            knowledge_point_ids=[section.id],
            difficulty_range=["easy"],
            total_count=1,
        )

        response = await client.post(
            f"/api/v1/practice/sessions/{session.id}/submit",
            json={
                "question_id": q1.id,
                "user_answer": "A",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_correct"] is True
        assert data["item"]["user_answer"] == "A"

    @pytest.mark.asyncio
    async def test_skip_question_endpoint(self, client, db_session: AsyncSession):
        """Golden path: POST /sessions/{id}/skip in general mode"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        q1 = await create_test_question(db_session, section, content="Q1", answer="A")

        service = PracticeService(db_session)
        session, _ = await service.start_general_session(
            student_id=student.id,
            knowledge_point_ids=[section.id],
            difficulty_range=["easy"],
        )

        response = await client.post(
            f"/api/v1/practice/sessions/{session.id}/skip",
            json={"question_id": q1.id},
        )

        assert response.status_code == 200
        data = response.json()
        assert "question" in data

    @pytest.mark.asyncio
    async def test_next_question_endpoint(self, client, db_session: AsyncSession):
        """Golden path: POST /sessions/{id}/next"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        q1 = await create_test_question(db_session, section, content="Q1", answer="A")
        q2 = await create_test_question(db_session, section, content="Q2", answer="B")

        service = PracticeService(db_session)
        session, first_q = await service.start_general_session(
            student_id=student.id,
            knowledge_point_ids=[section.id],
            difficulty_range=["easy"],
        )
        await service.submit_answer(
            session_id=session.id,
            question_id=first_q.id,
            user_answer="A" if first_q.answer == "A" else "B",
        )

        response = await client.post(
            f"/api/v1/practice/sessions/{session.id}/next",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["question"] is not None

    @pytest.mark.asyncio
    async def test_end_session_endpoint(self, client, db_session: AsyncSession):
        """Golden path: POST /sessions/{id}/end"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        await create_test_question(db_session, section, content="Q1", answer="A")

        service = PracticeService(db_session)
        session, _ = await service.start_focused_session(
            student_id=student.id,
            knowledge_point_ids=[section.id],
            difficulty_range=["easy"],
            total_count=1,
        )

        response = await client.post(
            f"/api/v1/practice/sessions/{session.id}/end",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ended_at"] is not None

    @pytest.mark.asyncio
    async def test_get_session_endpoint(self, client, db_session: AsyncSession):
        """Golden path: GET /sessions/{id}"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        q1 = await create_test_question(db_session, section, content="Q1", answer="A")

        service = PracticeService(db_session)
        session, _ = await service.start_focused_session(
            student_id=student.id,
            knowledge_point_ids=[section.id],
            difficulty_range=["easy"],
            total_count=1,
        )
        await service.submit_answer(
            session_id=session.id,
            question_id=q1.id,
            user_answer="A",
        )

        response = await client.get(
            f"/api/v1/practice/sessions/{session.id}",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session.id
        assert data["mode"] == "focused"
        assert len(data["items"]) == 1

    @pytest.mark.asyncio
    async def test_get_session_not_found_endpoint(self, client):
        """Error case: GET /sessions/{id} returns 404"""
        response = await client.get("/api/v1/practice/sessions/99999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Session not found"

    @pytest.mark.asyncio
    async def test_start_focused_no_questions_endpoint(self, client, db_session: AsyncSession):
        """Error case: POST /sessions/focused with no matching questions returns 400"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)

        response = await client.post(
            "/api/v1/practice/sessions/focused",
            json={
                "student_id": student.id,
                "knowledge_point_ids": [section.id],
                "difficulty_range": ["easy"],
                "total_count": 2,
            },
        )

        assert response.status_code == 400
        assert "No questions match the given criteria" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_skip_in_focused_mode_endpoint(self, client, db_session: AsyncSession):
        """Error case: POST /sessions/{id}/skip in focused mode returns 400"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        q1 = await create_test_question(db_session, section, content="Q1", answer="A")

        service = PracticeService(db_session)
        session, _ = await service.start_focused_session(
            student_id=student.id,
            knowledge_point_ids=[section.id],
            difficulty_range=["easy"],
            total_count=1,
        )

        response = await client.post(
            f"/api/v1/practice/sessions/{session.id}/skip",
            json={"question_id": q1.id},
        )

        assert response.status_code == 400
        assert "Skip is only allowed in general mode" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_submit_to_ended_session_endpoint(self, client, db_session: AsyncSession):
        """Error case: POST /sessions/{id}/submit after session ended returns 400"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        q1 = await create_test_question(db_session, section, content="Q1", answer="A")

        service = PracticeService(db_session)
        session, _ = await service.start_focused_session(
            student_id=student.id,
            knowledge_point_ids=[section.id],
            difficulty_range=["easy"],
            total_count=1,
        )
        await service.end_session(session_id=session.id)

        response = await client.post(
            f"/api/v1/practice/sessions/{session.id}/submit",
            json={
                "question_id": q1.id,
                "user_answer": "A",
            },
        )

        assert response.status_code == 400
        assert "Session already ended" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_sessions_endpoint(self, client, db_session: AsyncSession):
        """Golden path: GET /sessions returns only the student's rows, newest first"""
        student = await create_test_student(db_session)
        other = await create_test_student(db_session, name="Other")

        base = datetime(2026, 4, 1, 10, 0, 0)
        s_old = PracticeSession(
            mode=PracticeMode.FOCUSED,
            knowledge_point_ids=[],
            difficulty_range=[Difficulty.EASY],
            student_id=student.id,
            total_count=3,
            started_at=base,
        )
        s_new = PracticeSession(
            mode=PracticeMode.GENERAL,
            knowledge_point_ids=[],
            difficulty_range=[Difficulty.EASY],
            student_id=student.id,
            total_count=0,
            started_at=base.replace(hour=12),
        )
        s_other = PracticeSession(
            mode=PracticeMode.FOCUSED,
            knowledge_point_ids=[],
            difficulty_range=[Difficulty.EASY],
            student_id=other.id,
            total_count=0,
            started_at=base.replace(hour=11),
        )
        db_session.add_all([s_old, s_new, s_other])
        await db_session.flush()

        response = await client.get(
            "/api/v1/practice/sessions",
            params={"student_id": student.id, "limit": 10, "offset": 0},
        )

        assert response.status_code == 200
        data = response.json()
        assert [row["id"] for row in data] == [s_new.id, s_old.id]
        assert data[0]["mode"] == "general"
        assert data[1]["mode"] == "focused"
        assert all(row["student_id"] == student.id for row in data)

    @pytest.mark.asyncio
    async def test_list_sessions_endpoint_pagination(
        self, client, db_session: AsyncSession,
    ):
        """Edge case: GET /sessions honors limit & offset"""
        student = await create_test_student(db_session)
        base = datetime(2026, 4, 1, 9, 0, 0)
        sessions = []
        for i in range(3):
            s = PracticeSession(
                mode=PracticeMode.FOCUSED,
                knowledge_point_ids=[],
                difficulty_range=[Difficulty.EASY],
                student_id=student.id,
                total_count=0,
                started_at=base.replace(hour=9 + i),
            )
            sessions.append(s)
        db_session.add_all(sessions)
        await db_session.flush()

        response = await client.get(
            "/api/v1/practice/sessions",
            params={"student_id": student.id, "limit": 1, "offset": 1},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == sessions[1].id

    @pytest.mark.asyncio
    async def test_get_session_endpoint_includes_question(
        self, client, db_session: AsyncSession,
    ):
        """Golden path: GET /sessions/{id} now returns items[].question with full shape"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        q1 = await create_test_question(
            db_session, section, content="Q1 content", answer="A",
        )
        q1.analysis = "Answer is A"
        await db_session.flush()

        service = PracticeService(db_session)
        session, _ = await service.start_focused_session(
            student_id=student.id,
            knowledge_point_ids=[section.id],
            difficulty_range=["easy"],
            total_count=1,
        )
        await service.submit_answer(
            session_id=session.id,
            question_id=q1.id,
            user_answer="A",
        )

        response = await client.get(
            f"/api/v1/practice/sessions/{session.id}",
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        q = data["items"][0]["question"]
        assert q is not None
        assert q["id"] == q1.id
        assert q["content"] == "Q1 content"
        assert q["answer"] == "A"
        assert q["analysis"] == "Answer is A"
