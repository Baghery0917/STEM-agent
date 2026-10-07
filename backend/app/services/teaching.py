import asyncio
import json
import logging
import re
from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.external.teaching_strategy import StrategyResult, TeachingStrategyClient
from app.llm.client import LLMClient
from app.models.section import Section
from app.models.student_knowledge_summary import StudentKnowledgeSummary
from app.models.emotion import StudentKpEmotion
from app.models.practice import PracticeItem, PracticeSession
from app.models.question import Question
from app.models.student import ExplainStyle, Persona, Student
from app.llm.personas import is_frustrated, persona_prompt
from app.models.teaching import (
    MessageRole,
    MessageType,
    PipelineStatus,
    SessionEndReason,
    TeachingMessage,
    TeachingReference,
    TeachingSession,
    TeachingSessionStatus,
)
from app.external.emotion import describe_value
from app.services.emotion import EmotionService, InstantEmotion
from app.services.question import QuestionService


logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


_DEFAULT_STRATEGY = StrategyResult(
    strategy="Adaptive guided inquiry",
    reason="Default strategy (external service unavailable)",
)
_EMOTION_GUIDANCE = (
    "\n情绪使用规则：历史情绪反映学生对这些知识点的长期感受，当前状态反映此刻。"
    "状态偏向受挫（>=3）时先肯定已做对的部分、放慢节奏、一次只推进一小步；"
    "状态自信（<=2）时可以直接追问更深的问题。不要在回复里提及你观察到了情绪。"
)
_EXPLAIN_STYLE_GUIDANCE: dict[ExplainStyle, str] = {
    ExplainStyle.DIRECT: "\n学生设置：直接给答案。先给出完整解答与关键步骤，再补充一句为什么。",
    ExplainStyle.GUIDED: "\n学生设置：引导我自己找。不直接给答案，每次只抛一个小问题，等学生回应。",
    ExplainStyle.HINT: "\n学生设置：只给提示。只指出卡点所在和下一步方向，不展开推导。",
}
# 掌握度自评 -> 结束会话时的 mastery_level_delta（学生未显式提交时使用最后一次自评）
_SELF_RATING_DELTA: dict[int, float] = {0: -0.1, 1: 0.05, 2: 0.15, 3: 0.25}

_DEFAULT_ASSISTANT_REPLY = (
    "我现在暂时无法调用讲解服务，请稍后再试。你可以先尝试描述一下你对题目的初步思路。"
)


class TeachingService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.llm = LLMClient()
        self.strategy_client = TeachingStrategyClient()
        self.question_service = QuestionService()
        self.emotion = EmotionService(llm=self.llm)

    # ------------------------------------------------------------------
    # 公开方法
    # ------------------------------------------------------------------

    async def create_session_shell(
        self,
        student_id: int,
        question_content: str,
        question_image: str | None = None,
        source_practice_session_id: int | None = None,
        source_question_ids: list[int] | None = None,
    ) -> TeachingSession:
        if source_practice_session_id:
            question_content = await self.build_handoff_content(
                student_id=student_id,
                practice_session_id=source_practice_session_id,
                question_ids=source_question_ids or [],
                student_note=question_content,
            )
        persona = (
            await self.db.execute(select(Student.persona).where(Student.id == student_id))
        ).scalar_one_or_none()
        session = TeachingSession(
            student_id=student_id,
            status=TeachingSessionStatus.ACTIVE,
            pipeline_status=PipelineStatus.PENDING,
            persona=persona,
            source_practice_session_id=source_practice_session_id,
            source_question_ids=source_question_ids or None,
        )
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)

        await self._add_message(
            session_id=session.id,
            role=MessageRole.USER,
            content=question_content,
            message_type=MessageType.QUESTION_SUBMIT,
            sequence=0,
        )
        await self.db.flush()
        return session

    async def build_handoff_content(
        self,
        student_id: int,
        practice_session_id: int,
        question_ids: list[int],
        student_note: str,
    ) -> str:
        """练习转教学：把题干、学生作答、正确答案拼成第一条消息，供流水线分析与讲解"""
        result = await self.db.execute(
            select(PracticeSession).where(
                PracticeSession.id == practice_session_id,
                PracticeSession.student_id == student_id,
            )
        )
        practice = result.scalar_one_or_none()
        if practice is None:
            raise LookupError("Practice session not found")
        ids = [q for q in question_ids if q in practice.question_ids] or list(practice.starred_question_ids)
        if not ids:
            raise ValueError("No questions selected from the practice session")

        q_result = await self.db.execute(select(Question).where(Question.id.in_(ids)))
        q_by_id = {q.id: q for q in q_result.scalars().all()}
        it_result = await self.db.execute(
            select(PracticeItem).where(
                PracticeItem.practice_session_id == practice_session_id,
                PracticeItem.question_id.in_(ids),
            )
        )
        item_by_q = {it.question_id: it for it in it_result.scalars().all()}

        blocks: list[str] = []
        for qid in ids:
            q = q_by_id.get(qid)
            if q is None:
                continue
            pos = practice.question_ids.index(qid) + 1
            item = item_by_q.get(qid)
            if item is None:
                outcome = "未作答"
            elif item.is_skipped:
                outcome = "跳过"
            else:
                outcome = f"我的答案：{item.user_answer}（{'答对' if item.is_correct else '答错'}）"
            blocks.append(
                f"【练习第 {pos} 题】\n{q.content}\n{outcome}\n正确答案：{q.answer}"
            )
        header = f"（来自练习 #{practice.id}）"
        note = student_note.strip()
        return "\n\n".join([header, *blocks, note] if note else [header, *blocks])

    async def rate_message(
        self, session_id: int, message_id: int, rating: int | None,
    ) -> TeachingMessage:
        """记录学生对某条 AI 回复的掌握度自评（0-3），None 表示取消"""
        result = await self.db.execute(
            select(TeachingMessage).where(
                TeachingMessage.id == message_id,
                TeachingMessage.session_id == session_id,
            )
        )
        msg = result.scalar_one_or_none()
        if msg is None:
            raise LookupError("Message not found")
        if msg.role != MessageRole.ASSISTANT:
            raise ValueError("Only assistant messages can be rated")
        msg.self_rating = rating
        await self.db.flush()
        await self.db.refresh(msg)
        return msg

    async def run_pipeline(
        self,
        session_id: int,
        question_content: str,
        question_image: str | None = None,
        frame_base64: str | None = None,
    ) -> None:
        result = await self.db.execute(
            select(TeachingSession).where(TeachingSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise LookupError(f"Session {session_id} not found")

        session.pipeline_status = PipelineStatus.RUNNING
        await self.db.commit()

        try:
            # 2. LLM 分析知识点
            sections = await self._analyze_knowledge_points(question_content, question_image)
            analysis_content = self._format_analysis_content(sections)
            await self._add_message(
                session_id=session_id,
                role=MessageRole.SYSTEM,
                content=analysis_content,
                message_type=MessageType.LLM_ANALYSIS,
                sequence=1,
            )
            await self.db.commit()

            # 3. 学生知识数据 + 历史总体情绪（整个 session 冻结不变）
            section_ids = [s.id for s in sections]
            knowledge_data = await self._get_student_knowledge_data(
                session.student_id, section_ids,
            )
            emotion_history = await self.emotion.get_history(
                self.db, session.student_id, section_ids,
            )
            knowledge_content = self._format_knowledge_content(
                knowledge_data, emotion_history, sections,
            )
            await self._add_message(
                session_id=session_id,
                role=MessageRole.SYSTEM,
                content=knowledge_content,
                message_type=MessageType.STUDENT_DATA,
                sequence=2,
            )
            await self.db.commit()

            # 4. 即时情绪 + 教学策略（两者互不依赖，并行）
            instant, strategy_result = await asyncio.gather(
                self.emotion.detect_instant(
                    question_content, frame_base64,
                    student_id=session.student_id, session_id=session_id,
                ),
                self._get_teaching_strategy(
                    student_id=session.student_id,
                    session_id=session_id,
                    message=question_content,
                    sections=sections,
                    knowledge_data=knowledge_data,
                ),
            )
            await self._apply_instant_emotion(session_id, sequence=0, instant=instant)
            session.strategy = strategy_result.strategy
            await self._add_message(
                session_id=session_id,
                role=MessageRole.SYSTEM,
                content=self._format_strategy_content(strategy_result),
                message_type=MessageType.STRATEGY,
                sequence=3,
            )
            await self.db.commit()

            # 5. 相似度检索参考资料
            references = await self._search_references(
                question_content, session_id=session_id, sequence=4,
            )
            await self.db.commit()

            # 6. 组装 prompt，调用 LLM 生成初始回复
            assistant_content = await self._generate_teaching_response(
                session=session,
                question_content=question_content,
                sections=sections,
                knowledge_data=knowledge_data,
                emotion_history=emotion_history,
                instant_emotion=instant,
                strategy=strategy_result.strategy,
                references=references,
            )
            await self._add_message(
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                content=assistant_content,
                message_type=MessageType.CHAT,
                sequence=5,
            )

            session.pipeline_status = PipelineStatus.DONE
            await self.db.commit()
        except Exception:
            logger.exception("Teaching pipeline failed for session %s", session_id)
            await self.db.rollback()
            session.pipeline_status = PipelineStatus.FAILED
            try:
                next_seq = await self._get_next_sequence(session_id)
                await self._add_message(
                    session_id=session_id,
                    role=MessageRole.ASSISTANT,
                    content=_DEFAULT_ASSISTANT_REPLY,
                    message_type=MessageType.CHAT,
                    sequence=next_seq,
                )
            except Exception:
                logger.exception(
                    "Failed to write fallback reply for session %s", session_id,
                )
            await self.db.commit()
            raise

    async def start_session(
        self,
        student_id: int,
        question_content: str,
        question_image: str | None = None,
        frame_base64: str | None = None,
    ) -> TeachingSession:
        session = await self.create_session_shell(
            student_id=student_id,
            question_content=question_content,
            question_image=question_image,
        )
        await self.run_pipeline(session.id, question_content, question_image, frame_base64)
        return await self._get_session_with_messages(session.id)

    async def chat(
        self,
        session_id: int,
        user_message: str,
        frame_base64: str | None = None,
    ) -> tuple[TeachingMessage, list[TeachingReference]]:
        session = await self._get_session_with_messages(session_id)
        if not session:
            raise LookupError("Session not found")
        if session.status != TeachingSessionStatus.ACTIVE:
            raise ValueError(f"Session is not active (status={session.status.value})")

        await self._record_user_turn(session, user_message, frame_base64)

        assistant_content = await self._generate_chat_response(session_id)

        next_seq = await self._get_next_sequence(session_id)
        assistant_msg = await self._add_message(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=assistant_content,
            message_type=MessageType.CHAT,
            sequence=next_seq,
        )

        await self.db.flush()
        return assistant_msg, []

    async def chat_stream(
        self,
        session_id: int,
        user_message: str,
        frame_base64: str | None = None,
    ) -> AsyncIterator[str]:
        session = await self._get_session_with_messages(session_id)
        if not session:
            raise LookupError("Session not found")
        if session.status != TeachingSessionStatus.ACTIVE:
            raise ValueError(f"Session is not active (status={session.status.value})")

        await self._record_user_turn(session, user_message, frame_base64)
        await self.db.commit()

        llm_messages = await self._build_chat_messages(session_id)
        acc: list[str] = []
        try:
            async for delta in self.llm.chat_stream(llm_messages, temperature=0.7):
                acc.append(delta)
                yield delta
        except Exception as exc:
            logger.warning("LLM chat_stream failed: %s", exc)
            raise
        finally:
            assistant_content = "".join(acc) if acc else _DEFAULT_ASSISTANT_REPLY
            try:
                assistant_seq = await self._get_next_sequence(session_id)
                await self._add_message(
                    session_id=session_id,
                    role=MessageRole.ASSISTANT,
                    content=assistant_content,
                    message_type=MessageType.CHAT,
                    sequence=assistant_seq,
                )
                await self.db.commit()
            except Exception:
                logger.exception(
                    "Failed to persist assistant chat message for session %s", session_id,
                )

    async def end_session(
        self,
        session_id: int,
        mastery_level_delta: float | None = None,
        reason: SessionEndReason = SessionEndReason.USER,
    ) -> TeachingSession:
        session = await self._get_session_with_messages(session_id)
        if not session:
            raise LookupError("Session not found")
        if session.status != TeachingSessionStatus.ACTIVE:
            raise ValueError(f"Session is not active (status={session.status.value})")

        session.status = TeachingSessionStatus.COMPLETED
        session.ended_at = _utcnow()
        session.end_reason = reason

        if mastery_level_delta is None:
            mastery_level_delta = self._delta_from_self_rating(session)

        section_ids = self._extract_section_ids_from_session(session)
        await self._update_knowledge_summaries(
            student_id=session.student_id,
            section_ids=section_ids,
            mastery_level_delta=mastery_level_delta or 0.0,
        )

        instant_values = [
            m.emotion_value for m in session.messages
            if m.role == MessageRole.USER and m.emotion_value is not None
        ]
        await self.emotion.flow_back(
            self.db,
            student_id=session.student_id,
            section_ids=section_ids,
            session_id=session.id,
            instant_values=instant_values,
            start_time=session.created_at,
            end_time=session.ended_at,
        )

        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def end_idle_sessions(self, idle_minutes: int) -> list[int]:
        """最后一条消息超过 idle_minutes 的 active 会话自动结束并回流情绪"""
        cutoff = _utcnow() - timedelta(minutes=idle_minutes)
        last_msg_subq = (
            select(func.max(TeachingMessage.created_at))
            .where(TeachingMessage.session_id == TeachingSession.id)
            .correlate(TeachingSession)
            .scalar_subquery()
        )
        result = await self.db.execute(
            select(TeachingSession.id).where(
                TeachingSession.status == TeachingSessionStatus.ACTIVE,
                TeachingSession.pipeline_status.in_(
                    [PipelineStatus.DONE, PipelineStatus.FAILED],
                ),
                func.coalesce(last_msg_subq, TeachingSession.created_at) < cutoff,
            )
        )
        ended: list[int] = []
        for (session_id,) in result.all():
            try:
                await self.end_session(session_id, reason=SessionEndReason.IDLE)
                await self.db.commit()
                ended.append(session_id)
            except Exception:
                logger.exception("Failed to auto-end idle session %s", session_id)
                await self.db.rollback()
        return ended

    async def cancel_session(self, session_id: int) -> TeachingSession:
        session = await self._get_session_with_messages(session_id)
        if not session:
            raise LookupError("Session not found")
        if session.status != TeachingSessionStatus.ACTIVE:
            raise ValueError(f"Session is not active (status={session.status.value})")

        session.status = TeachingSessionStatus.CANCELLED
        session.ended_at = _utcnow()
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def get_session(self, session_id: int) -> TeachingSession | None:
        return await self._get_session_with_messages(session_id)

    async def list_sessions_by_student(
        self,
        student_id: int,
        limit: int,
        offset: int,
    ) -> list[tuple[TeachingSession, str | None, int]]:
        first_msg_subq = (
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
        message_count_subq = (
            select(func.count(TeachingMessage.id))
            .where(TeachingMessage.session_id == TeachingSession.id)
            .correlate(TeachingSession)
            .scalar_subquery()
        )

        stmt = (
            select(TeachingSession, first_msg_subq, message_count_subq)
            .where(TeachingSession.student_id == student_id)
            .order_by(TeachingSession.created_at.desc(), TeachingSession.id.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(stmt)
        rows = result.all()
        return [
            (session, self._truncate_preview(content), count or 0)
            for session, content, count in rows
        ]

    @staticmethod
    def _truncate_preview(content: str | None, length: int = 60) -> str | None:
        if not content:
            return None
        text = content.strip().replace("\n", " ")
        if len(text) <= length:
            return text
        return text[:length] + "…"

    # ------------------------------------------------------------------
    # 内部辅助方法
    # ------------------------------------------------------------------

    async def _get_session_with_messages(
        self, session_id: int,
    ) -> TeachingSession | None:
        result = await self.db.execute(
            select(TeachingSession)
            .where(TeachingSession.id == session_id)
            .options(
                selectinload(TeachingSession.messages)
                .selectinload(TeachingMessage.references),
            )
        )
        return result.scalar_one_or_none()

    async def _get_next_sequence(self, session_id: int) -> int:
        result = await self.db.execute(
            select(func.max(TeachingMessage.sequence))
            .where(TeachingMessage.session_id == session_id)
        )
        max_seq = result.scalar()
        return 0 if max_seq is None else max_seq + 1

    async def _add_message(
        self,
        session_id: int,
        role: MessageRole,
        content: str,
        message_type: MessageType,
        sequence: int,
    ) -> TeachingMessage:
        msg = TeachingMessage(
            session_id=session_id,
            role=role,
            content=content,
            message_type=message_type,
            sequence=sequence,
        )
        self.db.add(msg)
        await self.db.flush()
        await self.db.refresh(msg)
        return msg

    async def _record_user_turn(
        self,
        session: TeachingSession,
        user_message: str,
        frame_base64: str | None,
    ) -> None:
        """写入用户消息，并行取即时情绪与本轮策略，策略作为系统消息入库"""
        next_seq = await self._get_next_sequence(session.id)
        await self._add_message(
            session_id=session.id,
            role=MessageRole.USER,
            content=user_message,
            message_type=MessageType.CHAT,
            sequence=next_seq,
        )

        sections = await self._load_session_sections(session)
        knowledge_data = await self._get_student_knowledge_data(
            session.student_id, [s.id for s in sections],
        )
        instant, strategy_result = await asyncio.gather(
            self.emotion.detect_instant(
                user_message, frame_base64,
                student_id=session.student_id, session_id=session.id,
            ),
            self._get_teaching_strategy(
                student_id=session.student_id,
                session_id=session.id,
                message=user_message,
                sections=sections,
                knowledge_data=knowledge_data,
            ),
        )
        await self._apply_instant_emotion(session.id, sequence=next_seq, instant=instant)
        session.strategy = strategy_result.strategy
        await self._add_message(
            session_id=session.id,
            role=MessageRole.SYSTEM,
            content=self._format_strategy_content(strategy_result),
            message_type=MessageType.STRATEGY,
            sequence=next_seq + 1,
        )

    async def _apply_instant_emotion(
        self, session_id: int, sequence: int, instant: InstantEmotion,
    ) -> None:
        result = await self.db.execute(
            select(TeachingMessage).where(
                TeachingMessage.session_id == session_id,
                TeachingMessage.sequence == sequence,
            )
        )
        msg = result.scalar_one_or_none()
        if msg is None:
            return
        msg.facial_value = instant.facial
        msg.text_value = instant.text
        msg.emotion_value = instant.value
        await self.db.flush()

    async def _load_session_sections(self, session: TeachingSession) -> list[Section]:
        section_ids = self._extract_section_ids_from_session(session)
        if not section_ids:
            return []
        result = await self.db.execute(select(Section).where(Section.id.in_(section_ids)))
        return list(result.scalars().all())

    @staticmethod
    def _format_strategy_content(strategy_result: StrategyResult) -> str:
        return f"Strategy: {strategy_result.strategy}\nReason: {strategy_result.reason}"

    # ------------------------------------------------------------------
    # 知识点分析
    # ------------------------------------------------------------------

    async def _analyze_knowledge_points(
        self,
        question_content: str,
        question_image: str | None,
    ) -> list[Section]:
        result = await self.db.execute(select(Section))
        all_sections = result.scalars().all()

        if not all_sections:
            return []

        sections_text = "\n".join([
            f"ID: {s.id}, Title: {s.title}, Content: {s.content or ''}"
            for s in all_sections
        ])

        prompt = f"""You are a STEM education expert. Analyze the following student question and identify which knowledge points (sections) it relates to.

Available knowledge points:
{sections_text}

Student question: {question_content}

Respond with a JSON array of objects, each with "section_id" and "confidence" (0.0-1.0). Only include sections with confidence >= 0.5. Example:
[{{"section_id": 1, "confidence": 0.9}}, {{"section_id": 3, "confidence": 0.7}}]
"""

        messages = [{"role": "user", "content": prompt}]
        try:
            response_text = await self.llm.chat(messages, temperature=0.2)
        except Exception as exc:
            logger.warning("LLM knowledge-point analysis failed: %s", exc)
            return []

        section_ids = self._parse_section_ids(response_text)

        if section_ids:
            result = await self.db.execute(
                select(Section).where(Section.id.in_(section_ids))
            )
            return list(result.scalars().all())
        return []

    def _parse_section_ids(self, response_text: str) -> list[int]:
        try:
            match = re.search(r"\[.*\]", response_text, re.DOTALL)
            if match:
                data = json.loads(match.group())
                return [
                    item["section_id"]
                    for item in data
                    if item.get("confidence", 0) >= 0.5
                ]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            logger.warning("Failed to parse section ids: %s", exc)
        return []

    def _format_analysis_content(self, sections: list[Section]) -> str:
        if not sections:
            return "No knowledge points identified."
        return "Identified knowledge points:\n" + "\n".join([
            f"- {s.id}: {s.title}" for s in sections
        ])

    # ------------------------------------------------------------------
    # 学生知识数据
    # ------------------------------------------------------------------

    async def _get_student_knowledge_data(
        self,
        student_id: int,
        section_ids: list[int],
    ) -> list[StudentKnowledgeSummary]:
        if not section_ids:
            return []

        result = await self.db.execute(
            select(StudentKnowledgeSummary)
            .where(
                StudentKnowledgeSummary.student_id == student_id,
                StudentKnowledgeSummary.section_id.in_(section_ids),
            )
        )
        return list(result.scalars().all())

    def _format_knowledge_content(
        self,
        summaries: list[StudentKnowledgeSummary],
        emotion_history: dict[int, StudentKpEmotion] | None = None,
        sections: list[Section] | None = None,
    ) -> str:
        parts: list[str] = []
        if not summaries:
            parts.append("No prior knowledge data for related sections.")
        else:
            lines = []
            for s in summaries:
                error_rate = 0.0
                if s.total_practice_count > 0:
                    error_rate = 1.0 - (s.correct_count / s.total_practice_count)
                lines.append(
                    f"Section {s.section_id}: mastery={s.mastery_level:.2f}, "
                    f"correct={s.correct_count}, practice={s.total_practice_count}, "
                    f"teaching={s.total_teaching_count}, error_rate={error_rate:.2f}"
                )
            parts.append("Student knowledge data:\n" + "\n".join(lines))
        parts.append(self._format_emotion_history(emotion_history or {}, sections or []))
        return "\n\n".join(parts)

    @staticmethod
    def _format_emotion_history(
        emotion_history: dict[int, StudentKpEmotion], sections: list[Section],
    ) -> str:
        if not sections:
            return "Emotion history: none."
        lines = []
        for sec in sections:
            row = emotion_history.get(sec.id)
            if row:
                lines.append(
                    f"- {sec.title}: {describe_value(row.emotion_value)} "
                    f"({row.emotion_value:.1f}/5, {row.sample_count} sessions)"
                )
            else:
                lines.append(f"- {sec.title}: 无记录")
        return "Emotion history (1=自信 … 5=非常受挫):\n" + "\n".join(lines)

    # ------------------------------------------------------------------
    # 教学策略
    # ------------------------------------------------------------------

    async def _get_teaching_strategy(
        self,
        student_id: int,
        session_id: int,
        message: str,
        sections: list[Section],
        knowledge_data: list[StudentKnowledgeSummary],
    ) -> StrategyResult:
        if self.strategy_client.is_configured():
            try:
                return await self.strategy_client.get_strategy(
                    student_id=student_id,
                    session_id=session_id,
                    message=message,
                )
            except Exception as exc:
                logger.warning("Teaching strategy MCP failed: %s", exc)

        try:
            return await self._fallback_strategy(
                student_id=student_id,
                sections=sections,
                knowledge_data=knowledge_data,
            )
        except Exception as exc:
            logger.warning("Fallback strategy LLM failed: %s", exc)
            return _DEFAULT_STRATEGY

    async def _fallback_strategy(
        self,
        student_id: int,
        sections: list[Section],
        knowledge_data: list[StudentKnowledgeSummary],
    ) -> StrategyResult:
        prompt = f"""As a teaching strategy advisor, recommend a teaching approach for a student based on their profile.

Student ID: {student_id}
Topics: {[s.title for s in sections]}
Knowledge Data: {[
    {
        "section_id": s.section_id,
        "mastery": s.mastery_level,
        "practice": s.total_practice_count,
        "teaching": s.total_teaching_count,
    }
    for s in knowledge_data
]}

Respond in this exact format:
Strategy: <brief strategy name/description>
Reason: <one sentence reason>
"""

        messages = [{"role": "user", "content": prompt}]
        response = await self.llm.chat(messages, temperature=0.3)

        strategy = "Adaptive guided inquiry"
        reason = "Default strategy based on student profile."

        for line in response.split("\n"):
            if line.startswith("Strategy:"):
                strategy = line.replace("Strategy:", "").strip()
            elif line.startswith("Reason:"):
                reason = line.replace("Reason:", "").strip()

        return StrategyResult(strategy=strategy, reason=reason)

    # ------------------------------------------------------------------
    # 参考资料检索
    # ------------------------------------------------------------------

    async def _search_references(
        self,
        question_content: str,
        session_id: int,
        sequence: int,
    ) -> list[tuple]:
        similarity_threshold = settings.teaching_reference_similarity_threshold
        distance_threshold = max(0.0, 1.0 - similarity_threshold)
        try:
            results = await self.question_service.search_by_text(
                self.db, question_content, limit=1, threshold=distance_threshold,
            )
        except Exception as exc:
            logger.warning("Reference search failed: %s", exc)
            results = []

        ref_content = self._format_references_block(results, similarity_threshold)
        msg = await self._add_message(
            session_id=session_id,
            role=MessageRole.SYSTEM,
            content=ref_content,
            message_type=MessageType.REFERENCE_SEARCH,
            sequence=sequence,
        )

        for question, distance in results:
            score = max(0.0, min(1.0, 1.0 - distance))
            ref = TeachingReference(
                message_id=msg.id,
                question_id=question.id,
                similarity_score=round(score, 4),
            )
            self.db.add(ref)

        await self.db.flush()
        return results

    @staticmethod
    def _format_references_block(
        results: list[tuple],
        similarity_threshold: float,
    ) -> str:
        if not results:
            return (
                f"No reference question with similarity >= {similarity_threshold:.2f} found."
            )
        lines = [
            f"Reference question (top-1 by semantic similarity, threshold {similarity_threshold:.2f}):"
        ]
        for q, dist in results:
            score = max(0.0, min(1.0, 1.0 - dist))
            lines.append(f"\n[Q{q.id}] similarity={score:.3f}")
            lines.append(f"Content: {q.content}")
            lines.append(f"Answer: {q.answer}")
            if q.analysis:
                lines.append(f"Analysis: {q.analysis}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # LLM 响应生成
    # ------------------------------------------------------------------

    async def _generate_teaching_response(
        self,
        session: TeachingSession,
        question_content: str,
        sections: list[Section],
        knowledge_data: list[StudentKnowledgeSummary],
        emotion_history: dict[int, StudentKpEmotion],
        instant_emotion: InstantEmotion,
        strategy: str,
        references: list[tuple] | None = None,
    ) -> str:
        system_prompt = self._build_system_prompt(
            strategy=strategy,
            sections=sections,
            knowledge_data=knowledge_data,
            emotion_history=emotion_history,
            instant_emotion=instant_emotion,
            references=references,
            explain_style=await self._student_explain_style(session.student_id),
            persona=session.persona,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Student question: {question_content}"},
        ]

        try:
            return await self.llm.chat(messages, temperature=0.7)
        except Exception as exc:
            logger.warning("LLM teaching response failed: %s", exc)
            return _DEFAULT_ASSISTANT_REPLY

    async def _generate_chat_response(self, session_id: int) -> str:
        llm_messages = await self._build_chat_messages(session_id)
        try:
            return await self.llm.chat(llm_messages, temperature=0.7)
        except Exception as exc:
            logger.warning("LLM chat response failed: %s", exc)
            return _DEFAULT_ASSISTANT_REPLY

    async def _student_explain_style(self, student_id: int) -> ExplainStyle | None:
        result = await self.db.execute(
            select(Student.explain_style).where(Student.id == student_id)
        )
        return result.scalar_one_or_none()

    async def _explain_style_guidance(self, session_id: int) -> str | None:
        result = await self.db.execute(
            select(Student.explain_style)
            .join(TeachingSession, TeachingSession.student_id == Student.id)
            .where(TeachingSession.id == session_id)
        )
        style = result.scalar_one_or_none()
        return _EXPLAIN_STYLE_GUIDANCE[style] if style else None

    async def _build_chat_messages(self, session_id: int) -> list[dict]:
        result = await self.db.execute(
            select(TeachingMessage)
            .where(TeachingMessage.session_id == session_id)
            .order_by(TeachingMessage.sequence)
        )
        messages = list(result.scalars().all())

        strategy_content = ""
        reference_content = ""
        student_data_content = ""
        latest_user: TeachingMessage | None = None
        for msg in messages:
            if msg.message_type == MessageType.STRATEGY:
                strategy_content = msg.content
            elif msg.message_type == MessageType.REFERENCE_SEARCH:
                reference_content = msg.content
            elif msg.message_type == MessageType.STUDENT_DATA:
                student_data_content = msg.content
            if msg.role == MessageRole.USER:
                latest_user = msg

        system_parts = [
            "You are an expert STEM tutor. Your goal is to help the student understand concepts through guided inquiry.",
        ]
        if strategy_content:
            system_parts.append(f"\n{strategy_content}")
        if student_data_content:
            system_parts.append(f"\n{student_data_content}")
        if latest_user is not None and latest_user.emotion_value is not None:
            instant = InstantEmotion(latest_user.facial_value, latest_user.text_value)
            system_parts.append(f"\n学生当前状态：{instant.describe()}")
        if reference_content and not reference_content.startswith("No reference question"):
            system_parts.append(f"\n{reference_content}")
        system_parts.append(_EMOTION_GUIDANCE)
        style_guidance = await self._explain_style_guidance(session_id)
        if style_guidance:
            system_parts.append(style_guidance)
        persona = (
            await self.db.execute(select(TeachingSession.persona).where(TeachingSession.id == session_id))
        ).scalar_one_or_none()
        system_parts.append(persona_prompt(
            persona,
            soften=is_frustrated(latest_user.emotion_value if latest_user else None),
        ))

        llm_messages = [{"role": "system", "content": "\n".join(system_parts)}]
        for msg in messages:
            if msg.message_type in (MessageType.QUESTION_SUBMIT, MessageType.CHAT):
                llm_messages.append({
                    "role": msg.role.value,
                    "content": msg.content,
                })
        return llm_messages

    def _build_system_prompt(
        self,
        strategy: str,
        sections: list[Section],
        knowledge_data: list[StudentKnowledgeSummary],
        emotion_history: dict[int, StudentKpEmotion] | None = None,
        instant_emotion: InstantEmotion | None = None,
        references: list[tuple] | None = None,
        explain_style: ExplainStyle | None = None,
        persona: Persona | None = None,
    ) -> str:
        prompt_parts = [
            "You are an expert STEM tutor. Your goal is to help the student understand concepts through guided inquiry.",
            f"\nTeaching Strategy: {strategy}",
            "\nRelevant Knowledge Points:",
        ]

        for section in sections:
            prompt_parts.append(f"- {section.title}: {section.content or 'No description'}")

        if knowledge_data:
            prompt_parts.append("\nStudent's Prior Knowledge:")
            for summary in knowledge_data:
                error_rate = 0.0
                if summary.total_practice_count > 0:
                    error_rate = 1.0 - (summary.correct_count / summary.total_practice_count)
                prompt_parts.append(
                    f"- Section {summary.section_id}: mastery {summary.mastery_level:.0%}, "
                    f"practiced {summary.total_practice_count} times, "
                    f"error rate {error_rate:.0%}"
                )

        prompt_parts.append("\n" + self._format_emotion_history(emotion_history or {}, sections))
        if instant_emotion is not None and instant_emotion.value is not None:
            prompt_parts.append(f"\n学生当前状态：{instant_emotion.describe()}")

        if references:
            prompt_parts.append(
                "\n" + self._format_references_block(
                    references, settings.teaching_reference_similarity_threshold,
                )
            )
            prompt_parts.append(
                "Use this reference problem to inform your guidance, but do NOT copy its answer verbatim — "
                "adapt the reasoning to the student's question."
            )

        prompt_parts.append(
            "\nInstructions: Guide the student to discover the answer. "
            "Ask probing questions. Do not give the full answer immediately. "
            "Adapt your approach based on the teaching strategy and student's knowledge level."
        )
        prompt_parts.append(_EMOTION_GUIDANCE)
        if explain_style is not None:
            prompt_parts.append(_EXPLAIN_STYLE_GUIDANCE[explain_style])
        prompt_parts.append(persona_prompt(
            persona,
            soften=is_frustrated(instant_emotion.value if instant_emotion else None),
        ))

        return "\n".join(prompt_parts)

    # ------------------------------------------------------------------
    # 会话结束：知识点更新
    # ------------------------------------------------------------------

    @staticmethod
    def _delta_from_self_rating(session: TeachingSession) -> float | None:
        """取最后一条带自评的 AI 回复，映射为掌握度变化；没有自评则不变"""
        rated = [
            m for m in session.messages
            if m.role == MessageRole.ASSISTANT and m.self_rating is not None
        ]
        if not rated:
            return None
        latest = max(rated, key=lambda m: m.sequence)
        return _SELF_RATING_DELTA.get(latest.self_rating)

    def _extract_section_ids_from_session(
        self, session: TeachingSession,
    ) -> list[int]:
        for msg in session.messages:
            if msg.message_type == MessageType.LLM_ANALYSIS:
                ids = re.findall(r"- (\d+):", msg.content)
                return [int(i) for i in ids]
        return []

    async def _update_knowledge_summaries(
        self,
        student_id: int,
        section_ids: list[int],
        mastery_level_delta: float,
    ) -> None:
        now = _utcnow()

        for section_id in section_ids:
            result = await self.db.execute(
                select(StudentKnowledgeSummary)
                .where(
                    StudentKnowledgeSummary.student_id == student_id,
                    StudentKnowledgeSummary.section_id == section_id,
                )
            )
            summary = result.scalar_one_or_none()

            if summary:
                summary.total_teaching_count += 1
                summary.last_teaching_at = now
                if mastery_level_delta:
                    summary.mastery_level = max(
                        0.0, min(1.0, summary.mastery_level + mastery_level_delta),
                    )
            else:
                summary = StudentKnowledgeSummary(
                    student_id=student_id,
                    section_id=section_id,
                    mastery_level=max(0.0, min(1.0, mastery_level_delta)),
                    correct_count=0,
                    total_practice_count=0,
                    total_teaching_count=1,
                    last_practice_at=None,
                    last_teaching_at=now,
                )
                self.db.add(summary)

        await self.db.flush()
