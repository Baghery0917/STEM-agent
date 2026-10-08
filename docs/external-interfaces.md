# 外部接口一览（给对接同事）

本仓库是 **STEM 主系统**（FastAPI + React）。下列服务由**外部团队独立开发**，主系统按契约调用。  
**请按「契约文件」实现，不要只按本文摘要开发**——摘要仅作索引。

> **两件事别混：**  
> 1. 主系统 → 你们服务 = MCP / HTTP（§1–§3）  
> 2. 你们服务 → STEM 库 = Postgres 只读（§0，`stem-net` + `strategy_reader`）  
> **不要把数据库再包一层 MCP。**

产品背景：[`docs/PRD.md`](./PRD.md) §4

---

## 怎么找规范文件

| # | 能力 | 协议 | **契约 / 规范正文** | 说明 |
|---|------|------|---------------------|------|
| 0 | **STEM 只读数据库**（共享） | Postgres TCP | [`docs/design/db-external-access.md`](./design/db-external-access.md) | 策略 / 评价同机连库；表结构见 [`database_schema.md`](./database_schema.md) |
| 1 | 教学策略 | MCP Streamable HTTP | [`docs/design/mcp-strategy-contract.md`](./design/mcp-strategy-contract.md) | 调用代码 `backend/app/external/teaching_strategy.py`；假服务 `scripts/fake_strategy_server.py` |
| 2 | 学习评价（评价处） | MCP Streamable HTTP | [`docs/design/mcp-evaluation-contract.md`](./design/mcp-evaluation-contract.md) | 调用代码 `backend/app/external/evaluation.py`；假服务 `scripts/fake_evaluation_server.py` |
| 3 | 面部情绪识别 | HTTP multipart | [`docs/design/emotion-http-contract.md`](./design/emotion-http-contract.md) | 调用代码 `backend/app/external/emotion.py`；**不连库** |

---

## 0. STEM 只读数据库（共享基础设施）

**规范正文 →** [`design/db-external-access.md`](./design/db-external-access.md)  
**表结构 →** [`database_schema.md`](./database_schema.md)  
**Compose 示例 →** [`examples/external-service.compose.yml`](../examples/external-service.compose.yml)

策略服务、评价处跑在**同一台服务器**上时，加入 Docker 网络 `stem-net`，用只读角色直连本仓库的 `stem-db`，自行查学生画像 / 会话 / 练习等。主系统 MCP 调用**只传业务 id**，不代查库、不推全量数据。

| 项 | 内容 |
|----|------|
| 协议 | PostgreSQL（TCP `5432`），**不是** MCP |
| 容器名 / Host（已 join `stem-net`） | `stem-db` |
| Host（宿主机进程，不进 Docker） | `127.0.0.1` |
| Port | `5432` |
| Database | `stem_db` |
| User / Password | `strategy_reader` / `strategy_reader`（生产务必改密） |
| 权限 | 仅 `CONNECT` + `SELECT`；**禁止写库**；勿用超级用户 `postgres` |
| 网络 | Docker 外部网络 `stem-net`（本仓库 `make up` / `make db-up` 会自动创建） |
| 表含义 | [`database_schema.md`](./database_schema.md)；各服务推荐读哪些表见对应 MCP 契约 |

连接串（复制即用）：

```text
# 外部服务容器内（推荐）
postgresql://strategy_reader:strategy_reader@stem-db:5432/stem_db

# 宿主机上跑的进程
postgresql://strategy_reader:strategy_reader@127.0.0.1:5432/stem_db
```

你们侧 compose 要点：

```yaml
services:
  your-service:
    environment:
      DATABASE_URL: postgresql://strategy_reader:strategy_reader@stem-db:5432/stem_db
    networks:
      - stem-net

networks:
  stem-net:
    external: true
```

部署侧（本仓库维护者）一次性命令：

```bash
make up                 # 或 make db-up；会 ensure stem-net
make db-grant-reader    # 旧数据卷缺只读角色 / 新表无 SELECT 时补一次
```

验证：

```bash
docker exec -it stem-db psql -U strategy_reader -d stem_db -c '\dt'
```

谁需要连库：

| 外部服务 | 是否连库 |
|----------|----------|
| 教学策略 | 是，自行查画像 / 情绪 / 会话 |
| 评价处 | 是，自行查练习 / 掌握度 / 会话 |
| 面部情绪 | **否**，只收图片做识别 |

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
| 数据 | 按 **§0** 只读连库自行查画像；主系统**只传三个入参** |
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
| 数据 | 按 **§0** 只读连库；主系统**只传 student_id** |
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
| 数据 | **不连 STEM 库**；只处理上传图片 |
| 失败 | 本帧情绪为空；**不中断**教学 / 练习 |

说明：教学路径还有**文本情绪**（本仓库内 LLM），不是外部服务，无需你们实现。

---

## 不是「外部对接服务」的内容

| 能力 | 说明 |
|------|------|
| OpenAI 兼容 LLM | 主系统自己配置 `LLM_*`，调用 chat / vision / embed；不是同事要开发的服务 |
| 文本情绪分类 | 主系统内用 LLM 完成 |
| 本系统 REST API | 前后端之间接口，见 [`docs/api.md`](./api.md) |
| STEM 写库 / 迁移 | 仅主系统后端；外部只用 `strategy_reader` 只读 |

---

## 对接约定（共通）

1. **契约优先**：字段名、枚举、工具名以契约文件为准；改契约需与主系统同步改客户端。
2. **软失败**：主系统按「失败可降级」设计；你们侧超时 / 5xx 不应依赖主系统重试。
3. **鉴权**：MCP / HTTP 可选 Bearer；与主系统约定同一 key 即可。
4. **库访问**（策略 / 评价）：按 **§0** 与 [`design/db-external-access.md`](./design/db-external-access.md)；表含义以 [`database_schema.md`](./database_schema.md) 为准；**只读、不写库**。

---

## 建议发给同事的材料包

按角色复制下列路径即可：

```
策略同事
  docs/external-interfaces.md         # 总览：§0 连库 + §1 策略
  docs/design/mcp-strategy-contract.md
  docs/design/db-external-access.md
  docs/database_schema.md
  examples/external-service.compose.yml

评价同事
  docs/external-interfaces.md         # 总览：§0 连库 + §2 评价
  docs/design/mcp-evaluation-contract.md
  docs/design/db-external-access.md
  docs/database_schema.md
  examples/external-service.compose.yml

情绪同事
  docs/external-interfaces.md         # 总览 §3（不连库）
  docs/design/emotion-http-contract.md
```
