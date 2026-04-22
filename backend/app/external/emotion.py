import enum

from app.config import settings


class EmotionCategory(str, enum.Enum):
    """学生情绪类别"""

    CONFIDENT = "confident"
    SLIGHTLY_UNCERTAIN = "slightly_uncertain"
    DISCOURAGED = "discouraged"
    FRUSTRATED = "frustrated"
    VERY_FRUSTRATED = "very_frustrated"


class EmotionResult:
    def __init__(self, category: EmotionCategory, confidence: float) -> None:
        self.category = category
        self.confidence = confidence


class EmotionClient:
    """情绪识别外部服务客户端

    预留接口：通过 HTTP API 调用外部情绪识别服务，
    根据学生交互数据判断当前情绪类别。
    """

    def __init__(self) -> None:
        self._base_url = settings.emotion_base_url
        self._api_key = settings.emotion_api_key

    async def recognize(self, student_id: int, interaction_text: str) -> EmotionResult:
        """识别学生情绪。

        Args:
            student_id: 学生 ID
            interaction_text: 学生的交互文本（如答题过程、对话内容）

        Returns:
            EmotionResult: 情绪类别及置信度

        Raises:
            NotImplementedError: 具体实现待接入外部服务
        """
        raise NotImplementedError("Emotion recognition service not implemented yet")
