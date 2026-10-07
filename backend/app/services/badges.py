"""物理学家徽章：阈值型成就，与认可卡（计分解锁讲师）互不影响。

规则下发前端（有进度条）。徽章只增不减，达到阈值即发。
"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.badge import StudentBadge, StudentLogin
from app.models.practice import PracticeItem, PracticeSession
from app.models.teaching import MessageRole, TeachingMessage, TeachingSession, TeachingSessionStatus


@dataclass(frozen=True)
class BadgeRule:
    key: str
    metric: str
    threshold: float


# 顺序即展示顺序。metric 对应 BadgeService.metrics() 的键。
BADGES: list[BadgeRule] = [
    BadgeRule("newton", "answered", 1),            # 苹果落地：答完第 1 题
    BadgeRule("galileo", "logins", 10),            # 望远镜：登录 10 次
    BadgeRule("tycho", "logins", 50),              # 观测日志：登录 50 次
    BadgeRule("kepler", "streak_days", 7),         # 行星周期：连续学习 7 天
    BadgeRule("curie", "longest_minutes", 45),     # 实验室长夜：单次 45 分钟
    BadgeRule("faraday", "longest_minutes", 90),   # 线圈不停：单次 90 分钟
    BadgeRule("einstein", "total_minutes", 600),   # 时间是相对的：累计 10 小时
    BadgeRule("hawking", "total_minutes", 3000),   # 时间简史：累计 50 小时
    BadgeRule("maxwell", "answered", 200),         # 四个方程：答 200 题
    BadgeRule("bohr", "teaching_sessions", 20),    # 哥本哈根辩论：20 次教学会话
    BadgeRule("heisenberg", "star_asked", 5),      # 不确定就问：星标后追问 5 次
    BadgeRule("feynman", "teach_others", 5),       # 讲给别人听：自评「能讲给别人」5 次
]

# 单次时长上限：防止忘了结束的会话把时长算爆
SESSION_CAP_MINUTES = 180.0
# 自评 3 = 「能讲给别人」（见前端 SelfRate LABELS）
TEACH_OTHERS_RATING = 3


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BadgeService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def badges(self, student_id: int) -> list[StudentBadge]:
        result = await self.db.execute(
            select(StudentBadge)
            .where(StudentBadge.student_id == student_id)
            .order_by(StudentBadge.acquired_at)
        )
        return list(result.scalars().all())

    async def login_count(self, student_id: int) -> int:
        return int(await self._scalar(
            select(func.count(StudentLogin.id)).where(StudentLogin.student_id == student_id)
        ))

    async def record_login(self, student_id: int) -> list[StudentBadge]:
        self.db.add(StudentLogin(student_id=student_id))
        await self.db.flush()
        return await self.evaluate(student_id)

    async def evaluate(self, student_id: int) -> list[StudentBadge]:
        """按当前指标补发所有已达标但未持有的徽章"""
        metrics = await self.metrics(student_id)
        owned = {b.badge_key for b in await self.badges(student_id)}
        granted: list[StudentBadge] = []
        for rule in BADGES:
            if rule.key in owned or metrics[rule.metric] < rule.threshold:
                continue
            badge = StudentBadge(student_id=student_id, badge_key=rule.key, acquired_at=_utcnow())
            self.db.add(badge)
            granted.append(badge)
        if granted:
            await self.db.flush()
        return granted

    async def metrics(self, student_id: int) -> dict[str, float]:
        answered = await self._scalar(
            select(func.count(PracticeItem.id)).where(
                PracticeItem.student_id == student_id, PracticeItem.is_skipped.is_(False),
            )
        )
        teaching_sessions = await self._scalar(
            select(func.count(TeachingSession.id)).where(
                TeachingSession.student_id == student_id,
                TeachingSession.status == TeachingSessionStatus.COMPLETED,
            )
        )
        teach_others = await self._scalar(
            select(func.count(TeachingMessage.id))
            .join(TeachingSession, TeachingSession.id == TeachingMessage.session_id)
            .where(
                TeachingSession.student_id == student_id,
                TeachingMessage.role == MessageRole.ASSISTANT,
                TeachingMessage.self_rating == TEACH_OTHERS_RATING,
            )
        )
        longest, total = await self._durations(student_id)
        return {
            "logins": float(await self.login_count(student_id)),
            "answered": answered,
            "teaching_sessions": teaching_sessions,
            "teach_others": teach_others,
            "star_asked": await self._star_asked(student_id),
            "longest_minutes": longest,
            "total_minutes": total,
            "streak_days": await self._streak_days(student_id),
        }

    async def _scalar(self, stmt) -> float:
        result = await self.db.execute(stmt)
        return float(result.scalar_one() or 0)

    async def _star_asked(self, student_id: int) -> float:
        """来自练习的教学会话中，带的题至少有一道是星标题"""
        result = await self.db.execute(
            select(TeachingSession.source_question_ids, PracticeSession.starred_question_ids)
            .join(PracticeSession, PracticeSession.id == TeachingSession.source_practice_session_id)
            .where(TeachingSession.student_id == student_id)
        )
        return float(sum(
            1 for asked, starred in result.all()
            if asked and starred and set(asked) & set(starred)
        ))

    async def _durations(self, student_id: int) -> tuple[float, float]:
        """(最长单次分钟, 累计分钟)。练习按 started→ended，教学按 created→ended，未结束的不算"""
        practice = await self.db.execute(
            select(PracticeSession.started_at, PracticeSession.ended_at).where(
                PracticeSession.student_id == student_id, PracticeSession.ended_at.is_not(None),
            )
        )
        teaching = await self.db.execute(
            select(TeachingSession.created_at, TeachingSession.ended_at).where(
                TeachingSession.student_id == student_id, TeachingSession.ended_at.is_not(None),
            )
        )
        longest = total = 0.0
        for start, end in [*practice.all(), *teaching.all()]:
            minutes = min(max((end - start).total_seconds() / 60, 0.0), SESSION_CAP_MINUTES)
            longest = max(longest, minutes)
            total += minutes
        return round(longest, 1), round(total, 1)

    async def _streak_days(self, student_id: int) -> float:
        """以今天（或昨天）为终点、有登录或答题记录的连续天数"""
        login_days = await self.db.execute(
            select(func.distinct(func.date(StudentLogin.created_at)))
            .where(StudentLogin.student_id == student_id)
        )
        item_days = await self.db.execute(
            select(func.distinct(func.date(PracticeItem.ended_at)))
            .where(PracticeItem.student_id == student_id, PracticeItem.ended_at.is_not(None))
        )
        days = {
            d if isinstance(d, date) else d.date()
            for (d,) in [*login_days.all(), *item_days.all()] if d is not None
        }
        today = _utcnow().date()
        cursor = today if today in days else today - timedelta(days=1)
        streak = 0
        while cursor in days:
            streak += 1
            cursor -= timedelta(days=1)
        return float(streak)
