"""本地联调用的假教学策略 MCP 服务端，契约见 docs/design/mcp-strategy-contract.md

用法: cd backend && .venv/bin/python -m scripts.fake_strategy_server [--port 8100]
"""
import argparse

import uvicorn
from mcp.server.mcpserver import MCPServer

server = MCPServer(name="fake-teaching-strategy")

_RULES = [
    ("不对", "先让学生自己找错，不直接给答案"),
    ("不懂", "放慢节奏，用一个生活类比切入"),
    ("为什么", "先追问学生的直觉，再引出原理"),
    ("直接", "给完整过程，但每一步后停顿确认"),
]


@server.tool()
def get_teaching_strategy(student_id: int, session_id: int, message: str) -> dict:
    """根据学生 id、会话 id 和学生这句话返回一条简短教学策略"""
    for keyword, strategy in _RULES:
        if keyword in message:
            return {"strategy": strategy, "reason": f"matched '{keyword}'"}
    return {"strategy": "引导式提问，一次只推进一步", "reason": "default"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8100)
    args = parser.parse_args()
    uvicorn.run(server.streamable_http_app(), host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
