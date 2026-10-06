# 教学策略 MCP 契约

教学后端在**每条学生消息**到达时调用一次外部策略服务，拿回一句简短策略，放进本轮 LLM 的 system prompt。
调用方是 `backend/app/external/teaching_strategy.py`。

## 传输

- 协议：MCP，Streamable HTTP
- 地址：由后端环境变量 `TEACHING_STRATEGY_MCP_URL` 指定，例如 `http://strategy:8100/mcp`
- 鉴权：可选。配置 `TEACHING_STRATEGY_API_KEY` 时，后端在每个 HTTP 请求带 `Authorization: Bearer <key>`
- 超时：后端整次调用（含 initialize 和 call_tool）5 秒，超时即走兜底，不重试

## 工具

名称：`get_teaching_strategy`

入参（JSON object）：

| 字段 | 类型 | 说明 |
|---|---|---|
| `student_id` | integer | 学生唯一 id，即数据库 `students.id`。策略服务用它自己去查学生档案 |
| `session_id` | integer | 教学会话 id，`teaching_sessions.id`。同一道题的多轮追问共用一个 session_id |
| `message` | string | 学生这一句话的原文。第一轮是题目文本，之后是追问 |

返回：优先读 `structuredContent`，没有则读第一个 text content 并按 JSON 解析，解析失败时把整段文本当作 strategy。

```json
{ "strategy": "先让学生自己找错，不直接给答案" }
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `strategy` | string，必填 | 十几个字的教学策略，原样进 prompt |
| `reason` | string，可选 | 给出该策略的原因，只用于审计记录 |

`isError: true` 或 `strategy` 为空都按失败处理。

## 失败时后端的行为

MCP 未配置、连接失败、超时、返回异常：后端用自己的 LLM 生成一条兜底策略，会话不中断，日志记 warning。

## 策略服务可读的数据

策略服务加入 docker 网络 `stem-net` 后可直连 `stem-db:5432`，使用只读角色 `strategy_reader`。相关表：

- `students`、`student_knowledge_summaries`：学生档案与知识点掌握度
- `student_kp_emotions`：学生对每个知识点的历史总体情绪（1 自信 … 5 非常受挫），每次会话结束后指数平滑更新
- `emotion_logs`：情绪图谱流水，教学模式每个 session 按知识点一行
- `teaching_sessions`、`teaching_messages`：会话与消息。user 消息上的 `facial_value`、`text_value`、`emotion_value` 是即时情绪

建表语句见 `docs/database_schema.md`。

## 本地联调

仓库自带一个假服务端：

```bash
cd backend
.venv/bin/python -m scripts.fake_strategy_server   # 监听 http://127.0.0.1:8100/mcp
```

后端 `.env` 里设 `TEACHING_STRATEGY_MCP_URL=http://127.0.0.1:8100/mcp` 即可。假服务按 message 关键字返回不同策略，便于看效果。
