import enum

import httpx

from app.config import settings


class EmotionCategory(str, enum.Enum):
    CONFIDENT = "confident"
    SLIGHTLY_UNCERTAIN = "slightly_uncertain"
    DISCOURAGED = "discouraged"
    FRUSTRATED = "frustrated"
    VERY_FRUSTRATED = "very_frustrated"


# PRD 五档：1 自信 … 5 非常受挫
EMOTION_VALUE: dict[EmotionCategory, float] = {
    EmotionCategory.CONFIDENT: 1.0,
    EmotionCategory.SLIGHTLY_UNCERTAIN: 2.0,
    EmotionCategory.DISCOURAGED: 3.0,
    EmotionCategory.FRUSTRATED: 4.0,
    EmotionCategory.VERY_FRUSTRATED: 5.0,
}

EMOTION_LABEL_ZH: dict[EmotionCategory, str] = {
    EmotionCategory.CONFIDENT: "自信",
    EmotionCategory.SLIGHTLY_UNCERTAIN: "略犹豫",
    EmotionCategory.DISCOURAGED: "气馁",
    EmotionCategory.FRUSTRATED: "受挫",
    EmotionCategory.VERY_FRUSTRATED: "非常受挫",
}


def value_to_category(value: float) -> EmotionCategory:
    idx = int(round(max(1.0, min(5.0, value)))) - 1
    return list(EmotionCategory)[idx]


def describe_value(value: float) -> str:
    return EMOTION_LABEL_ZH[value_to_category(value)]


class EmotionResult:
    def __init__(self, category: EmotionCategory, confidence: float) -> None:
        self.category = category
        self.confidence = confidence

    @property
    def value(self) -> float:
        return EMOTION_VALUE[self.category]


class EmotionClient:
    """面部情绪识别 HTTP 客户端。

    契约：POST {base_url}/recognize，multipart 字段 image（jpeg），
    返回 {"emotion": "<category>", "confidence": 0.0-1.0}。
    """

    def __init__(self) -> None:
        self._base_url = settings.emotion_base_url.rstrip("/")
        self._api_key = settings.emotion_api_key
        self._timeout = settings.emotion_timeout_seconds

    def is_configured(self) -> bool:
        return bool(self._base_url)

    async def recognize(self, image_bytes: bytes, student_id: int | None = None) -> EmotionResult:
        if not self._base_url:
            raise ValueError("Emotion base URL not configured")

        headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}
        data = {"student_id": str(student_id)} if student_id is not None else {}

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/recognize",
                files={"image": ("frame.jpg", image_bytes, "image/jpeg")},
                data=data,
                headers=headers,
            )
            response.raise_for_status()
            payload = response.json()

        category = EmotionCategory(str(payload["emotion"]).strip().lower())
        confidence = float(payload.get("confidence", 1.0))
        return EmotionResult(category=category, confidence=confidence)
