# 外部接口一览（给对接同事）

本仓库是 **STEM 主系统**（FastAPI + React）。下列三个服务由**外部团队独立开发**，主系统按契约调用。  
**请按「契约文件」实现，不要只按本文摘要开发**——摘要仅作索引。

---

## 怎么找规范文件

| # | 外部服务 | 协议 | **契约文件（规范正文）** | 本仓库调用代码 | 本地假服务（联调） |
|---|----------|------|--------------------------|----------------|-------------------|
| 1 | 教学策略 | MCP Streamable HTTP | [`docs/design/mcp-strategy-contract.md`](./design/mcp-strategy-contract.md) | `backend/app/external/teaching_strategy.py` | `backend/scripts/fake_strategy_server.py` |
| 2 | 学习评价（评价处） | MCP Streamable HTTP | [`docs/design/mcp-evaluation-contract.md`](./design/mcp-evaluation-contract.md) | `backend/app/external/evaluation.py` | `backend/scripts/fake_evaluation_server.py` |
| 3 | 面部情绪识别 | HTTP multipart | [`docs/design/emotion-http-contract.md`](./design/emotion-http-contract.md) | `backend/app/external/emotion.py` | （无内置假服务，按契约自起即可） |

相关只读数据表结构：[`docs/database_schema.md`](./database_schema.md)  
**同机只读连库（不是 MCP）**：[`docs/design/db-external-access.md`](./design/db-external-access.md)  
产品背景：[`docs/PRD.md`](./PRD.md) §4

> 分清两件事：主系统 → 你们服务 = MCP；你们服务 → STEM 库 = Postgres 只读（`stem-net` + `strategy_reader`）。不要把数据库再包一层 MCP。

---

## 1. 教学策略服务

**发给策略同事：请打开 →** [`design/mcp-strategy-contract.md`](./design/mcp-strategy-contract.md)

| 项 | 内容 |
|----|------|
| 作用 | 每条学生消息给一句短策略，写入本轮 LLM system prompt |
| 工具名 | `get_teaching_strategy` |
| 入参 | `student_id`, `session_id`, `message` |
| 出参 | `{ "strategy": "…", "reason": "…" }`（`strategy` 必填） |
| 环境变量（主系统） | `TEACHING_STRATEGY_MCP_URL`、`TEACHING_STRATEGY_API_KEY`（可选）、超时默认 5s |
| 数据 | 服务可加入 `stem-net`，只读连库（角色 `strategy_reader`）自行查画像；主系统**只传三个入参** |
| 失败 | 主系统 LLM 兜底 → 再失败用硬编码策略；**不中断**教学 |

联调：

```bash
cd backend && .venv/bin/python -m scripts.fake_strategy_server   # :8100/mcp
# .env: TEACHING_STRATEGY_MCP_URL=http://127.0.0.1:8100/mcp
```

---

## 2. 评价处服务

**发给评价同事：请打开 →** [`design/mcp-evaluation-contract.md`](./design/mcp-evaluation-contract.md)

| 项 | 内容 |
|----|------|
| 作用 | 报告页「让评价处点评」：对学生近期学习写一段话 + 可选要点标签 |
| 工具名 | `get_student_evaluation` |
| 入参 | `student_id` |
| 出参 | `{ "evaluation": "…", "highlights": ["…"] }`（`evaluation` 必填） |
| 环境变量（主系统） | `EVALUATION_MCP_URL`、`EVALUATION_API_KEY`（可选）、超时默认 15s |
| 数据 | 同策略服务，只读连库；主系统**只传 student_id** |
| 失败 | API 返回 `source=unavailable`；报告其他部分仍可用 |

联调：

```bash
cd backend && .venv/bin/python -m scripts.fake_evaluation_server   # :8200/mcp
# .env: EVALUATION_MCP_URL=http://127.0.0.1:8200/mcp
```

---

## 3. 面部情绪识别服务

**发给情绪同事：请打开 →** [`design/emotion-http-contract.md`](./design/emotion-http-contract.md)

| 项 | 内容 |
|----|------|
| 作用 | 对摄像头 JPEG 截帧做五档情绪分类 |
| 接口 | `POST {EMOTION_BASE_URL}/recognize`，multipart 字段 `image`（+ 可选 `student_id`） |
| 出参 | `{ "emotion": "<五档之一>", "confidence": 0.0-1.0 }` |
| 五档枚举 | `confident` / `slightly_uncertain` / `discouraged` / `frustrated` / `very_frustrated` |
| 环境变量（主系统） | `EMOTION_BASE_URL`、`EMOTION_API_KEY`（可选）、超时默认 3s |
| 失败 | 本帧情绪为空；**不中断**教学 / 练习 |

说明：教学路径还有**文本情绪**（本仓库内 LLM），不是外部服务，无需你们实现。

---

## 不是「外部对接服务」的内容

| 能力 | 说明 |
|------|------|
| OpenAI 兼容 LLM | 主系统自己配置 `LLM_*`，调用 chat / vision / embed；不是同事要开发的服务 |
| 文本情绪分类 | 主系统内用 LLM 完成 |
| 本系统 REST API | 前后端之间接口，见 [`docs/api.md`](./api.md) |

---

## 对接约定（三条服务共通）

1. **契约优先**：字段名、枚举、工具名以契约文件为准；改契约需与主系统同步改客户端。
2. **软失败**：主系统按「失败可降级」设计；你们侧超时 / 5xx 不应依赖主系统重试。
3. **鉴权**：可选 Bearer；与主系统约定同一 key 即可。
4. **库访问**（策略 / 评价）：只读角色连 `stem-db`，见 [`design/db-external-access.md`](./design/db-external-access.md)；表含义以 [`database_schema.md`](./database_schema.md) 为准；不要写库。

---

## 建议发给同事的材料包

按角色复制下列路径即可：

```
策略同事
  docs/design/mcp-strategy-contract.md
  docs/design/db-external-access.md   # 同机只读连库
  docs/database_schema.md
  docs/external-interfaces.md         # 本索引 §1
  examples/external-service.compose.yml

评价同事
  docs/design/mcp-evaluation-contract.md
  docs/design/db-external-access.md
  docs/database_schema.md
  docs/external-interfaces.md         # 本索引 §2
  examples/external-service.compose.yml

情绪同事
  docs/design/emotion-http-contract.md
  docs/external-interfaces.md         # 本索引 §3（情绪服务不连库）
```
