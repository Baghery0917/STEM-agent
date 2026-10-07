from typing import Literal

from pydantic import BaseModel


class StudentEvaluation(BaseModel):
    student_id: int
    evaluation: str | None = None
    highlights: list[str] = []
    # mcp: 来自评价处；unavailable: 未配置或调用失败
    source: Literal["mcp", "unavailable"]
    detail: str | None = None
