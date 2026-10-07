from datetime import timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.badge import StudentLogin
from app.models.practice import PracticeItem, PracticeSession
from app.models.question import Difficulty, Question, QuestionType
from app.models.teaching import MessageRole, MessageType, TeachingMessage, TeachingSession, TeachingSessionStatus
from app.services import badges as badges_mod
from app.services.badges import BADGES, SESSION_CAP_MINUTES, TEACH_OTHERS_RATING, BadgeRule, BadgeService
from tests.test_teaching import _utcnow, create_test_student


async def _practice(
    db: AsyncSession, student, answered: int = 0, skipped: int = 0, minutes: float = 0.0,
) -> PracticeSession:
    start = _utcnow() - timedelta(minutes=minutes)
    end = _utcnow()
    session = PracticeSession(
        timed=False, instant_feedback=True, knowledge_point_ids=[], difficulty_range=[Difficulty.EASY],
        question_ids=[], starred_question_ids=[], student_id=student.id,
        total_count=answered + skipped, started_at=start, ended_at=end,
        correct_count=answered, skip_count=skipped,
    )
    db.add(session)
    await db.flush()
    for i in range(answered + skipped):
        q = Question(type=QuestionType.SINGLE_CHOICE, content=f"Q{i}", answer="A", difficulty=Difficulty.EASY)
        db.add(q)
        await db.flush()
        db.add(PracticeItem(
            student_id=student.id, practice_session_id=session.id, question_id=q.id, user_answer="A",
            sequence=i, is_correct=i < answered, is_skipped=i >= answered, started_at=start, ended_at=end,
        ))
    await db.flush()
    return session


async def _login_on(db: AsyncSession, student, days_ago: int) -> None:
    # 取当天正午，避免 DB 会话时区与 UTC 不同导致 date() 跨天
    at = (_utcnow() - timedelta(days=days_ago)).replace(hour=12, minute=0, second=0, microsecond=0)
    db.add(StudentLogin(student_id=student.id, created_at=at))
    await db.flush()


async def _teaching(db: AsyncSession, student, ratings: list[tuple[MessageRole, int | None]]) -> TeachingSession:
    session = TeachingSession(student_id=student.id, status=TeachingSessionStatus.COMPLETED, ended_at=_utcnow())
    db.add(session)
    await db.flush()
    for i, (role, rating) in enumerate(ratings):
        db.add(TeachingMessage(
            session_id=session.id, role=role, content=f"m{i}", message_type=MessageType.CHAT,
            sequence=i, self_rating=rating,
        ))
    await db.flush()
    return session


class TestLogins:
    async def test_record_login_counts_and_grants_galileo(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        svc = BadgeService(db_session)
        assert await svc.login_count(student.id) == 0

        granted = await svc.record_login(student.id)
        assert granted == []
        assert await svc.login_count(student.id) == 1
        assert (await svc.metrics(student.id))["logins"] == 1.0

        for _ in range(8):
            assert await svc.record_login(student.id) == []
        granted = await svc.record_login(student.id)
        assert [b.badge_key for b in granted] == ["galileo"]
        assert await svc.login_count(student.id) == 10

    async def test_evaluate_idempotent_and_ordered(self, db_session: AsyncSession, monkeypatch):
        monkeypatch.setattr(badges_mod, "BADGES", [
            BadgeRule("galileo", "logins", 1),
            BadgeRule("tycho", "logins", 2),
        ])
        student = await create_test_student(db_session)
        svc = BadgeService(db_session)

        assert [b.badge_key for b in await svc.record_login(student.id)] == ["galileo"]
        assert await svc.evaluate(student.id) == []
        assert [b.badge_key for b in await svc.record_login(student.id)] == ["tycho"]
        assert await svc.evaluate(student.id) == []
        assert [b.badge_key for b in await svc.badges(student.id)] == ["galileo", "tycho"]


class TestPractice:
    async def test_newton_after_one_answered(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        svc = BadgeService(db_session)
        await _practice(db_session, student, answered=1)
        assert (await svc.metrics(student.id))["answered"] == 1.0
        assert [b.badge_key for b in await svc.evaluate(student.id)] == ["newton"]

    async def test_skipped_only_grants_nothing(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        svc = BadgeService(db_session)
        await _practice(db_session, student, skipped=3)
        assert (await svc.metrics(student.id))["answered"] == 0.0
        assert await svc.evaluate(student.id) == []
        assert await svc.badges(student.id) == []


class TestDurations:
    async def test_fifty_minute_session_grants_curie(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        svc = BadgeService(db_session)
        await _practice(db_session, student, minutes=50)
        metrics = await svc.metrics(student.id)
        assert metrics["longest_minutes"] == pytest.approx(50, abs=0.2)
        assert metrics["total_minutes"] == pytest.approx(50, abs=0.2)
        assert [b.badge_key for b in await svc.evaluate(student.id)] == ["curie"]

    async def test_session_capped(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        svc = BadgeService(db_session)
        await _practice(db_session, student, minutes=600)
        metrics = await svc.metrics(student.id)
        assert metrics["longest_minutes"] == SESSION_CAP_MINUTES
        assert metrics["total_minutes"] == SESSION_CAP_MINUTES
        granted = {b.badge_key for b in await svc.evaluate(student.id)}
        assert granted == {"curie", "faraday"}

    async def test_unfinished_session_ignored(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        session = await _practice(db_session, student, minutes=50)
        session.ended_at = None
        await db_session.flush()
        metrics = await BadgeService(db_session).metrics(student.id)
        assert metrics["longest_minutes"] == 0.0
        assert metrics["total_minutes"] == 0.0


class TestStreak:
    async def test_three_consecutive_days(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        for days_ago in (0, 1, 2):
            await _login_on(db_session, student, days_ago)
        assert (await BadgeService(db_session).metrics(student.id))["streak_days"] == 3.0

    async def test_gap_breaks_streak(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        for days_ago in (0, 2, 3):
            await _login_on(db_session, student, days_ago)
        assert (await BadgeService(db_session).metrics(student.id))["streak_days"] == 1.0

    async def test_counts_from_yesterday_without_today(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        for days_ago in (1, 2):
            await _login_on(db_session, student, days_ago)
        assert (await BadgeService(db_session).metrics(student.id))["streak_days"] == 2.0

    async def test_only_old_records_is_zero(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        await _login_on(db_session, student, 2)
        assert (await BadgeService(db_session).metrics(student.id))["streak_days"] == 0.0


class TestTeaching:
    async def test_teach_others_counts_assistant_rating_only(self, db_session: AsyncSession):
        student = await create_test_student(db_session)
        await _teaching(db_session, student, [
            (MessageRole.ASSISTANT, TEACH_OTHERS_RATING),
            (MessageRole.ASSISTANT, TEACH_OTHERS_RATING),
            (MessageRole.ASSISTANT, TEACH_OTHERS_RATING - 1),
            (MessageRole.ASSISTANT, None),
            (MessageRole.USER, TEACH_OTHERS_RATING),
        ])
        metrics = await BadgeService(db_session).metrics(student.id)
        assert metrics["teach_others"] == 2.0
        assert metrics["teaching_sessions"] == 1.0

    async def test_other_students_messages_excluded(self, db_session: AsyncSession):
        student = await create_test_student(db_session, name="A")
        other = await create_test_student(db_session, name="B")
        await _teaching(db_session, other, [(MessageRole.ASSISTANT, TEACH_OTHERS_RATING)])
        assert (await BadgeService(db_session).metrics(student.id))["teach_others"] == 0.0


class TestApi:
    async def test_cards_returns_badges_and_progress(self, client, db_session: AsyncSession):
        student = await create_test_student(db_session)
        await _practice(db_session, student, answered=1)
        await db_session.commit()

        resp = await client.get(f"/api/v1/students/{student.id}/cards")
        assert resp.status_code == 200
        body = resp.json()
        assert set(body) == {"cards", "unlocked", "badges", "badge_progress"}
        assert body["unlocked"] == ["leonard"]
        assert [b["badge_key"] for b in body["badges"]] == ["newton"]

        progress = body["badge_progress"]
        assert [p["badge_key"] for p in progress] == [r.key for r in BADGES]
        for p, rule in zip(progress, BADGES):
            assert p["metric"] == rule.metric
            assert p["threshold"] == rule.threshold
        by_key = {p["badge_key"]: p for p in progress}
        assert by_key["newton"]["value"] == 1.0
        assert by_key["galileo"]["value"] == 0.0

    async def test_checkin(self, client, db_session: AsyncSession, monkeypatch):
        monkeypatch.setattr(badges_mod, "BADGES", [BadgeRule("galileo", "logins", 2)])
        student = await create_test_student(db_session)
        await db_session.commit()

        resp = await client.post(f"/api/v1/students/{student.id}/checkin")
        assert resp.status_code == 200
        assert resp.json() == {"login_count": 1, "new_badges": []}

        resp = await client.post(f"/api/v1/students/{student.id}/checkin")
        body = resp.json()
        assert body["login_count"] == 2
        assert [b["badge_key"] for b in body["new_badges"]] == ["galileo"]
        assert "acquired_at" in body["new_badges"][0]

    async def test_unknown_student_404(self, client):
        assert (await client.get("/api/v1/students/999999/cards")).status_code == 404
        assert (await client.post("/api/v1/students/999999/checkin")).status_code == 404
