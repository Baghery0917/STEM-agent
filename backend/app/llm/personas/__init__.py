"""讲师人格 prompt：只注入语气，不碰教学决策。"""
from functools import lru_cache
from pathlib import Path

from app.models.student import Persona

_DIR = Path(__file__).parent
DEFAULT_PERSONA = Persona.LEONARD

# 语言硬约束：讲题中文，英文只做点缀
_LANGUAGE_RULE = (
    "\n语言规则（必须遵守）：全部用中文回答，包括口头禅。不要出现英文句子或英文口头禅，"
    "物理量符号和单位（如 N、m/s²、cos30°）除外。口头禅每条消息最多一句，放在开头或结尾。"
)

# 情绪安全阀：学生受挫时去掉调侃，只保留语气标识
_SOFTEN_RULE = (
    "\n降温规则：学生此刻状态偏向受挫。本条回复去掉所有调侃、挑剔和自我吹嘘，"
    "口头禅只保留鼓励性的那一句或干脆不用，语气标识保留但收敛。"
    "Sheldon 在这种状态下不说「逗你玩的」。"
)


@lru_cache(maxsize=None)
def _load(persona: Persona) -> str:
    return (_DIR / f"{persona.value}.md").read_text(encoding="utf-8").strip()


def persona_prompt(persona: Persona | None, *, soften: bool = False) -> str:
    """返回拼进 system prompt 的人格段落。persona 为空用默认讲师。"""
    body = _load(persona or DEFAULT_PERSONA)
    parts = ["\n讲师人格（只决定语气，教学策略与讲解风格仍以上面的设置为准）：", body, _LANGUAGE_RULE]
    if soften:
        parts.append(_SOFTEN_RULE)
    return "\n".join(parts)


def is_frustrated(emotion_value: float | None) -> bool:
    """与 _EMOTION_GUIDANCE 的阈值一致：>=3 视为受挫"""
    return emotion_value is not None and emotion_value >= 3
