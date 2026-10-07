import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.practice import PracticeItem, PracticeSession
from app.models.recognition import ScoreEvent, StudentCard
from app.models.student import Persona
from app.services import recognition as rec
from app.services.recognition import RecognitionService
from tests.test_teaching import _utcnow, create_knowledge_chain, create_test_student


async def _practice(db: AsyncSession, student, n_correct: int, n_wrong: int = 0, timed: bool = False) -> PracticeSession:
    from app.models.question import Difficulty, Question, QuestionType

    session = PracticeSession(
        timed=timed, instant_feedback=True, knowledge_point_ids=[], difficulty_range=[Difficulty.EASY],
        question_ids=[], starred_question_ids=[], student_id=student.id,
        total_count=n_correct + n_wrong, started_at=_utcnow(), ended_at=_utcnow(),
        correct_count=n_correct, wrong_count=n_wrong,
    )
    db.add(session)
    await db.flush()
    for i in range(n_correct + n_wrong):
        q = Question(type=QuestionType.SINGLE_CHOICE, content=f"Q{i}", answer="A", difficulty=Difficulty.EASY)
        db.add(q)
        await db.flush()
        db.add(PracticeItem(
            student_id=student.id, practice_session_id=session.id, question_id=q.id, user_answer="A",
            sequence=i, is_correct=i < n_correct, is_skipped=False, started_at=_utcnow(), ended_at=_utcnow(),
        ))
    await db.flush()
    return session


class TestRecognition:
    async def test_practice_points_and_idempotent(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        session = await _practice(db_session, student, n_correct=3, n_wrong=1)
        svc = RecognitionService(db_session)

        await svc.on_practice_end(session)
        total = await svc.total_points(student.id)
        # 3 对 ×4 + 1 错 ×2 = 14，首日 streak 加成 ×1.1
        assert total == pytest.approx(14 * 1.1, abs=0.01)

        await svc.on_practice_end(session)
        assert await svc.total_points(student.id) == pytest.approx(total)

    async def test_timed_multiplier(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        session = await _practice(db_session, student, n_correct=5, timed=True)
        svc = RecognitionService(db_session)
        await svc.on_practice_end(session)
        assert await svc.total_points(student.id) == pytest.approx(20 * 1.2 * 1.1, abs=0.01)

    async def test_cards_unlock_in_order(self, db_session: AsyncSession, monkeypatch):
        monkeypatch.setattr(rec, "THRESHOLDS", {**rec.THRESHOLDS, Persona.PENNY: 10, Persona.HOWARD: 20})
        student = await create_test_student(db_session)
        svc = RecognitionService(db_session)
        assert await svc.unlocked_personas(student.id) == [Persona.LEONARD]

        s1 = await _practice(db_session, student, n_correct=3)  # 12 × 1.1 = 13.2
        granted = await svc.on_practice_end(s1)
        assert [c.card_key for c in granted] == ["penny"]

        s2 = await _practice(db_session, student, n_correct=2)  # +8.8 → 22
        granted = await svc.on_practice_end(s2)
        assert [c.card_key for c in granted] == ["howard"]
        assert await svc.unlocked_personas(student.id) == [Persona.LEONARD, Persona.PENNY, Persona.HOWARD]

    async def test_daily_diminishing(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        svc = RecognitionService(db_session)
        session = await _practice(db_session, student, n_correct=40)
        await svc.on_practice_end(session)
        # 前 30 题 4 分，后 10 题半额 2 分
        assert await svc.total_points(student.id) == pytest.approx((30 * 4 + 10 * 2) * 1.1, abs=0.01)

    async def test_persona_update_requires_unlock(self, client, db_session: AsyncSession):
        student = await create_test_student(db_session)
        await db_session.commit()
        resp = await client.put(f"/api/v1/students/{student.id}", json={"persona": "sheldon"})
        assert resp.status_code == 403
        resp = await client.put(f"/api/v1/students/{student.id}", json={"persona": "leonard"})
        assert resp.status_code == 200

        db_session.add(StudentCard(student_id=student.id, card_key="penny", acquired_at=_utcnow()))
        await db_session.commit()
        resp = await client.put(f"/api/v1/students/{student.id}", json={"persona": "penny"})
        assert resp.status_code == 200
        cards = await client.get(f"/api/v1/students/{student.id}/cards")
        assert cards.json()["unlocked"] == ["leonard", "penny"]
