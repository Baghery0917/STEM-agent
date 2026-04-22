import logging
import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.llm.client import LLMClient
from app.models.question import Question, question_knowledge_point
from app.models.section import Section
from app.schemas.question import QuestionCreate, QuestionUpdate


logger = logging.getLogger(__name__)


def _strip_text_for_embedding(text: str) -> str:
    """剔除 LaTeX 公式和多余空白，按 PRD 3.6.2 只嵌入纯文本内容。"""
    if not text:
        return ""
    stripped = re.sub(r"\$\$.+?\$\$", " ", text, flags=re.DOTALL)
    stripped = re.sub(r"\$.+?\$", " ", stripped)
    stripped = re.sub(r"\\\[.+?\\\]", " ", stripped, flags=re.DOTALL)
    stripped = re.sub(r"\\\(.+?\\\)", " ", stripped)
    stripped = re.sub(r"\s+", " ", stripped)
    return stripped.strip()


class QuestionService:
    async def _compute_embedding(self, content: str) -> list[float] | None:
        text = _strip_text_for_embedding(content)
        if not text:
            return None
        try:
            llm = LLMClient()
            vectors = await llm.embed([text])
            return vectors[0] if vectors else None
        except Exception as exc:
            logger.warning("Embedding generation failed: %s", exc)
            return None

    async def _resolve_knowledge_points(
        self,
        db: AsyncSession,
        ids: list[int],
    ) -> list[Section]:
        if not ids:
            return []
        result = await db.execute(select(Section).where(Section.id.in_(ids)))
        sections = list(result.scalars().all())
        found_ids = {s.id for s in sections}
        missing = sorted(set(ids) - found_ids)
        if missing:
            raise ValueError(f"Knowledge point ids not found: {missing}")
        return sections

    async def create(self, db: AsyncSession, obj_in: QuestionCreate) -> Question:
        knowledge_point_ids = obj_in.knowledge_point_ids
        obj_data = obj_in.model_dump(exclude={"knowledge_point_ids"})

        db_obj = Question(**obj_data)
        if knowledge_point_ids:
            db_obj.knowledge_points = await self._resolve_knowledge_points(
                db, knowledge_point_ids,
            )

        embedding = await self._compute_embedding(obj_in.content)
        if embedding is not None:
            db_obj.embedding = embedding

        db.add(db_obj)
        await db.flush()
        return await self.get(db, db_obj.id)

    async def get(self, db: AsyncSession, question_id: int) -> Question | None:
        stmt = select(Question).where(Question.id == question_id).options(selectinload(Question.knowledge_points))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_list(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        type: str | None = None,
        difficulty: str | None = None,
        knowledge_point_ids: list[int] | None = None,
        volume_id: int | None = None,
        chapter_id: int | None = None,
        match_all_kps: bool = False,
    ) -> list[Question]:
        stmt = select(Question).options(selectinload(Question.knowledge_points))

        if type:
            stmt = stmt.where(Question.type == type)
        if difficulty:
            stmt = stmt.where(Question.difficulty == difficulty)

        needs_subquery = bool(knowledge_point_ids) or chapter_id or volume_id

        if needs_subquery:
            subq = select(question_knowledge_point.c.question_id).join(
                Section, Section.id == question_knowledge_point.c.section_id,
            )
            if knowledge_point_ids:
                subq = subq.where(
                    question_knowledge_point.c.section_id.in_(knowledge_point_ids)
                )
                if match_all_kps:
                    subq = subq.group_by(
                        question_knowledge_point.c.question_id
                    ).having(
                        func.count(
                            func.distinct(question_knowledge_point.c.section_id)
                        ) == len(set(knowledge_point_ids))
                    )
            if chapter_id:
                subq = subq.where(Section.chapter_id == chapter_id)
            elif volume_id:
                from app.models.chapter import Chapter
                subq = subq.join(
                    Chapter, Chapter.id == Section.chapter_id,
                ).where(Chapter.volume_id == volume_id)
            stmt = stmt.where(Question.id.in_(subq.scalar_subquery()))

        stmt = stmt.order_by(Question.id).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def update(self, db: AsyncSession, question_id: int, obj_in: QuestionUpdate) -> Question | None:
        db_obj = await self.get(db, question_id)
        if not db_obj:
            return None

        update_data = obj_in.model_dump(exclude_unset=True, exclude={"knowledge_point_ids"})
        knowledge_point_ids = obj_in.knowledge_point_ids
        content_changed = "content" in update_data and update_data["content"] != db_obj.content

        for key, value in update_data.items():
            setattr(db_obj, key, value)

        if knowledge_point_ids is not None:
            db_obj.knowledge_points = await self._resolve_knowledge_points(
                db, knowledge_point_ids,
            )

        if content_changed:
            embedding = await self._compute_embedding(db_obj.content)
            db_obj.embedding = embedding

        await db.flush()
        return await self.get(db, db_obj.id)

    async def delete(self, db: AsyncSession, question_id: int) -> bool:
        db_obj = await self.get(db, question_id)
        if not db_obj:
            return False
        await db.delete(db_obj)
        await db.flush()
        return True

    async def search_by_text(
        self,
        db: AsyncSession,
        query: str,
        limit: int = 20,
        threshold: float | None = None,
    ) -> list[tuple[Question, float]]:
        if not query:
            return []
        embedding = await self._compute_embedding(query)
        if embedding is None:
            return []
        distance_expr = Question.embedding.cosine_distance(embedding).label("distance")
        stmt = (
            select(Question, distance_expr)
            .where(Question.embedding.isnot(None))
            .options(selectinload(Question.knowledge_points))
            .order_by(distance_expr)
            .limit(limit)
        )
        if threshold is not None:
            stmt = stmt.where(distance_expr <= threshold)
        result = await db.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]