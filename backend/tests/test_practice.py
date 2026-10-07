import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.emotion import EmotionLog, EmotionMode, StudentKpEmotion
from app.models.practice import PracticeItem, PracticeSession
from app.models.question import Difficulty, Question, QuestionType, question_knowledge_point
from app.models.student import Gender
from app.models.student_knowledge_summary import StudentKnowledgeSummary
from app.schemas.chapter import ChapterCreate
from app.schemas.section import SectionCreate
from app.schemas.student import StudentCreate
from app.schemas.volume import VolumeCreate
from app.services.chapter import ChapterService
from app.services.emotion import EmotionService
from app.services.practice import PracticeService
from app.services.section import SectionService
from app.services.student import StudentService
from app.services.volume import VolumeService


async def create_test_student(db: AsyncSession, name: str = "Test Student"):
    return await StudentService().create(db, StudentCreate(name=name, gender=Gender.MALE))


async def create_knowledge_chain(db: AsyncSession, section_title: str = "Test Section"):
    volume = await VolumeService(db).create(VolumeCreate(title="Test Volume"))
    chapter = await ChapterService(db).create(ChapterCreate(volume_id=volume.id, title="Test Chapter"))
    section = await SectionService(db).create(SectionCreate(chapter_id=chapter.id, title=section_title))
    return volume, chapter, section


async def create_test_question(
    db: AsyncSession,
    section,
    content: str = "What is 2+2?",
    answer: str = "4",
    difficulty: Difficulty = Difficulty.EASY,
    qtype: QuestionType = QuestionType.SINGLE_CHOICE,
    analysis: str | None = None,
) -> Question:
    question = Question(type=qtype, content=content, answer=answer, difficulty=difficulty, analysis=analysis)
    db.add(question)
    await db.flush()
    await db.refresh(question)
    await db.execute(
        question_knowledge_point.insert().values(question_id=question.id, section_id=section.id)
    )
    await db.flush()
    return question


class FakeEmotion(EmotionService):
    """不走外部服务：固定返回一个面部情绪值"""

    def __init__(self, value: float | None = None) -> None:
        self._value = value

    async def detect_facial(self, frame_base64, *, student_id):
        return self._value if frame_base64 else None


async def start(db, student, section, n=3, timed=False, emotion=None):
    service = PracticeService(db, emotion=FakeEmotion(emotion))
    session, questions = await service.start_session(
        student_id=student.id,
        knowledge_point_ids=[section.id],
        difficulty_range=["easy"],
        total_count=n,
        timed=timed,
    )
    return service, session, questions


class TestStartSession:
    @pytest.mark.asyncio
    async def test_draws_all_questions_up_front(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        qs = [await create_test_question(db_session, section, content=f"Q{i}", answer="A") for i in range(5)]

        _, session, questions = await start(db_session, student, section, n=3, timed=True)

        assert session.timed is True
        assert session.total_count == 3
        assert len(questions) == 3
        assert session.question_ids == [q.id for q in questions]
        assert set(session.question_ids) <= {q.id for q in qs}
        assert session.starred_question_ids == []

    @pytest.mark.asyncio
    async def test_total_count_clamped_to_available(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        await create_test_question(db_session, section, content="Q1", answer="A")
        await create_test_question(db_session, section, content="Q2", answer="A")

        _, session, questions = await start(db_session, student, section, n=10)

        assert session.total_count == 2
        assert len(questions) == 2

    @pytest.mark.asyncio
    async def test_question_type_filter(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        await create_test_question(db_session, section, content="single", answer="A")
        fill = await create_test_question(
            db_session, section, content="fill", answer="4", qtype=QuestionType.FILL_BLANK,
        )

        service = PracticeService(db_session, emotion=FakeEmotion())
        session, questions = await service.start_session(
            student_id=student.id, knowledge_point_ids=[section.id],
            difficulty_range=["easy"], total_count=5, question_types=["fill_blank"],
        )
        assert [q.id for q in questions] == [fill.id]

    @pytest.mark.asyncio
    async def test_no_matching_questions(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        service = PracticeService(db_session, emotion=FakeEmotion())
        with pytest.raises(ValueError, match="No questions match the given criteria"):
            await service.start_session(
                student_id=student.id, knowledge_point_ids=[section.id],
                difficulty_range=["easy"], total_count=3,
            )

    @pytest.mark.asyncio
    async def test_count_matching(self, db_session: AsyncSession):
        _, _, section = await create_knowledge_chain(db_session)
        await create_test_question(db_session, section, content="Q1", answer="A")
        await create_test_question(db_session, section, content="Q2", answer="A", difficulty=Difficulty.HARD)
        service = PracticeService(db_session, emotion=FakeEmotion())
        assert await service.count_matching([section.id], ["easy"]) == 1
        assert await service.count_matching([section.id], ["easy", "hard"]) == 2


class TestSubmitAndSkip:
    @pytest.mark.asyncio
    async def test_submit_correct_returns_feedback(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        await create_test_question(db_session, section, content="Q1", answer="A", analysis="because")
        await create_test_question(db_session, section, content="Q2", answer="B")

        service, session, questions = await start(db_session, student, section, n=2)
        target = questions[0]

        item, is_correct, question, updated = await service.submit_answer(
            session_id=session.id, question_id=target.id,
            user_answer=target.answer, duration_seconds=12,
        )

        assert is_correct is True
        assert question.id == target.id
        assert item.duration_seconds == 12
        assert item.is_skipped is False
        assert updated.correct_count == 1
        assert updated.wrong_count == 0

    @pytest.mark.asyncio
    async def test_submit_wrong(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        await create_test_question(db_session, section, content="Q1", answer="A")

        service, session, questions = await start(db_session, student, section, n=1)
        _, is_correct, _, updated = await service.submit_answer(
            session_id=session.id, question_id=questions[0].id, user_answer="Z",
        )
        assert is_correct is False
        assert updated.wrong_count == 1

    @pytest.mark.asyncio
    async def test_submit_records_facial_emotion(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        await create_test_question(db_session, section, content="Q1", answer="A")

        service, session, questions = await start(db_session, student, section, n=1, emotion=4.0)
        item, *_ = await service.submit_answer(
            session_id=session.id, question_id=questions[0].id,
            user_answer="A", frame_base64="data:image/jpeg;base64,AAAA",
        )
        assert item.emotion_value == 4.0
        assert item.emotion == "受挫"

    @pytest.mark.asyncio
    async def test_skip_any_question_creates_item_and_counts(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        await create_test_question(db_session, section, content="Q1", answer="A")

        service, session, questions = await start(db_session, student, section, n=1, timed=True)
        item, updated = await service.skip_question(
            session_id=session.id, question_id=questions[0].id, duration_seconds=3,
        )

        assert item.is_skipped is True
        assert item.user_answer == ""
        assert updated.skip_count == 1
        assert updated.correct_count == 0 and updated.wrong_count == 0

        # 跳过不计入学生档案
        result = await db_session.execute(
            select(StudentKnowledgeSummary).where(StudentKnowledgeSummary.student_id == student.id)
        )
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_cannot_submit_after_skip(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        await create_test_question(db_session, section, content="Q1", answer="A")

        service, session, questions = await start(db_session, student, section, n=1)
        await service.skip_question(session_id=session.id, question_id=questions[0].id)
        with pytest.raises(ValueError, match="already answered"):
            await service.submit_answer(
                session_id=session.id, question_id=questions[0].id, user_answer="A",
            )

    @pytest.mark.asyncio
    async def test_reject_question_outside_session(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        await create_test_question(db_session, section, content="Q1", answer="A")
        other = await create_test_question(db_session, section, content="Q2", answer="A")

        service, session, questions = await start(db_session, student, section, n=1)
        outside = other if other.id != questions[0].id else None
        if outside is None:
            pytest.skip("random draw picked the only alternative")
        with pytest.raises(ValueError, match="does not belong"):
            await service.submit_answer(session_id=session.id, question_id=outside.id, user_answer="A")

    @pytest.mark.asyncio
    async def test_submit_updates_knowledge_summary(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        await create_test_question(db_session, section, content="Q1", answer="A")

        service, session, questions = await start(db_session, student, section, n=1)
        await service.submit_answer(session_id=session.id, question_id=questions[0].id, user_answer="A")

        result = await db_session.execute(
            select(StudentKnowledgeSummary).where(
                StudentKnowledgeSummary.student_id == student.id,
                StudentKnowledgeSummary.section_id == section.id,
            )
        )
        summary = result.scalar_one()
        assert summary.correct_count == 1
        assert summary.total_practice_count == 1

    @pytest.mark.asyncio
    async def test_submit_to_ended_session(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        await create_test_question(db_session, section, content="Q1", answer="A")

        service, session, questions = await start(db_session, student, section, n=1)
        await service.end_session(session.id)
        with pytest.raises(ValueError, match="Session already ended"):
            await service.submit_answer(session_id=session.id, question_id=questions[0].id, user_answer="A")


class TestInstantFeedback:
    @pytest.mark.asyncio
    async def test_timed_forces_batch_grading(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        await create_test_question(db_session, section, content="Q1", answer="A")
        service = PracticeService(db_session, emotion=FakeEmotion())
        session, _ = await service.start_session(
            student_id=student.id, knowledge_point_ids=[section.id], difficulty_range=["easy"],
            total_count=1, timed=True, instant_feedback=True,
        )
        assert session.instant_feedback is False

    @pytest.mark.asyncio
    async def test_untimed_keeps_choice(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        await create_test_question(db_session, section, content="Q1", answer="A")
        service = PracticeService(db_session, emotion=FakeEmotion())
        s1, _ = await service.start_session(
            student_id=student.id, knowledge_point_ids=[section.id], difficulty_range=["easy"],
            total_count=1, timed=False, instant_feedback=False,
        )
        s2, _ = await service.start_session(
            student_id=student.id, knowledge_point_ids=[section.id], difficulty_range=["easy"],
            total_count=1, timed=False, instant_feedback=True,
        )
        assert s1.instant_feedback is False and s2.instant_feedback is True

    @pytest.mark.asyncio
    async def test_batch_grading_hides_answer_until_detail(self, client, db_session: AsyncSession, monkeypatch):
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        await create_test_question(db_session, section, content="Q1", answer="A", analysis="why")
        monkeypatch.setattr(EmotionService, "detect_facial", FakeEmotion().detect_facial)

        resp = await client.post("/api/v1/practice/sessions", json={
            "student_id": student.id, "knowledge_point_ids": [section.id],
            "difficulty_range": ["easy"], "total_count": 1, "timed": True,
        })
        sid = resp.json()["session"]["id"]; qid = resp.json()["questions"][0]["id"]
        sub = await client.post(f"/api/v1/practice/sessions/{sid}/submit", json={"question_id": qid, "user_answer": "A"})
        body = sub.json()
        assert body["is_correct"] is None and body["correct_answer"] is None and body["analysis"] is None
        assert body["item"]["is_correct"] is False
        # 后台仍按真实对错计数
        assert body["session"]["correct_count"] == 1
        await client.post(f"/api/v1/practice/sessions/{sid}/end")
        detail = (await client.get(f"/api/v1/practice/sessions/{sid}")).json()
        assert detail["items"][0]["is_correct"] is True
        assert detail["items"][0]["question"]["answer"] == "A"


class TestStarAndEnd:
    @pytest.mark.asyncio
    async def test_star_toggle(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        await create_test_question(db_session, section, content="Q1", answer="A")

        service, session, questions = await start(db_session, student, section, n=1)
        qid = questions[0].id
        s = await service.star_question(session.id, qid, True)
        assert s.starred_question_ids == [qid]
        s = await service.star_question(session.id, qid, True)
        assert s.starred_question_ids == [qid]
        s = await service.star_question(session.id, qid, False)
        assert s.starred_question_ids == []

    @pytest.mark.asyncio
    async def test_end_session_sets_ended_at_and_rejects_twice(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        await create_test_question(db_session, section, content="Q1", answer="A")

        service, session, _ = await start(db_session, student, section, n=1)
        ended = await service.end_session(session.id)
        assert ended.ended_at is not None
        with pytest.raises(ValueError, match="Session already ended"):
            await service.end_session(session.id)

    @pytest.mark.asyncio
    async def test_end_session_marks_unanswered_as_skipped(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        for i in range(3):
            await create_test_question(db_session, section, content=f"Q{i}", answer="A")

        service, session, questions = await start(db_session, student, section, n=3)
        await service.submit_answer(session_id=session.id, question_id=questions[0].id, user_answer="A")
        ended = await service.end_session(session.id)

        assert ended.skip_count == 2
        detail = await service.get_session(session.id)
        assert len(detail.items) == 3
        assert sum(1 for it in detail.items if it.is_skipped) == 2

    @pytest.mark.asyncio
    async def test_end_session_flows_practice_emotion_back(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        await create_test_question(db_session, section, content="Q1", answer="A")
        await create_test_question(db_session, section, content="Q2", answer="A")

        service, session, questions = await start(db_session, student, section, n=2, emotion=2.0)
        for q in questions:
            await service.submit_answer(
                session_id=session.id, question_id=q.id, user_answer="A",
                frame_base64="data:image/jpeg;base64,AAAA",
            )
        await service.end_session(session.id)

        hist = (await db_session.execute(
            select(StudentKpEmotion).where(StudentKpEmotion.student_id == student.id)
        )).scalar_one()
        assert hist.section_id == section.id
        assert hist.emotion_value == 2.0
        log = (await db_session.execute(
            select(EmotionLog).where(EmotionLog.student_id == student.id)
        )).scalar_one()
        assert log.mode == EmotionMode.PRACTICE
        assert log.session_id == session.id

    @pytest.mark.asyncio
    async def test_end_without_emotion_writes_no_history(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        await create_test_question(db_session, section, content="Q1", answer="A")

        service, session, questions = await start(db_session, student, section, n=1)
        await service.submit_answer(session_id=session.id, question_id=questions[0].id, user_answer="A")
        await service.end_session(session.id)
        result = await db_session.execute(select(StudentKpEmotion))
        assert result.scalars().all() == []


class TestGetAndList:
    @pytest.mark.asyncio
    async def test_get_session_returns_questions_and_items(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        await create_test_question(db_session, section, content="Q1", answer="A")
        await create_test_question(db_session, section, content="Q2", answer="B")

        service, session, questions = await start(db_session, student, section, n=2)
        await service.submit_answer(session_id=session.id, question_id=questions[0].id, user_answer="A")

        detail = await service.get_session(session.id)
        assert [q.id for q in detail.questions] == session.question_ids
        assert len(detail.items) == 1
        assert detail.items[0].question.id == questions[0].id

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, db_session: AsyncSession):
        assert await PracticeService(db_session, emotion=FakeEmotion()).get_session(9999) is None

    @pytest.mark.asyncio
    async def test_list_sessions_scoped_and_ordered(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        other = await create_test_student(db_session, name="Other")
        _, _, section = await create_knowledge_chain(db_session)
        await create_test_question(db_session, section, content="Q1", answer="A")

        _, s1, _ = await start(db_session, student, section, n=1)
        _, s2, _ = await start(db_session, student, section, n=1)
        await start(db_session, other, section, n=1)

        rows = await PracticeService(db_session, emotion=FakeEmotion()).list_sessions_by_student(
            student.id, limit=10, offset=0,
        )
        assert [r.id for r in rows] == [s2.id, s1.id]


class TestPracticeRouter:
    @pytest.mark.asyncio
    async def test_full_flow_over_http(self, client, db_session: AsyncSession, monkeypatch):
        student = await create_test_student(db_session)
        _, _, section = await create_knowledge_chain(db_session)
        await create_test_question(db_session, section, content="Q1\nA. x\nB. y", answer="A", analysis="why")
        await create_test_question(db_session, section, content="Q2", answer="B")

        monkeypatch.setattr(EmotionService, "detect_facial", FakeEmotion().detect_facial)

        match = await client.post("/api/v1/practice/match", json={
            "knowledge_point_ids": [section.id], "difficulty_range": ["easy"],
        })
        assert match.status_code == 200 and match.json()["matched_count"] == 2

        resp = await client.post("/api/v1/practice/sessions", json={
            "student_id": student.id, "knowledge_point_ids": [section.id],
            "difficulty_range": ["easy"], "total_count": 2, "timed": True,
        })
        assert resp.status_code == 201, resp.text
        body = resp.json()
        sid = body["session"]["id"]
        assert body["session"]["timed"] is True
        assert len(body["questions"]) == 2
        assert "answer" not in body["questions"][0]

        q1, q2 = body["questions"]
        sub = await client.post(f"/api/v1/practice/sessions/{sid}/submit", json={
            "question_id": q1["id"], "user_answer": "A", "duration_seconds": 20,
        })
        assert sub.status_code == 200, sub.text
        fb = sub.json()
        assert "correct_answer" in fb and fb["session"]["id"] == sid

        star = await client.post(f"/api/v1/practice/sessions/{sid}/star", json={"question_id": q2["id"]})
        assert star.status_code == 200 and star.json()["starred_question_ids"] == [q2["id"]]

        skip = await client.post(f"/api/v1/practice/sessions/{sid}/skip", json={"question_id": q2["id"]})
        assert skip.status_code == 200 and skip.json()["session"]["skip_count"] == 1

        end = await client.post(f"/api/v1/practice/sessions/{sid}/end")
        assert end.status_code == 200 and end.json()["ended_at"] is not None

        detail = await client.get(f"/api/v1/practice/sessions/{sid}")
        assert detail.status_code == 200
        d = detail.json()
        assert len(d["items"]) == 2 and len(d["questions"]) == 2
        assert d["items"][0]["question"]["answer"] == "A"

        listing = await client.get("/api/v1/practice/sessions", params={"student_id": student.id})
        assert listing.status_code == 200 and listing.json()[0]["id"] == sid
