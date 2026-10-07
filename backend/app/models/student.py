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


class Persona(str, enum.Enum):
    """讲师人格：只改变语气，不改变教学决策"""

    LEONARD = "leonard"
    PENNY = "penny"
    HOWARD = "howard"
    RAJ = "raj"
    BERNADETTE = "bernadette"
    AMY = "amy"
    SHELDON = "sheldon"


class Student(BaseModel):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    gender: Mapped[Gender] = mapped_column(Enum(Gender), nullable=False)
    explain_style: Mapped[ExplainStyle | None] = mapped_column(
        Enum(ExplainStyle), nullable=True,
    )
    # 为空等于 Leonard
    persona: Mapped[Persona | None] = mapped_column(Enum(Persona), nullable=True)
