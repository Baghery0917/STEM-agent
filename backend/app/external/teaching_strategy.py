import asyncio
import json
import logging

from mcp import ClientSession
from mcp.client.streamable_http import create_mcp_http_client, streamable_http_client

from app.config import settings

logger = logging.getLogger(__name__)

STRATEGY_TOOL_NAME = "get_teaching_strategy"


class StrategyResult:
    def __init__(self, strategy: str, reason: str) -> None:
        self.strategy = strategy
        self.reason = reason


class TeachingStrategyClient:
    """教学策略 MCP 客户端。

    契约见 docs/design/mcp-strategy-contract.md：
    tool get_teaching_strategy(student_id, session_id, message) -> {"strategy": str}
    """

    def __init__(self) -> None:
        self._url = settings.teaching_strategy_mcp_url
        self._api_key = settings.teaching_strategy_api_key
        self._timeout = settings.teaching_strategy_timeout_seconds

    def is_configured(self) -> bool:
        return bool(self._url)

    async def get_strategy(
        self,
        student_id: int,
        session_id: int,
        message: str,
    ) -> StrategyResult:
        if not self._url:
            raise ValueError("Teaching strategy MCP URL not configured")

        headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else None
        arguments = {
            "student_id": student_id,
            "session_id": session_id,
            "message": message,
        }

        async def _call() -> StrategyResult:
            async with create_mcp_http_client(headers=headers) as http_client:
                async with streamable_http_client(self._url, http_client=http_client) as (read, write):
                    async with ClientSession(read, write) as mcp:
                        await mcp.initialize()
                        result = await mcp.call_tool(STRATEGY_TOOL_NAME, arguments)
            return self._parse(result)

        return await asyncio.wait_for(_call(), timeout=self._timeout)

    @staticmethod
    def _parse(result) -> StrategyResult:
        if getattr(result, "is_error", False):
            raise RuntimeError(f"MCP tool error: {result.content}")

        data = getattr(result, "structured_content", None)
        if not data:
            text = next(
                (c.text for c in result.content if getattr(c, "type", None) == "text"),
                None,
            )
            if text is None:
                raise RuntimeError("MCP tool returned no content")
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                data = {"strategy": text}

        strategy = str(data.get("strategy", "")).strip()
        if not strategy:
            raise RuntimeError("MCP tool returned empty strategy")
        return StrategyResult(
            strategy=strategy,
            reason=str(data.get("reason", "")).strip() or "From strategy service",
        )
