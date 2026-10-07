from datetime import datetime
from typing import Literal

from pydantic import BaseModel

ReportMode = Literal["recent", "all"]


class KnowledgePointMastery(BaseModel):
    section_id: int
    section_title: str
    mastery_level: float
    correct_count: int
    total_practice_count: int
    total_teaching_count: int
    last_practice_at: datetime | None = None
    last_teaching_at: datetime | None = None
    # 近 7 天内练习/教学次数（all 模式为 0）
    recent_practice_count: int = 0
    recent_teaching_count: int = 0


class EmotionLogEntry(BaseModel):
    section_id: int
    section_title: str
    mode: Literal["teaching", "practice"]
    session_id: int | None = None
    emotion_value: float
    emotion: str
    created_at: datetime


class EmotionDay(BaseModel):
    """按天聚合的情绪均值，1=自信 … 5=非常受挫；没有记录的天 value 为 None"""

    date: str
    value: float | None = None
    count: int = 0


class StudentReport(BaseModel):
    mode: ReportMode
    range_start: datetime
    range_end: datetime
    practice_count: int
    teaching_count: int
    answered_count: int
    correct_count: int
    knowledge_points: list[KnowledgePointMastery]
    emotion_days: list[EmotionDay]
    emotion_logs: list[EmotionLogEntry]
    # LLM 生成的一段话总结，失败时为空
    summary: str | None = None
