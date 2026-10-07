# 评价处 MCP 契约

学习报告页的「让评价处点评」按钮会让后端调一次外部评价服务，拿回一段对该学生近期学习的评价展示给学生。
后端只传 `student_id`，评价服务自己连数据库读学生数据。调用方是 `backend/app/external/evaluation.py`。

## 传输

- 协议：MCP，Streamable HTTP
- 地址：由后端环境变量 `EVALUATION_MCP_URL` 指定，例如 `http://evaluation:8200/mcp`
- 鉴权：可选。配置 `EVALUATION_API_KEY` 时，后端在每个 HTTP 请求带 `Authorization: Bearer <key>`
- 超时：后端整次调用（含 initialize 和 call_tool）15 秒，超时即返回「评价处暂不可用」，不重试

## 工具

名称：`get_student_evaluation`

入参（JSON object）：

| 字段 | 类型 | 说明 |
|---|---|---|
| `student_id` | integer | 学生唯一 id，即数据库 `students.id` |

返回：优先读 `structuredContent`，没有则读第一个 text content 并按 JSON 解析，解析失败时把整段文本当作 evaluation。

```json
{
  "evaluation": "这周练习量稳定，匀变速直线运动进步明显；牛顿第二定律连续两次在摩擦力方向上出错……",
  "highlights": ["匀变速直线运动 ↑", "摩擦力方向需巩固"]
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `evaluation` | string，必填 | 面向学生的一段话评价，原样展示 |
| `highlights` | string[]，可选 | 两到四个要点，展示为标签 |

`isError: true` 或 `evaluation` 为空都按失败处理。

## 失败时后端的行为

MCP 未配置、连接失败、超时、返回异常：`GET /students/{id}/evaluation` 返回 `source = "unavailable"` 和 `detail`，前端显示「评价处暂不可用」，不影响报告其他部分。

## 评价服务可读的数据

与教学策略服务相同，加入 docker 网络 `stem-net` 后直连 `stem-db:5432`，只读角色 `strategy_reader`（接入步骤见 [`db-external-access.md`](./db-external-access.md)）。推荐读取：

- `student_knowledge_summaries`：知识点掌握度、练习 / 教学次数
- `practice_sessions`、`practice_items`：练习记录（`is_skipped` 的题不计入档案；`duration_seconds` 为用时）
- `teaching_sessions`、`teaching_messages`：会话；assistant 消息上的 `self_rating` 是学生自评（0 还没懂 … 3 能讲给别人）
- `student_kp_emotions`、`emotion_logs`：历史情绪与流水（`mode` 区分 teaching / practice）

建表语句见 `docs/database_schema.md`。

## 本地联调

```bash
cd backend
.venv/bin/python -m scripts.fake_evaluation_server   # 监听 http://127.0.0.1:8200/mcp
```

后端 `.env` 里设 `EVALUATION_MCP_URL=http://127.0.0.1:8200/mcp` 即可。
