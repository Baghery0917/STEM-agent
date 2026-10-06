from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.external.teaching_strategy import StrategyResult
from app.models.emotion import EmotionLog, EmotionMode, StudentKpEmotion
from app.models.student import Gender, Student
from app.models.student_knowledge_summary import StudentKnowledgeSummary
from app.models.teaching import (
    MessageRole,
    MessageType,
    PipelineStatus,
    SessionEndReason,
    TeachingMessage,
    TeachingSession,
    TeachingSessionStatus,
)
from app.schemas.chapter import ChapterCreate
from app.schemas.section import SectionCreate
from app.schemas.student import StudentCreate
from app.schemas.volume import VolumeCreate
from app.services.chapter import ChapterService
from app.services.emotion import EmotionService, InstantEmotion
from app.services.section import SectionService
from app.services.student import StudentService
from app.services.teaching import TeachingService, _DEFAULT_ASSISTANT_REPLY, _utcnow
from app.services.volume import VolumeService


@pytest.fixture
def mock_llm_chat():
    """Mock LLM chat responses for different scenarios."""
    def _mock(*args, **kwargs):
        # Default return for unrecognized prompts
        return "This is a mock teaching response."
    return _mock


def patch_text_emotion(value: float | None = None):
    # 文本情绪分类与策略 fallback 共用同一个 LLMClient；固定它，chat side_effect 顺序才可预测
    return patch.object(EmotionService, "_detect_text", new=AsyncMock(return_value=value))


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


class TestTeachingService:
    """Tests for TeachingService"""

    async def test_start_session(self, db_session: AsyncSession):
        """Golden path: start a teaching session"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session, section_title="Algebra Basics")

        with (
            patch("app.services.teaching.LLMClient") as MockLLM,
            patch("app.services.question.LLMClient") as MockQuestionLLM,
            patch_text_emotion(),
        ):
            mock_llm = MockLLM.return_value
            mock_llm.chat = AsyncMock(side_effect=[
                f'[{{"section_id": {section.id}, "confidence": 0.9}}]',
                "Strategy: Guided discovery\nReason: Student needs scaffolding.",
                "Welcome! Let's explore this problem together.",
            ])
            mock_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            mock_q_llm = MockQuestionLLM.return_value
            mock_q_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            service = TeachingService(db_session)
            session = await service.start_session(
                student_id=student.id,
                question_content="What is x in 2x + 3 = 7?",
            )

            assert session.id is not None
            assert session.student_id == student.id
            assert session.status == TeachingSessionStatus.ACTIVE
            assert session.strategy is not None

            # Verify all message types were created
            message_types = [m.message_type for m in session.messages]
            assert MessageType.QUESTION_SUBMIT in message_types
            assert MessageType.LLM_ANALYSIS in message_types
            assert MessageType.STUDENT_DATA in message_types
            assert MessageType.STRATEGY in message_types
            assert MessageType.REFERENCE_SEARCH in message_types
            assert MessageType.CHAT in message_types

            # Verify chat message is from assistant
            chat_msgs = [m for m in session.messages if m.message_type == MessageType.CHAT]
            assert len(chat_msgs) == 1
            assert chat_msgs[0].role == MessageRole.ASSISTANT

    async def test_chat_in_session(self, db_session: AsyncSession):
        """Golden path: continue a teaching session with chat"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)

        with (
            patch("app.services.teaching.LLMClient") as MockLLM,
            patch("app.services.question.LLMClient") as MockQuestionLLM,
            patch_text_emotion(),
        ):
            mock_llm = MockLLM.return_value
            mock_llm.chat = AsyncMock(side_effect=[
                f'[{{"section_id": {section.id}, "confidence": 0.9}}]',
                "Strategy: Guided discovery\nReason: Test.",
                "Welcome! Let's explore.",
                "Strategy: Follow-up\nReason: Test.",
                "Good question! Let's think about it...",
            ])
            mock_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            mock_q_llm = MockQuestionLLM.return_value
            mock_q_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            service = TeachingService(db_session)
            session = await service.start_session(
                student_id=student.id,
                question_content="What is 2+2?",
            )

            assistant_msg, _ = await service.chat(
                session_id=session.id,
                user_message="I don't understand.",
            )

            assert assistant_msg.role == MessageRole.ASSISTANT
            assert assistant_msg.message_type == MessageType.CHAT

            # Verify chat messages in DB (1 initial assistant + 1 user + 1 new assistant = 3)
            result = await db_session.execute(
                select(TeachingMessage)
                .where(
                    TeachingMessage.session_id == session.id,
                    TeachingMessage.message_type == MessageType.CHAT,
                )
            )
            all_msgs = list(result.scalars().all())
            assert len(all_msgs) == 3

    async def test_end_session_updates_knowledge_summary(self, db_session: AsyncSession):
        """Golden path: end session updates existing knowledge summary"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)

        # Pre-create a knowledge summary record
        summary = StudentKnowledgeSummary(
            student_id=student.id,
            section_id=section.id,
            mastery_level=0.3,
            correct_count=5,
            total_practice_count=10,
            total_teaching_count=2,
        )
        db_session.add(summary)
        await db_session.flush()

        with (
            patch("app.services.teaching.LLMClient") as MockLLM,
            patch("app.services.question.LLMClient") as MockQuestionLLM,
            patch_text_emotion(),
        ):
            mock_llm = MockLLM.return_value
            mock_llm.chat = AsyncMock(side_effect=[
                f'[{{"section_id": {section.id}, "confidence": 0.9}}]',
                "Strategy: Test\nReason: Test.",
                "Welcome!",
            ])
            mock_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            mock_q_llm = MockQuestionLLM.return_value
            mock_q_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            service = TeachingService(db_session)
            session = await service.start_session(
                student_id=student.id,
                question_content="Test question",
            )

            ended = await service.end_session(
                session_id=session.id,
                mastery_level_delta=0.1,
            )

        assert ended.status == TeachingSessionStatus.COMPLETED
        assert ended.ended_at is not None

        # Refresh summary from DB
        await db_session.refresh(summary)
        assert summary.total_teaching_count == 3
        assert summary.mastery_level == pytest.approx(0.4)
        assert summary.last_teaching_at is not None

    async def test_end_session_creates_new_summary(self, db_session: AsyncSession):
        """Golden path: end session creates new summary when none exists"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)

        with (
            patch("app.services.teaching.LLMClient") as MockLLM,
            patch("app.services.question.LLMClient") as MockQuestionLLM,
            patch_text_emotion(),
        ):
            mock_llm = MockLLM.return_value
            mock_llm.chat = AsyncMock(side_effect=[
                f'[{{"section_id": {section.id}, "confidence": 0.9}}]',
                "Strategy: Test\nReason: Test.",
                "Welcome!",
            ])
            mock_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            mock_q_llm = MockQuestionLLM.return_value
            mock_q_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            service = TeachingService(db_session)
            session = await service.start_session(
                student_id=student.id,
                question_content="Test question",
            )

            await service.end_session(session_id=session.id)

        # Verify new summary was created
        result = await db_session.execute(
            select(StudentKnowledgeSummary)
            .where(
                StudentKnowledgeSummary.student_id == student.id,
                StudentKnowledgeSummary.section_id == section.id,
            )
        )
        new_summary = result.scalar_one_or_none()
        assert new_summary is not None
        assert new_summary.total_teaching_count == 1
        assert new_summary.mastery_level == 0.0

    async def test_cancel_session(self, db_session: AsyncSession):
        """Golden path: cancel a session"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)

        with (
            patch("app.services.teaching.LLMClient") as MockLLM,
            patch("app.services.question.LLMClient") as MockQuestionLLM,
            patch_text_emotion(),
        ):
            mock_llm = MockLLM.return_value
            mock_llm.chat = AsyncMock(side_effect=[
                f'[{{"section_id": {section.id}, "confidence": 0.9}}]',
                "Strategy: Test\nReason: Test.",
                "Welcome!",
            ])
            mock_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            mock_q_llm = MockQuestionLLM.return_value
            mock_q_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            service = TeachingService(db_session)
            session = await service.start_session(
                student_id=student.id,
                question_content="Test question",
            )

            cancelled = await service.cancel_session(session_id=session.id)

        assert cancelled.status == TeachingSessionStatus.CANCELLED
        assert cancelled.ended_at is not None

    async def test_chat_inactive_session_fails(self, db_session: AsyncSession):
        """Error case: chat in a completed session raises ValueError"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)

        with (
            patch("app.services.teaching.LLMClient") as MockLLM,
            patch("app.services.question.LLMClient") as MockQuestionLLM,
            patch_text_emotion(),
        ):
            mock_llm = MockLLM.return_value
            mock_llm.chat = AsyncMock(side_effect=[
                f'[{{"section_id": {section.id}, "confidence": 0.9}}]',
                "Strategy: Test\nReason: Test.",
                "Welcome!",
            ])
            mock_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            mock_q_llm = MockQuestionLLM.return_value
            mock_q_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            service = TeachingService(db_session)
            session = await service.start_session(
                student_id=student.id,
                question_content="Test question",
            )
            await service.end_session(session_id=session.id)

            with pytest.raises(ValueError, match="not active"):
                await service.chat(session_id=session.id, user_message="Hello?")

    async def test_get_session_not_found(self, db_session: AsyncSession):
        """Error case: get non-existent session returns None"""
        service = TeachingService(db_session)
        result = await service.get_session(99999)
        assert result is None

    async def test_start_session_with_strategy_fallback(self, db_session: AsyncSession):
        """Golden path: external strategy service unavailable, fallback to LLM works"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)

        with (
            patch("app.services.teaching.LLMClient") as MockLLM,
            patch("app.services.teaching.TeachingStrategyClient") as MockStrategy,
            patch("app.services.question.LLMClient") as MockQuestionLLM,
            patch_text_emotion(),
        ):
            mock_llm = MockLLM.return_value
            mock_llm.chat = AsyncMock(side_effect=[
                f'[{{"section_id": {section.id}, "confidence": 0.9}}]',
                "Strategy: Socratic questioning\nReason: Student benefits from guided discovery.",
                "Welcome! Let's explore this together.",
            ])
            mock_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            mock_strategy = MockStrategy.return_value
            mock_strategy.is_configured.return_value = False

            mock_q_llm = MockQuestionLLM.return_value
            mock_q_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            service = TeachingService(db_session)
            session = await service.start_session(
                student_id=student.id,
                question_content="Test question",
            )

        assert session.strategy is not None
        assert "Socratic" in session.strategy

    async def test_list_sessions_by_student_only_returns_own(self, db_session: AsyncSession):
        """Golden path: list_sessions_by_student scopes to one student and orders by created_at DESC"""
        student_a = await create_test_student(db_session, name="A")
        student_b = await create_test_student(db_session, name="B")

        base = datetime(2026, 4, 1, 10, 0, 0)
        # Insert B's session between A's two to verify scoping + ordering
        s_a_old = TeachingSession(
            student_id=student_a.id,
            status=TeachingSessionStatus.ACTIVE,
            created_at=base,
            updated_at=base,
        )
        s_b = TeachingSession(
            student_id=student_b.id,
            status=TeachingSessionStatus.ACTIVE,
            created_at=base.replace(hour=11),
            updated_at=base.replace(hour=11),
        )
        s_a_new = TeachingSession(
            student_id=student_a.id,
            status=TeachingSessionStatus.ACTIVE,
            created_at=base.replace(hour=12),
            updated_at=base.replace(hour=12),
        )
        db_session.add_all([s_a_old, s_b, s_a_new])
        await db_session.flush()

        service = TeachingService(db_session)
        rows = await service.list_sessions_by_student(
            student_id=student_a.id, limit=20, offset=0,
        )

        assert [r[0].id for r in rows] == [s_a_new.id, s_a_old.id]
        assert all(r[0].student_id == student_a.id for r in rows)

    async def test_list_sessions_by_student_pagination(self, db_session: AsyncSession):
        """Edge case: limit/offset paginate correctly"""
        student = await create_test_student(db_session)

        base = datetime(2026, 4, 1, 9, 0, 0)
        sessions = []
        for i in range(5):
            s = TeachingSession(
                student_id=student.id,
                status=TeachingSessionStatus.ACTIVE,
                created_at=base.replace(hour=9 + i),
                updated_at=base.replace(hour=9 + i),
            )
            sessions.append(s)
        db_session.add_all(sessions)
        await db_session.flush()

        service = TeachingService(db_session)

        page1 = await service.list_sessions_by_student(
            student_id=student.id, limit=2, offset=0,
        )
        page2 = await service.list_sessions_by_student(
            student_id=student.id, limit=2, offset=2,
        )
        page3 = await service.list_sessions_by_student(
            student_id=student.id, limit=2, offset=4,
        )

        # Ordered newest-first; sessions[4] is newest, sessions[0] is oldest
        assert [r[0].id for r in page1] == [sessions[4].id, sessions[3].id]
        assert [r[0].id for r in page2] == [sessions[2].id, sessions[1].id]
        assert [r[0].id for r in page3] == [sessions[0].id]

        # Boundary: offset past end returns empty list
        empty = await service.list_sessions_by_student(
            student_id=student.id, limit=10, offset=100,
        )
        assert empty == []

    async def test_list_sessions_preview_and_message_count(self, db_session: AsyncSession):
        """Golden path: preview uses QUESTION_SUBMIT with smallest sequence; message_count = total messages"""
        student = await create_test_student(db_session)
        session = TeachingSession(
            student_id=student.id,
            status=TeachingSessionStatus.ACTIVE,
        )
        db_session.add(session)
        await db_session.flush()

        # Earlier non-QUESTION_SUBMIT + a QUESTION_SUBMIT at seq=1 + a later QUESTION_SUBMIT at seq=3.
        # Preview must pick seq=1 (the smallest-sequence QUESTION_SUBMIT), not seq=0 or seq=3.
        db_session.add_all([
            TeachingMessage(
                session_id=session.id, role=MessageRole.SYSTEM,
                content="analysis text", message_type=MessageType.LLM_ANALYSIS,
                sequence=0,
            ),
            TeachingMessage(
                session_id=session.id, role=MessageRole.USER,
                content="What is 2+2?", message_type=MessageType.QUESTION_SUBMIT,
                sequence=1,
            ),
            TeachingMessage(
                session_id=session.id, role=MessageRole.ASSISTANT,
                content="hello", message_type=MessageType.CHAT,
                sequence=2,
            ),
            TeachingMessage(
                session_id=session.id, role=MessageRole.USER,
                content="second submit (should be ignored)",
                message_type=MessageType.QUESTION_SUBMIT, sequence=3,
            ),
        ])
        await db_session.flush()

        service = TeachingService(db_session)
        rows = await service.list_sessions_by_student(
            student_id=student.id, limit=10, offset=0,
        )

        assert len(rows) == 1
        _, preview, message_count = rows[0]
        assert preview == "What is 2+2?"
        assert message_count == 4

    async def test_list_sessions_preview_truncation_and_newlines(
        self, db_session: AsyncSession,
    ):
        """Edge case: preview replaces newlines with space, truncates to 60 chars with trailing …"""
        student = await create_test_student(db_session)

        exact_60 = "a" * 60  # boundary: exactly 60 chars → no truncation
        over_60 = "b" * 61    # one over → truncated
        multi_line = "line1\nline2 " + "c" * 80  # newline stripped, then truncated

        base = datetime(2026, 4, 1, 10, 0, 0)
        cases = [
            ("exact", exact_60, base.replace(hour=10)),
            ("over", over_60, base.replace(hour=11)),
            ("multi", multi_line, base.replace(hour=12)),
        ]
        session_by_label: dict[str, TeachingSession] = {}
        for label, content, created in cases:
            s = TeachingSession(
                student_id=student.id,
                status=TeachingSessionStatus.ACTIVE,
                created_at=created,
                updated_at=created,
            )
            db_session.add(s)
            await db_session.flush()
            db_session.add(TeachingMessage(
                session_id=s.id, role=MessageRole.USER,
                content=content, message_type=MessageType.QUESTION_SUBMIT,
                sequence=0,
            ))
            session_by_label[label] = s
        await db_session.flush()

        service = TeachingService(db_session)
        rows = await service.list_sessions_by_student(
            student_id=student.id, limit=10, offset=0,
        )
        preview_by_id = {r[0].id: r[1] for r in rows}

        assert preview_by_id[session_by_label["exact"].id] == exact_60
        assert preview_by_id[session_by_label["over"].id] == "b" * 60 + "…"

        multi_preview = preview_by_id[session_by_label["multi"].id]
        assert "\n" not in multi_preview
        assert multi_preview.endswith("…")
        assert len(multi_preview) == 61  # 60 chars + ellipsis
        assert multi_preview.startswith("line1 line2 ")

    async def test_list_sessions_preview_none_when_no_question_submit(
        self, db_session: AsyncSession,
    ):
        """Edge case: preview is None when no QUESTION_SUBMIT message exists"""
        student = await create_test_student(db_session)
        session = TeachingSession(
            student_id=student.id,
            status=TeachingSessionStatus.ACTIVE,
        )
        db_session.add(session)
        await db_session.flush()

        db_session.add(TeachingMessage(
            session_id=session.id, role=MessageRole.SYSTEM,
            content="just analysis", message_type=MessageType.LLM_ANALYSIS,
            sequence=0,
        ))
        await db_session.flush()

        service = TeachingService(db_session)
        rows = await service.list_sessions_by_student(
            student_id=student.id, limit=10, offset=0,
        )

        assert len(rows) == 1
        _, preview, message_count = rows[0]
        assert preview is None
        assert message_count == 1

    async def test_list_sessions_empty_student(self, db_session: AsyncSession):
        """Edge case: student with no sessions returns empty list"""
        student = await create_test_student(db_session)
        service = TeachingService(db_session)
        rows = await service.list_sessions_by_student(
            student_id=student.id, limit=10, offset=0,
        )
        assert rows == []

    async def test_end_session_without_mastery_delta(self, db_session: AsyncSession):
        """Edge case: end session without mastery_level_delta does not change mastery"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)

        summary = StudentKnowledgeSummary(
            student_id=student.id,
            section_id=section.id,
            mastery_level=0.5,
            total_teaching_count=1,
        )
        db_session.add(summary)
        await db_session.flush()

        with (
            patch("app.services.teaching.LLMClient") as MockLLM,
            patch("app.services.question.LLMClient") as MockQuestionLLM,
            patch_text_emotion(),
        ):
            mock_llm = MockLLM.return_value
            mock_llm.chat = AsyncMock(side_effect=[
                f'[{{"section_id": {section.id}, "confidence": 0.9}}]',
                "Strategy: Test\nReason: Test.",
                "Welcome!",
            ])
            mock_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            mock_q_llm = MockQuestionLLM.return_value
            mock_q_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            service = TeachingService(db_session)
            session = await service.start_session(
                student_id=student.id,
                question_content="Test question",
            )

            await service.end_session(session_id=session.id)

        await db_session.refresh(summary)
        assert summary.mastery_level == pytest.approx(0.5)
        assert summary.total_teaching_count == 2

    async def test_create_session_shell_returns_pending_with_question_submit(
        self, db_session: AsyncSession,
    ):
        """Shell creation: returns PENDING session + 1 QUESTION_SUBMIT message; no LLM calls."""
        student = await create_test_student(db_session)

        with patch("app.services.teaching.LLMClient") as MockLLM:
            mock_llm = MockLLM.return_value
            mock_llm.chat = AsyncMock()
            mock_llm.embed = AsyncMock()

            service = TeachingService(db_session)
            session = await service.create_session_shell(
                student_id=student.id,
                question_content="hello",
            )

            assert session.pipeline_status == PipelineStatus.PENDING
            assert session.status == TeachingSessionStatus.ACTIVE

            result = await db_session.execute(
                select(TeachingMessage)
                .where(TeachingMessage.session_id == session.id)
            )
            messages = list(result.scalars().all())
            assert len(messages) == 1
            assert messages[0].message_type == MessageType.QUESTION_SUBMIT
            assert messages[0].sequence == 0
            assert messages[0].content == "hello"

            mock_llm.chat.assert_not_called()

    async def test_run_pipeline_transitions_to_done(self, db_session: AsyncSession):
        """Pipeline golden path: shell → run_pipeline ends in DONE with all message types."""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session, section_title="Algebra")

        with (
            patch("app.services.teaching.LLMClient") as MockLLM,
            patch("app.services.question.LLMClient") as MockQuestionLLM,
            patch_text_emotion(),
        ):
            mock_llm = MockLLM.return_value
            mock_llm.chat = AsyncMock(side_effect=[
                f'[{{"section_id": {section.id}, "confidence": 0.9}}]',
                "Strategy: Guided discovery\nReason: Student needs scaffolding.",
                "Here is a guided explanation.",
            ])
            mock_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            mock_q_llm = MockQuestionLLM.return_value
            mock_q_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            service = TeachingService(db_session)
            session = await service.create_session_shell(
                student_id=student.id,
                question_content="question",
            )
            await service.run_pipeline(session.id, "question")

        refreshed = await db_session.execute(
            select(TeachingSession).where(TeachingSession.id == session.id)
        )
        session_row = refreshed.scalar_one()
        assert session_row.pipeline_status == PipelineStatus.DONE

        msg_result = await db_session.execute(
            select(TeachingMessage)
            .where(TeachingMessage.session_id == session.id)
        )
        messages = list(msg_result.scalars().all())
        message_types = {m.message_type for m in messages}
        assert MessageType.QUESTION_SUBMIT in message_types
        assert MessageType.LLM_ANALYSIS in message_types
        assert MessageType.STUDENT_DATA in message_types
        assert MessageType.STRATEGY in message_types
        assert MessageType.REFERENCE_SEARCH in message_types
        assert MessageType.CHAT in message_types

        chat_msgs = [m for m in messages if m.message_type == MessageType.CHAT]
        assert len(chat_msgs) == 1
        assert chat_msgs[0].role == MessageRole.ASSISTANT

    async def test_run_pipeline_marks_failed_on_uncaught_exception(
        self, db_session: AsyncSession,
    ):
        """Pipeline failure: uncaught exception sets FAILED, writes fallback reply, re-raises."""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)

        with (
            patch("app.services.teaching.LLMClient") as MockLLM,
            patch("app.services.question.LLMClient") as MockQuestionLLM,
            patch.object(
                TeachingService,
                "_get_student_knowledge_data",
                new=AsyncMock(side_effect=RuntimeError("boom")),
            ),
        ):
            mock_llm = MockLLM.return_value
            mock_llm.chat = AsyncMock(side_effect=[
                f'[{{"section_id": {section.id}, "confidence": 0.9}}]',
            ])
            mock_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            mock_q_llm = MockQuestionLLM.return_value
            mock_q_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            service = TeachingService(db_session)
            session = await service.create_session_shell(
                student_id=student.id,
                question_content="question",
            )

            with pytest.raises(RuntimeError, match="boom"):
                await service.run_pipeline(session.id, "question")

        refreshed = await db_session.execute(
            select(TeachingSession).where(TeachingSession.id == session.id)
        )
        session_row = refreshed.scalar_one()
        assert session_row.pipeline_status == PipelineStatus.FAILED

        msg_result = await db_session.execute(
            select(TeachingMessage)
            .where(TeachingMessage.session_id == session.id)
        )
        messages = list(msg_result.scalars().all())
        fallback = [
            m for m in messages
            if m.role == MessageRole.ASSISTANT
            and m.message_type == MessageType.CHAT
            and m.content == _DEFAULT_ASSISTANT_REPLY
        ]
        assert len(fallback) == 1

    async def test_service_chat_stream_persists_and_streams(
        self, db_session: AsyncSession,
    ):
        """Streaming chat: yields deltas in order and persists user + aggregated assistant messages."""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session, section_title="Arithmetic")

        with (
            patch("app.services.teaching.LLMClient") as MockLLM,
            patch("app.services.question.LLMClient") as MockQuestionLLM,
            patch_text_emotion(),
        ):
            mock_llm = MockLLM.return_value
            mock_llm.chat = AsyncMock(side_effect=[
                f'[{{"section_id": {section.id}, "confidence": 0.9}}]',
                "Strategy: Guided\nReason: Test.",
                "Welcome!",
            ])
            mock_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            mock_q_llm = MockQuestionLLM.return_value
            mock_q_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            service = TeachingService(db_session)
            session = await service.start_session(
                student_id=student.id,
                question_content="Let's begin.",
            )

        service2 = TeachingService(db_session)

        async def fake_stream(*args, **kwargs):
            for t in ["1+", "1=", "2"]:
                yield t

        service2.llm.chat_stream = fake_stream
        service2.llm.chat = AsyncMock(return_value="Strategy: Guided\nReason: Test.")

        session_id = session.id

        acc: list[str] = []
        with patch_text_emotion():
            async for d in service2.chat_stream(session_id, "what is 1+1?"):
                acc.append(d)

        assert acc == ["1+", "1=", "2"]
        assert "".join(acc) == "1+1=2"

        await db_session.commit()
        db_session.expire_all()

        result = await db_session.execute(
            select(TeachingMessage)
            .where(
                TeachingMessage.session_id == session_id,
                TeachingMessage.message_type == MessageType.CHAT,
            )
            .order_by(TeachingMessage.sequence)
        )
        chat_msgs = list(result.scalars().all())

        # initial welcome assistant + new user + new aggregated assistant
        assert len(chat_msgs) == 3
        last_two = chat_msgs[-2:]
        assert last_two[0].role == MessageRole.USER
        assert last_two[0].content == "what is 1+1?"
        assert last_two[0].message_type == MessageType.CHAT
        assert last_two[1].role == MessageRole.ASSISTANT
        assert last_two[1].content == "1+1=2"
        assert last_two[1].message_type == MessageType.CHAT

    async def test_strategy_refreshed_every_turn(self, db_session: AsyncSession):
        """Per-turn strategy: start + one chat → 2 STRATEGY messages, session.strategy is the latest"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)

        with (
            patch("app.services.teaching.LLMClient") as MockLLM,
            patch("app.services.teaching.TeachingStrategyClient") as MockStrategy,
            patch("app.services.question.LLMClient") as MockQuestionLLM,
            patch_text_emotion(),
        ):
            mock_llm = MockLLM.return_value
            mock_llm.chat = AsyncMock(side_effect=[
                f'[{{"section_id": {section.id}, "confidence": 0.9}}]',
                "Welcome!",
                "Let's continue.",
            ])
            mock_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            mock_strategy = MockStrategy.return_value
            mock_strategy.is_configured.return_value = True
            mock_strategy.get_strategy = AsyncMock(side_effect=[
                StrategyResult(strategy="Worked example first", reason="Cold start"),
                StrategyResult(strategy="Socratic questioning", reason="Student engaged"),
            ])

            mock_q_llm = MockQuestionLLM.return_value
            mock_q_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            service = TeachingService(db_session)
            session = await service.start_session(
                student_id=student.id,
                question_content="Why does ice float?",
            )
            assert session.strategy == "Worked example first"

            await service.chat(session_id=session.id, user_message="Is it about density?")

        assert mock_strategy.get_strategy.await_count == 2
        second_call = mock_strategy.get_strategy.await_args_list[1].kwargs
        assert second_call["message"] == "Is it about density?"
        assert second_call["session_id"] == session.id

        await db_session.refresh(session)
        assert session.strategy == "Socratic questioning"

        result = await db_session.execute(
            select(TeachingMessage)
            .where(
                TeachingMessage.session_id == session.id,
                TeachingMessage.message_type == MessageType.STRATEGY,
            )
            .order_by(TeachingMessage.sequence)
        )
        strategy_msgs = list(result.scalars().all())
        assert len(strategy_msgs) == 2
        assert "Worked example first" in strategy_msgs[0].content
        assert "Socratic questioning" in strategy_msgs[1].content

    async def test_instant_emotion_persisted_on_user_message(self, db_session: AsyncSession):
        """Instant emotion: facial 4.0 + text 3.0 → emotion_value 3.6 on the QUESTION_SUBMIT message"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)

        with (
            patch("app.services.teaching.LLMClient") as MockLLM,
            patch("app.services.question.LLMClient") as MockQuestionLLM,
            patch.object(
                EmotionService,
                "detect_instant",
                new=AsyncMock(return_value=InstantEmotion(facial=4.0, text=3.0)),
            ),
        ):
            mock_llm = MockLLM.return_value
            mock_llm.chat = AsyncMock(side_effect=[
                f'[{{"section_id": {section.id}, "confidence": 0.9}}]',
                "Strategy: Test\nReason: Test.",
                "Welcome!",
            ])
            mock_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            mock_q_llm = MockQuestionLLM.return_value
            mock_q_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            service = TeachingService(db_session)
            session = await service.start_session(
                student_id=student.id,
                question_content="I keep getting this wrong",
                frame_base64="ZmFrZQ==",
            )

        user_msgs = [m for m in session.messages if m.role == MessageRole.USER]
        assert len(user_msgs) == 1
        assert user_msgs[0].message_type == MessageType.QUESTION_SUBMIT
        assert user_msgs[0].facial_value == 4.0
        assert user_msgs[0].text_value == 3.0
        assert user_msgs[0].emotion_value == pytest.approx(3.6)

        system_msgs = [m for m in session.messages if m.role == MessageRole.SYSTEM]
        assert all(m.emotion_value is None for m in system_msgs)

    async def test_strategy_mcp_failure_falls_back_to_llm(self, db_session: AsyncSession):
        """MCP configured but raising → strategy comes from LLM fallback, pipeline still DONE"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)

        with (
            patch("app.services.teaching.LLMClient") as MockLLM,
            patch("app.services.teaching.TeachingStrategyClient") as MockStrategy,
            patch("app.services.question.LLMClient") as MockQuestionLLM,
            patch_text_emotion(),
        ):
            mock_llm = MockLLM.return_value
            mock_llm.chat = AsyncMock(side_effect=[
                f'[{{"section_id": {section.id}, "confidence": 0.9}}]',
                "Strategy: LLM fallback plan\nReason: MCP down.",
                "Welcome!",
            ])
            mock_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            mock_strategy = MockStrategy.return_value
            mock_strategy.is_configured.return_value = True
            mock_strategy.get_strategy = AsyncMock(side_effect=RuntimeError("MCP unreachable"))

            mock_q_llm = MockQuestionLLM.return_value
            mock_q_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            service = TeachingService(db_session)
            session = await service.start_session(
                student_id=student.id,
                question_content="Test question",
            )

        mock_strategy.get_strategy.assert_awaited_once()
        assert session.strategy == "LLM fallback plan"
        assert session.pipeline_status == PipelineStatus.DONE
        chat_msgs = [m for m in session.messages if m.message_type == MessageType.CHAT]
        assert len(chat_msgs) == 1
        assert chat_msgs[0].content == "Welcome!"

    async def test_end_session_flows_emotion_back_with_ema(self, db_session: AsyncSession):
        """Flow back: first session writes 4.0/count 1 + TEACHING log; second session EMA → 3.4/count 2"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)

        with (
            patch("app.services.teaching.LLMClient") as MockLLM,
            patch("app.services.question.LLMClient") as MockQuestionLLM,
            patch_text_emotion(4.0),
        ):
            mock_llm = MockLLM.return_value
            mock_llm.chat = AsyncMock(side_effect=[
                f'[{{"section_id": {section.id}, "confidence": 0.9}}]',
                "Strategy: Test\nReason: Test.",
                "Welcome!",
                "Strategy: Test\nReason: Test.",
                "Keep going.",
            ])
            mock_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            mock_q_llm = MockQuestionLLM.return_value
            mock_q_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            service = TeachingService(db_session)
            session = await service.start_session(
                student_id=student.id,
                question_content="This is too hard",
            )
            await service.chat(session_id=session.id, user_message="I still don't get it")
            ended = await service.end_session(session_id=session.id)

        assert ended.end_reason == SessionEndReason.USER
        result = await db_session.execute(
            select(TeachingMessage.emotion_value)
            .where(
                TeachingMessage.session_id == session.id,
                TeachingMessage.role == MessageRole.USER,
            )
            .order_by(TeachingMessage.sequence)
        )
        assert list(result.scalars().all()) == [4.0, 4.0]

        result = await db_session.execute(
            select(StudentKpEmotion).where(
                StudentKpEmotion.student_id == student.id,
                StudentKpEmotion.section_id == section.id,
            )
        )
        kp_emotion = result.scalar_one()
        assert kp_emotion.emotion_value == pytest.approx(4.0)
        assert kp_emotion.sample_count == 1

        result = await db_session.execute(
            select(EmotionLog).where(EmotionLog.student_id == student.id)
        )
        logs = list(result.scalars().all())
        assert len(logs) == 1
        assert logs[0].mode == EmotionMode.TEACHING
        assert logs[0].session_id == session.id
        assert logs[0].section_id == section.id
        assert logs[0].emotion_value == pytest.approx(4.0)
        assert logs[0].start_time is not None
        assert logs[0].end_time is not None

        with (
            patch("app.services.teaching.LLMClient") as MockLLM,
            patch("app.services.question.LLMClient") as MockQuestionLLM,
            patch_text_emotion(2.0),
        ):
            mock_llm = MockLLM.return_value
            mock_llm.chat = AsyncMock(side_effect=[
                f'[{{"section_id": {section.id}, "confidence": 0.9}}]',
                "Strategy: Test\nReason: Test.",
                "Welcome back!",
            ])
            mock_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            mock_q_llm = MockQuestionLLM.return_value
            mock_q_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            service = TeachingService(db_session)
            second = await service.start_session(
                student_id=student.id,
                question_content="I think I got it now",
            )
            await service.end_session(session_id=second.id)

        await db_session.refresh(kp_emotion)
        assert kp_emotion.emotion_value == pytest.approx(4.0 * 0.7 + 2.0 * 0.3)
        assert kp_emotion.sample_count == 2

        result = await db_session.execute(
            select(func.count(EmotionLog.id)).where(EmotionLog.student_id == student.id)
        )
        assert result.scalar() == 2

    async def test_end_session_without_emotion_writes_no_history(self, db_session: AsyncSession):
        """Edge case: no instant emotion values → no StudentKpEmotion/EmotionLog rows, no error"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)

        with (
            patch("app.services.teaching.LLMClient") as MockLLM,
            patch("app.services.question.LLMClient") as MockQuestionLLM,
            patch_text_emotion(),
        ):
            mock_llm = MockLLM.return_value
            mock_llm.chat = AsyncMock(side_effect=[
                f'[{{"section_id": {section.id}, "confidence": 0.9}}]',
                "Strategy: Test\nReason: Test.",
                "Welcome!",
            ])
            mock_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            mock_q_llm = MockQuestionLLM.return_value
            mock_q_llm.embed = AsyncMock(return_value=[[0.0] * 1024])

            service = TeachingService(db_session)
            session = await service.start_session(
                student_id=student.id,
                question_content="Test question",
            )
            ended = await service.end_session(session_id=session.id)

        assert ended.status == TeachingSessionStatus.COMPLETED
        assert ended.end_reason == SessionEndReason.USER
        assert all(m.emotion_value is None for m in ended.messages)

        result = await db_session.execute(
            select(func.count(StudentKpEmotion.id)).where(
                StudentKpEmotion.student_id == student.id,
            )
        )
        assert result.scalar() == 0
        result = await db_session.execute(
            select(func.count(EmotionLog.id)).where(EmotionLog.student_id == student.id)
        )
        assert result.scalar() == 0

    async def test_end_idle_sessions_only_ends_stale_ones(self, db_session: AsyncSession):
        """Idle sweep: only the DONE session whose last message is older than cutoff gets COMPLETED/IDLE"""
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)

        stale = TeachingSession(
            student_id=student.id,
            status=TeachingSessionStatus.ACTIVE,
            pipeline_status=PipelineStatus.DONE,
        )
        recent = TeachingSession(
            student_id=student.id,
            status=TeachingSessionStatus.ACTIVE,
            pipeline_status=PipelineStatus.DONE,
        )
        pending = TeachingSession(
            student_id=student.id,
            status=TeachingSessionStatus.ACTIVE,
            pipeline_status=PipelineStatus.PENDING,
        )
        db_session.add_all([stale, recent, pending])
        await db_session.flush()

        old_time = _utcnow() - timedelta(hours=2)
        analysis = f"Identified knowledge points:\n- {section.id}: {section.title}"
        db_session.add_all([
            TeachingMessage(
                session_id=stale.id, role=MessageRole.USER, content="old question",
                message_type=MessageType.QUESTION_SUBMIT, sequence=0,
                emotion_value=3.0, text_value=3.0,
                created_at=old_time, updated_at=old_time,
            ),
            TeachingMessage(
                session_id=stale.id, role=MessageRole.SYSTEM, content=analysis,
                message_type=MessageType.LLM_ANALYSIS, sequence=1,
                created_at=old_time, updated_at=old_time,
            ),
            TeachingMessage(
                session_id=stale.id, role=MessageRole.ASSISTANT, content="old reply",
                message_type=MessageType.CHAT, sequence=2,
                created_at=old_time, updated_at=old_time,
            ),
            TeachingMessage(
                session_id=recent.id, role=MessageRole.USER, content="fresh question",
                message_type=MessageType.QUESTION_SUBMIT, sequence=0,
            ),
            TeachingMessage(
                session_id=pending.id, role=MessageRole.USER, content="still running",
                message_type=MessageType.QUESTION_SUBMIT, sequence=0,
                created_at=old_time, updated_at=old_time,
            ),
        ])
        await db_session.flush()

        service = TeachingService(db_session)
        ended = await service.end_idle_sessions(idle_minutes=30)

        assert ended == [stale.id]

        db_session.expire_all()
        result = await db_session.execute(
            select(TeachingSession).where(TeachingSession.id.in_([stale.id, recent.id, pending.id]))
        )
        by_id = {s.id: s for s in result.scalars().all()}
        assert by_id[stale.id].status == TeachingSessionStatus.COMPLETED
        assert by_id[stale.id].end_reason == SessionEndReason.IDLE
        assert by_id[stale.id].ended_at is not None
        assert by_id[recent.id].status == TeachingSessionStatus.ACTIVE
        assert by_id[recent.id].end_reason is None
        assert by_id[pending.id].status == TeachingSessionStatus.ACTIVE

        result = await db_session.execute(
            select(StudentKpEmotion).where(
                StudentKpEmotion.student_id == student.id,
                StudentKpEmotion.section_id == section.id,
            )
        )
        kp_emotion = result.scalar_one()
        assert kp_emotion.emotion_value == pytest.approx(3.0)
        assert kp_emotion.sample_count == 1

        again = await service.end_idle_sessions(idle_minutes=30)
        assert again == []


class TestTeachingRouter:
    """Tests for teaching API endpoints"""

    async def test_list_sessions_endpoint(self, client, db_session: AsyncSession):
        """Golden path: GET /sessions returns scoped, shaped list with preview + message_count"""
        student = await create_test_student(db_session)
        other = await create_test_student(db_session, name="Other")

        base = datetime(2026, 4, 1, 10, 0, 0)
        s_old = TeachingSession(
            student_id=student.id,
            status=TeachingSessionStatus.ACTIVE,
            strategy="Socratic",
            created_at=base,
            updated_at=base,
        )
        s_new = TeachingSession(
            student_id=student.id,
            status=TeachingSessionStatus.COMPLETED,
            strategy="Guided",
            created_at=base.replace(hour=12),
            updated_at=base.replace(hour=12),
        )
        s_other = TeachingSession(
            student_id=other.id,
            status=TeachingSessionStatus.ACTIVE,
            created_at=base.replace(hour=11),
            updated_at=base.replace(hour=11),
        )
        db_session.add_all([s_old, s_new, s_other])
        await db_session.flush()

        db_session.add_all([
            TeachingMessage(
                session_id=s_new.id, role=MessageRole.USER,
                content="Newest question", message_type=MessageType.QUESTION_SUBMIT,
                sequence=0,
            ),
            TeachingMessage(
                session_id=s_new.id, role=MessageRole.ASSISTANT,
                content="hello", message_type=MessageType.CHAT, sequence=1,
            ),
            TeachingMessage(
                session_id=s_old.id, role=MessageRole.SYSTEM,
                content="analysis only", message_type=MessageType.LLM_ANALYSIS,
                sequence=0,
            ),
        ])
        await db_session.flush()

        response = await client.get(
            "/api/v1/teaching/sessions",
            params={"student_id": student.id, "limit": 10, "offset": 0},
        )

        assert response.status_code == 200
        data = response.json()
        assert [row["id"] for row in data] == [s_new.id, s_old.id]

        newest = data[0]
        assert newest["student_id"] == student.id
        assert newest["status"] == "completed"
        assert newest["strategy"] == "Guided"
        assert newest["preview"] == "Newest question"
        assert newest["message_count"] == 2

        oldest = data[1]
        assert oldest["preview"] is None
        assert oldest["message_count"] == 1

    async def test_list_sessions_endpoint_pagination(
        self, client, db_session: AsyncSession,
    ):
        """Edge case: GET /sessions honors limit & offset"""
        student = await create_test_student(db_session)
        base = datetime(2026, 4, 1, 9, 0, 0)
        sessions = []
        for i in range(3):
            s = TeachingSession(
                student_id=student.id,
                status=TeachingSessionStatus.ACTIVE,
                created_at=base.replace(hour=9 + i),
                updated_at=base.replace(hour=9 + i),
            )
            sessions.append(s)
        db_session.add_all(sessions)
        await db_session.flush()

        response = await client.get(
            "/api/v1/teaching/sessions",
            params={"student_id": student.id, "limit": 1, "offset": 1},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        # sessions[2] newest, sessions[1] second, sessions[0] oldest → offset=1 gives middle
        assert data[0]["id"] == sessions[1].id
