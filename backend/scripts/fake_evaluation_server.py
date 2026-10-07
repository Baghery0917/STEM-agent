"""本地联调用的假评价处 MCP 服务端，契约见 docs/design/mcp-evaluation-contract.md

用法: cd backend && .venv/bin/python -m scripts.fake_evaluation_server [--port 8200]
"""
import argparse

import uvicorn
from mcp.server.mcpserver import MCPServer

server = MCPServer(name="fake-evaluation")


@server.tool()
def get_student_evaluation(student_id: int) -> dict:
    """根据学生 id 返回一段评价（真实服务会自己读数据库）"""
    return {
        "evaluation": (
            f"学生 #{student_id} 这周练习量稳定，匀变速直线运动进步明显；"
            "牛顿第二定律连续两次在摩擦力方向上出错且情绪偏受挫，建议下次从一道基础题回暖后再推进。"
        ),
        "highlights": ["匀变速直线运动 ↑", "摩擦力方向需巩固", "受挫时放慢节奏"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8200)
    args = parser.parse_args()
    uvicorn.run(server.streamable_http_app(), host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
