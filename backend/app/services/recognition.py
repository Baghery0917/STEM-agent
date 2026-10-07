"""认可卡：一套隐藏计分规则，线性解锁七位讲师。

规则不下发前端。分数只增不减。所有入口都按来源幂等。
"""
import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.practice import PracticeItem, PracticeSession
from app.models.recognition import ScoreEvent, StudentCard
from app.models.student import Persona
from app.models.teaching import MessageRole, MessageType, TeachingSession

logger = logging.getLogger(__name__)

# 解锁顺序与阈值。Leonard 注册即有。
CARD_ORDER: list[Persona] = [
    Persona.PENNY, Persona.HOWARD, Persona.RAJ, Persona.BERNADETTE, Persona.AMY, Persona.SHELDON,
]
THRESHOLDS: dict[Persona, float] = {
    Persona.PENNY: 150,
    Persona.HOWARD: 400,
    Persona.RAJ: 800,
    Persona.BERNADETTE: 1500,
    Persona.AMY: 2600,
    Persona.SHELDON: 4500,
}

# 练习：每答一题（不含跳过）基础分，答对翻倍
ANSWER_BASE = 2.0
CORRECT_MULTIPLIER = 2.0
# 每日答题递减：前 30 题全额，31–60 半额，之后两折
DAILY_FULL = 30
DAILY_HALF = 60
TIMED_MULTIPLIER = 1.2
# 教学：正常结束 5 分，填了自评 15 分；掌握度正增量 ×100
TEACHING_END = 5.0
TEACHING_END_RATED = 15.0
MASTERY_DELTA_MULTIPLIER = 100.0
# 星标后真的去问了
STAR_ASKED = 10.0
# 自评「能自己做」且 7 天内该知识点练习正确率 ≥ 70%
SELF_RATING_CONFIRMED = 30.0
SELF_RATING_CONFIRM_DAYS = 7
SELF_RATING_CONFIRM_RATE = 0.7
# 连续学习天数加成：×(1 + 0.1 × min(streak, 7))
STREAK_STEP = 0.1
STREAK_CAP = 7


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RecognitionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # 查询
    # ------------------------------------------------------------------

    async def cards(self, student_id: int) -> list[StudentCard]:
        result = await self.db.execute(
            select(StudentCard)
            .where(StudentCard.student_id == student_id)
            .order_by(StudentCard.acquired_at)
        )
        return list(result.scalars().all())

    async def unlocked_personas(self, student_id: int) -> list[Persona]:
        owned = {c.card_key for c in await self.cards(student_id)}
        return [Persona.LEONARD] + [p for p in CARD_ORDER if p.value in owned]

    async def total_points(self, student_id: int) -> float:
        result = await self.db.execute(
            select(func.coalesce(func.sum(ScoreEvent.points), 0.0))
            .where(ScoreEvent.student_id == student_id)
        )
        return float(result.scalar_one())

    # ------------------------------------------------------------------
    # 钩子
    # ------------------------------------------------------------------

    async def on_practice_end(self, session: PracticeSession) -> list[StudentCard]:
        """练习结束：答题分（含每日递减、计时加成）+ 自评验证分"""
        items = await self._items(session.id)
        answered = [i for i in items if not i.is_skipped]
        before_today = await self._answered_today_before(session)

        points = 0.0
        for idx, item in enumerate(answered):
            base = ANSWER_BASE * (CORRECT_MULTIPLIER if item.is_correct else 1.0)
            points += base * self._daily_factor(before_today + idx)
        if session.timed and answered:
            points *= TIMED_MULTIPLIER
        points *= await self._streak_multiplier(session.student_id)

        new_cards: list[StudentCard] = []
        if points > 0:
            new_cards += await self._award(session.student_id, "practice_end", session.id, points)
        new_cards += await self._confirm_self_ratings(session, answered)
        return new_cards

    async def on_teaching_end(
        self, session: TeachingSession, mastery_level_delta: float | None,
    ) -> list[StudentCard]:
        """教学结束：结束分 + 掌握度正增量 + 星标追问"""
        rated = any(
            m.role == MessageRole.ASSISTANT and m.self_rating is not None for m in session.messages
        )
        points = TEACHING_END_RATED if rated else TEACHING_END
        if mastery_level_delta and mastery_level_delta > 0:
            points += mastery_level_delta * MASTERY_DELTA_MULTIPLIER
        points *= await self._streak_multiplier(session.student_id)

        new_cards = await self._award(session.student_id, "teaching_end", session.id, points)
        if await self._asked_starred(session):
            new_cards += await self._award(session.student_id, "star_asked", session.id, STAR_ASKED)
        return new_cards

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    async def _award(
        self, student_id: int, source_type: str, source_id: int, points: float,
    ) -> list[StudentCard]:
        exists = await self.db.execute(
            select(ScoreEvent.id).where(
                ScoreEvent.source_type == source_type, ScoreEvent.source_id == source_id,
            )
        )
        if exists.scalar_one_or_none() is not None:
            return []
        self.db.add(ScoreEvent(
            student_id=student_id, source_type=source_type, source_id=source_id,
            points=round(points, 2),
        ))
        await self.db.flush()
        return await self._grant_due_cards(student_id)

    async def _grant_due_cards(self, student_id: int) -> list[StudentCard]:
        total = await self.total_points(student_id)
        owned = {c.card_key for c in await self.cards(student_id)}
        granted: list[StudentCard] = []
        for persona in CARD_ORDER:
            if persona.value in owned:
                continue
            if total < THRESHOLDS[persona]:
                break  # 线性解锁：前一张没到就不看后面
            card = StudentCard(student_id=student_id, card_key=persona.value, acquired_at=_utcnow())
            self.db.add(card)
            granted.append(card)
        if granted:
            await self.db.flush()
        return granted

    @staticmethod
    def _daily_factor(position: int) -> float:
        if position < DAILY_FULL:
            return 1.0
        if position < DAILY_HALF:
            return 0.5
        return 0.2

    async def _items(self, session_id: int) -> list[PracticeItem]:
        result = await self.db.execute(
            select(PracticeItem)
            .where(PracticeItem.practice_session_id == session_id)
            .order_by(PracticeItem.sequence)
        )
        return list(result.scalars().all())

    async def _answered_today_before(self, session: PracticeSession) -> int:
        start = datetime.combine(_utcnow().date(), datetime.min.time(), tzinfo=timezone.utc)
        result = await self.db.execute(
            select(func.count(PracticeItem.id)).where(
                PracticeItem.student_id == session.student_id,
                PracticeItem.practice_session_id != session.id,
                PracticeItem.is_skipped.is_(False),
                PracticeItem.ended_at >= start,
            )
        )
        return int(result.scalar_one())

    async def _streak_multiplier(self, student_id: int) -> float:
        """以往有计分的连续天数（含今天）"""
        result = await self.db.execute(
            select(func.distinct(func.date(ScoreEvent.created_at)))
            .where(ScoreEvent.student_id == student_id)
        )
        days = {d if isinstance(d, date) else d.date() for (d,) in result.all()}
        today = _utcnow().date()
        streak = 1
        cursor = today - timedelta(days=1)
        while cursor in days:
            streak += 1
            cursor -= timedelta(days=1)
        return 1 + STREAK_STEP * min(streak, STREAK_CAP)

    async def _asked_starred(self, session: TeachingSession) -> bool:
        if not session.source_practice_session_id or not session.source_question_ids:
            return False
        result = await self.db.execute(
            select(PracticeSession.starred_question_ids)
            .where(PracticeSession.id == session.source_practice_session_id)
        )
        starred = set(result.scalar_one_or_none() or [])
        return bool(starred.intersection(session.source_question_ids))

    async def _confirm_self_ratings(
        self, session: PracticeSession, answered: list[PracticeItem],
    ) -> list[StudentCard]:
        """7 天内自评「能自己做」或「能讲给别人」的教学会话，用这次练习验证"""
        if not answered:
            return []
        since = _utcnow() - timedelta(days=SELF_RATING_CONFIRM_DAYS)
        result = await self.db.execute(
            select(TeachingSession)
            .where(
                TeachingSession.student_id == session.student_id,
                TeachingSession.ended_at.is_not(None),
                TeachingSession.ended_at >= since,
            )
        )
        candidates = list(result.scalars().all())
        if not candidates:
            return []

        from sqlalchemy.orm import selectinload  # 局部导入避免循环
        from app.models.question import Question

        q_result = await self.db.execute(
            select(Question).options(selectinload(Question.knowledge_points))
            .where(Question.id.in_([i.question_id for i in answered]))
        )
        kp_of_q = {q.id: {kp.id for kp in q.knowledge_points} for q in q_result.scalars().all()}

        granted: list[StudentCard] = []
        for ts in candidates:
            msgs = await self.db.execute(
                select(TeachingSession)
                .options(selectinload(TeachingSession.messages))
                .where(TeachingSession.id == ts.id)
            )
            full = msgs.scalar_one()
            rated = [m for m in full.messages if m.role == MessageRole.ASSISTANT and m.self_rating is not None]
            if not rated or max(rated, key=lambda m: m.sequence).self_rating < 2:
                continue
            section_ids: set[int] = set()
            for m in full.messages:
                if m.message_type == MessageType.LLM_ANALYSIS:
                    import re
                    section_ids = {int(x) for x in re.findall(r"- (\d+):", m.content)}
                    break
            related = [i for i in answered if kp_of_q.get(i.question_id, set()) & section_ids]
            if not related:
                continue
            rate = sum(1 for i in related if i.is_correct) / len(related)
            if rate >= SELF_RATING_CONFIRM_RATE:
                granted += await self._award(
                    session.student_id, "self_rating_confirmed", ts.id, SELF_RATING_CONFIRMED,
                )
        return granted
