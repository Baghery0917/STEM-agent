import enum

from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class ExplainStyle(str, enum.Enum):
    """学生手动覆盖的讲解风格；为空时完全由教学策略模块决定"""

    DIRECT = "direct"      # 直接给答案
    GUIDED = "guided"      # 引导我自己找
    HINT = "hint"          # 只给提示


class Student(BaseModel):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    gender: Mapped[Gender] = mapped_column(Enum(Gender), nullable=False)
    explain_style: Mapped[ExplainStyle | None] = mapped_column(
        Enum(ExplainStyle), nullable=True,
    )
