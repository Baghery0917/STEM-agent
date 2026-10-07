from sqlalchemy import exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.practice import PracticeSession
from app.models.section import Section
from app.models.teaching import MessageRole, MessageType, TeachingMessage, TeachingSession


def _snippet(text: str, keyword: str, width: int = 60) -> str:
    """围绕命中位置截一段"""
    flat = text.replace("\n", " ")
    idx = flat.lower().find(keyword.lower())
    if idx == -1:
        return flat[:width]
    start = max(0, idx - width // 3)
    out = flat[start:start + width]
    return ("…" if start > 0 else "") + out + ("…" if start + width < len(flat) else "")


class SessionSearchService:
    """左侧会话栏的搜索：教学会话按消息内容，练习按知识点名称"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def search(self, student_id: int, q: str, limit: int = 20) -> list[dict]:
        keyword = q.strip()
        if not keyword:
            return []
        pattern = f"%{keyword}%"
        results: list[dict] = []

        # 教学：任一 user / assistant 消息命中
        hit_msg = (
            select(TeachingMessage.content)
            .where(
                TeachingMessage.session_id == TeachingSession.id,
                TeachingMessage.role.in_([MessageRole.USER, MessageRole.ASSISTANT]),
                TeachingMessage.content.ilike(pattern),
            )
            .order_by(TeachingMessage.sequence.asc())
            .limit(1)
            .correlate(TeachingSession)
            .scalar_subquery()
        )
        first_q = (
            select(TeachingMessage.content)
            .where(
                TeachingMessage.session_id == TeachingSession.id,
                TeachingMessage.message_type == MessageType.QUESTION_SUBMIT,
            )
            .order_by(TeachingMessage.sequence.asc())
            .limit(1)
            .correlate(TeachingSession)
            .scalar_subquery()
        )
        t_rows = await self.db.execute(
            select(TeachingSession, hit_msg, first_q)
            .where(TeachingSession.student_id == student_id, hit_msg.isnot(None))
            .order_by(TeachingSession.created_at.desc())
            .limit(limit)
        )
        for session, hit, question in t_rows.all():
            results.append({
                "kind": "teaching",
                "id": session.id,
                "title": (question or "").replace("\n", " ")[:60] or f"会话 #{session.id}",
                "snippet": _snippet(hit, keyword),
                "at": session.created_at,
                "status": session.status.value,
            })

        # 练习：知识点标题命中
        section_hit = (
            select(Section.id)
            .where(
                Section.id == func.any(PracticeSession.knowledge_point_ids),
                Section.title.ilike(pattern),
            )
            .correlate(PracticeSession)
        )
        p_rows = await self.db.execute(
            select(PracticeSession)
            .where(PracticeSession.student_id == student_id, exists(section_hit))
            .order_by(PracticeSession.started_at.desc())
            .limit(limit)
        )
        practices = list(p_rows.scalars().all())
        if practices:
            all_ids = {sid for p in practices for sid in p.knowledge_point_ids}
            titles = dict((await self.db.execute(
                select(Section.id, Section.title).where(Section.id.in_(all_ids))
            )).all())
            for p in practices:
                names = [titles[i] for i in p.knowledge_point_ids if i in titles]
                results.append({
                    "kind": "practice",
                    "id": p.id,
                    "title": f"{'、'.join(names[:2])}{' 等' if len(names) > 2 else ''} · {p.total_count} 题",
                    "snippet": "、".join(n for n in names if keyword.lower() in n.lower()),
                    "at": p.started_at,
                    "status": "completed" if p.ended_at else "active",
                })

        results.sort(key=lambda r: r["at"], reverse=True)
        return results[:limit]
