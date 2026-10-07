import asyncio
import json
import logging

from mcp import ClientSession
from mcp.client.streamable_http import create_mcp_http_client, streamable_http_client

from app.config import settings

logger = logging.getLogger(__name__)

EVALUATION_TOOL_NAME = "get_student_evaluation"


class EvaluationResult:
    def __init__(self, evaluation: str, highlights: list[str] | None = None) -> None:
        self.evaluation = evaluation
        self.highlights = highlights or []


class EvaluationClient:
    """评价处 MCP 客户端。

    契约见 docs/design/mcp-evaluation-contract.md：
    tool get_student_evaluation(student_id) -> {"evaluation": str, "highlights": [str]}
    评价服务自己连数据库读学生数据，后端只传 student_id。
    """

    def __init__(self) -> None:
        self._url = settings.evaluation_mcp_url
        self._api_key = settings.evaluation_api_key
        self._timeout = settings.evaluation_timeout_seconds

    def is_configured(self) -> bool:
        return bool(self._url)

    async def get_evaluation(self, student_id: int) -> EvaluationResult:
        if not self._url:
            raise ValueError("Evaluation MCP URL not configured")

        headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else None

        async def _call() -> EvaluationResult:
            async with create_mcp_http_client(headers=headers) as http_client:
                async with streamable_http_client(self._url, http_client=http_client) as (read, write):
                    async with ClientSession(read, write) as mcp:
                        await mcp.initialize()
                        result = await mcp.call_tool(EVALUATION_TOOL_NAME, {"student_id": student_id})
            return self._parse(result)

        return await asyncio.wait_for(_call(), timeout=self._timeout)

    @staticmethod
    def _parse(result) -> EvaluationResult:
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
                data = {"evaluation": text}

        evaluation = str(data.get("evaluation", "")).strip()
        if not evaluation:
            raise RuntimeError("MCP tool returned empty evaluation")
        highlights = data.get("highlights") or []
        return EvaluationResult(
            evaluation=evaluation,
            highlights=[str(h) for h in highlights if str(h).strip()],
        )
