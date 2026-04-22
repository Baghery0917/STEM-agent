import httpx

from app.config import settings


class StrategyResult:
    def __init__(self, strategy: str, reason: str) -> None:
        self.strategy = strategy
        self.reason = reason


class TeachingStrategyClient:
    """教学策略外部服务客户端"""

    def __init__(self) -> None:
        self._base_url = settings.teaching_strategy_base_url
        self._api_key = settings.teaching_strategy_api_key

    def is_configured(self) -> bool:
        return bool(self._base_url)

    async def get_strategy(
        self,
        student_id: int,
        emotion_category: str | None = None,
        current_topic: str | None = None,
        performance_history: list[dict] | None = None,
    ) -> StrategyResult:
        """获取针对学生的推荐教学策略。

        Args:
            student_id: 学生 ID
            emotion_category: 当前情绪类别（如 confident, frustrated）
            current_topic: 当前学习主题
            performance_history: 历史表现数据

        Returns:
            StrategyResult: 推荐的教学策略及理由

        Raises:
            ValueError: base_url 未配置
            httpx.HTTPError: HTTP 请求失败
        """
        if not self._base_url:
            raise ValueError("Teaching strategy base URL not configured")

        headers = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload = {
            "student_id": student_id,
            "emotion_category": emotion_category,
            "current_topic": current_topic,
            "performance_history": performance_history or [],
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self._base_url}/strategy",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

        return StrategyResult(
            strategy=data.get("strategy", "Adaptive guided inquiry"),
            reason=data.get("reason", "Default strategy from external service"),
        )
