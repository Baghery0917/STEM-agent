import asyncio
import base64
import logging
import re
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.external.emotion import (
    EmotionCategory,
    EmotionClient,
    EMOTION_VALUE,
    describe_value,
)
from app.llm.client import LLMClient
from app.models.emotion import EmotionLog, EmotionMode, StudentKpEmotion

logger = logging.getLogger(__name__)

_TEXT_PROMPT = """判断下面这句学生在学习物理时说的话所反映的情绪，只能从以下五类中选一个：
confident / slightly_uncertain / discouraged / frustrated / very_frustrated

学生的话：
{text}

只输出类别英文标识，不要输出其他内容。"""

_CATEGORY_RE = re.compile(
    r"very_frustrated|frustrated|discouraged|slightly_uncertain|confident", re.I,
)


class InstantEmotion:
    def __init__(self, facial: float | None, text: float | None) -> None:
        self.facial = facial
        self.text = text

    @property
    def value(self) -> float | None:
        w = settings.emotion_facial_weight
        if self.facial is not None and self.text is not None:
            return round(self.facial * w + self.text * (1 - w), 3)
        if self.facial is not None:
            return self.facial
        return self.text

    def describe(self) -> str | None:
        value = self.value
        if value is None:
            return None
        parts = []
        if self.facial is not None:
            parts.append(f"面部 {self.facial:.0f}")
        if self.text is not None:
            parts.append(f"文本 {self.text:.0f}")
        return f"{describe_value(value)}（{'，'.join(parts)}）"


class EmotionService:
    def __init__(self, llm: LLMClient | None = None, facial: EmotionClient | None = None) -> None:
        self.llm = llm or LLMClient()
        self.facial = facial or EmotionClient()

    # ------------------------------------------------------------------
    # 即时情绪
    # ------------------------------------------------------------------

    async def detect_instant(
        self,
        text: str,
        frame_base64: str | None,
        *,
        student_id: int,
        session_id: int | None = None,
    ) -> InstantEmotion:
        facial_task = asyncio.create_task(self._detect_facial(frame_base64, student_id))
        text_task = asyncio.create_task(self._detect_text(text, student_id, session_id))
        facial, text_value = await asyncio.gather(facial_task, text_task)
        return InstantEmotion(facial=facial, text=text_value)

    async def detect_facial(self, frame_base64: str | None, *, student_id: int) -> float | None:
        """只做面部识别（练习提交时用，没有文本可分析）"""
        return await self._detect_facial(frame_base64, student_id)

    async def _detect_facial(self, frame_base64: str | None, student_id: int) -> float | None:
        if not frame_base64 or not self.facial.is_configured():
            return None
        try:
            image_bytes = _decode_frame(frame_base64)
            result = await self.facial.recognize(image_bytes, student_id=student_id)
            return result.value
        except Exception as exc:
            logger.warning("Facial emotion recognition failed: %s", exc)
            return None

    async def _detect_text(
        self, text: str, student_id: int, session_id: int | None,
    ) -> float | None:
        if not text.strip():
            return None
        try:
            response = await self.llm.chat(
                [{"role": "user", "content": _TEXT_PROMPT.format(text=text.strip())}],
                temperature=0.0,
                context={"student_id": student_id, "teaching_session_id": session_id},
            )
        except Exception as exc:
            logger.warning("Text emotion classification failed: %s", exc)
            return None
        match = _CATEGORY_RE.search(response or "")
        if not match:
            logger.warning("Unrecognized text emotion response: %r", response)
            return None
        return EMOTION_VALUE[EmotionCategory(match.group(0).lower())]

    # ------------------------------------------------------------------
    # 历史总体情绪
    # ------------------------------------------------------------------

    async def get_history(
        self, db: AsyncSession, student_id: int, section_ids: list[int],
    ) -> dict[int, StudentKpEmotion]:
        if not section_ids:
            return {}
        result = await db.execute(
            select(StudentKpEmotion).where(
                StudentKpEmotion.student_id == student_id,
                StudentKpEmotion.section_id.in_(section_ids),
            )
        )
        return {row.section_id: row for row in result.scalars().all()}

    async def flow_back(
        self,
        db: AsyncSession,
        *,
        student_id: int,
        section_ids: list[int],
        session_id: int,
        instant_values: list[float],
        start_time: datetime,
        end_time: datetime,
        mode: EmotionMode = EmotionMode.TEACHING,
    ) -> float | None:
        """会话结束：即时情绪均值以指数平滑回流到知识点历史，并写一行情绪图谱流水"""
        values = [v for v in instant_values if v is not None]
        if not values or not section_ids:
            return None
        session_value = round(sum(values) / len(values), 3)
        alpha = settings.emotion_history_alpha

        existing = await self.get_history(db, student_id, section_ids)
        for section_id in section_ids:
            row = existing.get(section_id)
            if row:
                row.emotion_value = round(
                    row.emotion_value * (1 - alpha) + session_value * alpha, 3,
                )
                row.sample_count += 1
            else:
                db.add(StudentKpEmotion(
                    student_id=student_id,
                    section_id=section_id,
                    emotion_value=session_value,
                    sample_count=1,
                ))
            db.add(EmotionLog(
                student_id=student_id,
                section_id=section_id,
                mode=mode,
                session_id=session_id,
                emotion_value=session_value,
                start_time=start_time,
                end_time=end_time,
            ))
        await db.flush()
        return session_value


def _decode_frame(frame_base64: str) -> bytes:
    payload = frame_base64.split(",", 1)[1] if frame_base64.startswith("data:") else frame_base64
    return base64.b64decode(payload)
