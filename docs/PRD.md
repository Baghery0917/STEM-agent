# STEM 智能教学系统 — 产品需求文档（PRD）

> 本文档按当前代码实现重写，描述系统「现在是什么」。  
> - 本系统 REST API：[`api.md`](./api.md)  
> - 表结构：[`database_schema.md`](./database_schema.md)  
> - **外部对接总览（发给同事用）**：[`external-interfaces.md`](./external-interfaces.md)

---

# 1. 项目概述

STEM 智能教学系统是一个面向学生的物理（STEM）智能辅导产品。学生提交题目后，系统结合知识点分析、学习画像、教学策略与相似题检索，由 LLM 完成个性化讲解；同时提供按知识点抽题练习、情绪感知、学习报告与讲师人格（认可卡）解锁。

## 1.1 当前角色与范围

| 角色 | 入口 | 能力 |
|------|------|------|
| **学生** | 姓名登录（无密码；同名复用，新名自动建档） | 教学对话、练习、学习报告、认可卡、设置（讲解风格 / 讲师 / 摄像头） |
| **管理员** | 登录页「教师」页签 → 共享口令 `ADMIN_PASSWORD` | 知识树、题库、学生 CRUD、数据库只读浏览 |

无独立「教师」业务角色（无班级、布置作业、批改等）。学生侧 API 以 `student_id` 标识身份，不做登录鉴权；管理台 DB 接口需 `X-Admin-Token`。

## 1.2 产品形态

- 交互主模式：**教学模式**、**练习模式**（可互相跳转：练习错题 / 星标题 → 教学）
- 前端主题：TBBT（The Big Bang Theory）风格壳层 + 七位讲师人格
- 部署：Docker Compose 全栈，或本地前后端分启 + PostgreSQL/pgvector

---

# 2. 系统架构

```
┌──────────────────────────────────────────────────────────────────────────┐
│  前端（React 18 + TypeScript + Vite）                                      │
│  学生端：教学 / 练习 / 报告 / 认可卡 / 设置（自定义 CSS + Zustand）          │
│  管理端：知识树 / 题库 / 学生 / DB 浏览（Ant Design）                        │
│  摄像头：可选，发送时截帧 frame_base64 供面部情绪识别                        │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │ HTTP / SSE
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  API 层（FastAPI /api/v1）                                                 │
│  knowledge · questions · students · teaching · practice · admin · health │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  服务层                                                                    │
│  TeachingService（流水线 + 多轮对话）  PracticeService（抽题 / 批改 / 星标） │
│  EmotionService · ReportService · RecognitionService · QuestionService   │
│  SessionSearchService · Volume/Chapter/Section CRUD                      │
└───┬─────────────────────────────┬────────────────────────────┬───────────┘
    │                             │                            │
    ▼                             ▼                            ▼
┌───────────────┐    ┌────────────────────────┐    ┌─────────────────────┐
│ 外部集成       │    │ LLM（OpenAI 兼容）       │    │ PostgreSQL 16        │
│ 面部情绪 HTTP  │    │ chat / stream / vision │    │ + pgvector           │
│ 教学策略 MCP   │    │ embed · 人格 prompt     │    │ 业务表 + 向量列       │
│ 评价处 MCP     │    │ 调用审计 llm_call_logs  │    │                      │
└───────────────┘    └────────────────────────┘    └─────────────────────┘
```

---

# 3. 功能需求

## 3.1 知识结构管理

### 3.1.1 层级

```
册（Volume）
└── 章（Chapter）
    └── 节（Section）   ← 系统中的「知识点」
```

- **节 = 知识点**：题目多对多挂到 `sections`；掌握度、情绪均以 `section_id` 为粒度。
- 无独立「知识点表」或六位 `kp_id` 编码；主键为自增整数。

### 3.1.2 能力

| 功能 | 说明 |
|------|------|
| CRUD | 管理端对册 / 章 / 节增删改查，支持 `order`、描述 / 内容 |
| 树形管理 | 管理端可视化树；学生端用于练习选范围、报告路径展示 |
| 批量导入 | 前端按 JSON 顺序调创建接口（当前无专用 bulk API） |

### 3.1.3 导入 JSON 示例

```json
{
  "volumes": [
    {
      "title": "力学",
      "chapters": [
        {
          "title": "运动学",
          "sections": [
            { "title": "匀变速直线运动", "content": "..." }
          ]
        }
      ]
    }
  ]
}
```

### 3.1.4 核心字段

| 实体 | 主要字段 |
|------|----------|
| Volume | `title`, `description`, `order` |
| Chapter | `volume_id`, `title`, `description`, `order` |
| Section | `chapter_id`, `title`, `content`, `order` |

---

## 3.2 题库管理

### 3.2.1 题目类型与难度

| 枚举 | 取值 |
|------|------|
| `type` | `single_choice` / `multiple_choice` / `fill_blank` / `short_answer` / `calculation` |
| `difficulty` | `easy` / `medium` / `hard` |

### 3.2.2 题目模型（概要）

| 字段 | 说明 |
|------|------|
| `content` / `content_image` | 题干文本；可选图片 URL |
| `answer` / `answer_image` | 标准答案 |
| `analysis` / `analysis_image` | 解析（可选） |
| `embedding` | 题干向量（pgvector，默认 1024 维）；写入 / 更新题干时生成，生成前剥离 LaTeX |
| `knowledge_points` | 多对多 → `sections` |

### 3.2.3 管理能力

- 管理端：筛选（类型 / 难度）、创建 / 编辑 / 删除
- 创建与更新时自动算 embedding
- 练习抽题按知识点 + 难度（+ 可选题型）过滤后随机抽取；**向量检索不用于练习出题**
- 向量检索用于教学模式的相似参考题（见 3.6）

---

## 3.3 学生档案

### 3.3.1 学生基础信息

| 字段 | 说明 |
|------|------|
| `name` | 姓名（登录标识） |
| `gender` | `male` / `female` / `other` |
| `explain_style` | 可选讲解风格覆盖：`direct` / `guided` / `hint`；空则完全由策略模块决定 |
| `persona` | 讲师人格；空等价 `leonard`；未解锁人格不可设置（403） |

### 3.3.2 知识点掌握度（`student_knowledge_summaries`）

按 `(student_id, section_id)` 唯一：

| 字段 | 说明 |
|------|------|
| `mastery_level` | 掌握度浮点，教学结束时按自评或显式 delta 调整 |
| `correct_count` / `total_practice_count` | 练习正确数 / 总练习题数（跳过不计） |
| `total_teaching_count` | 教学会话次数 |
| `last_practice_at` / `last_teaching_at` | 最近练习 / 教学时间 |

### 3.3.3 情绪相关

| 表 | 说明 |
|----|------|
| `student_kp_emotions` | 学生对某节的历史总体情绪（EMA 平滑） |
| `emotion_logs` | 流水：`mode` = `teaching` \| `practice`，含时段与 `emotion_value` |

情绪量表：**1 = 自信 … 5 = 非常受挫**。

---

## 3.4 教学交互模块

核心：学生对一道题开启一次会话，支持多轮追问；会话可由学生结束、取消，或空闲超时自动结束。

### 3.4.1 会话与消息

**会话（`teaching_sessions`）**

| 字段 | 说明 |
|------|------|
| `status` | `active` / `completed` / `cancelled` |
| `pipeline_status` | `pending` / `running` / `done` / `failed` |
| `strategy` | 最近一次策略文本 |
| `persona` | 创建时讲师快照（之后改设置不影响本会话） |
| `end_reason` | `user` / `idle` |
| `source_practice_session_id` / `source_question_ids` | 练习转教学时的来源 |

**消息类型（`message_type`）**

| 类型 | 角色 | 含义 |
|------|------|------|
| `question_submit` | user | 首轮提交的题目（可含图片 / 练习手递内容） |
| `llm_analysis` | system | LLM 映射到的知识点 |
| `student_data` | system | 相关节的掌握度与情绪历史 |
| `strategy` | system | 本轮教学策略 |
| `reference_search` | system | 相似参考题检索结果 |
| `chat` | user / assistant | 对话正文 |

首轮流水线典型序号：`0 question_submit → 1 llm_analysis → 2 student_data → 3 strategy → 4 reference_search → 5 chat(assistant)`。后续轮次：`user chat → system strategy → assistant chat`。

用户消息可存即时情绪 `facial_value` / `text_value` / `emotion_value`；助手消息可存 `self_rating`（0–3）。

### 3.4.2 首轮流水线（后台异步）

`POST /teaching/sessions` 立即返回会话壳，后台 `run_pipeline`：

```
学生提交题目（文本 ± 图片 ± frame_base64 ± 练习来源）
     │
     ▼
[1] 知识点分析（LLM）→ 关联 sections
     │
     ▼
[2] 学生数据检索 → 相关节掌握度 + KP 情绪历史
     │
     ▼
[3] 并行：即时情绪识别 + 教学策略 MCP
     │
     ▼
[4] 相似题检索（embedding，top-1，相似度 ≥ 阈值才采用）
     │
     ▼
[5] 组装 Prompt（策略 + 画像 + 参考题 + 人格语气 + 讲解风格）
     │
     ▼
[6] LLM 首轮讲解 → pipeline_status = done | failed
```

前端对 `pipeline_status` 轮询，并以可折叠「思考块」展示各阶段。

### 3.4.3 多轮追问

- `POST /teaching/sessions/chat/stream`：SSE 流式（学生端实际使用）
- 每轮重新拉取策略与即时情绪；策略写入 system 消息
- 人格只改语气；学生 `explain_style` 可覆盖辅导风格
- 当即时情绪 ≥ 3 时，前端可展示安抚动效（Soft Kitty），Prompt 侧放缓节奏（不向学生明示「在观察情绪」）

### 3.4.4 掌握度自评

助手消息可打分（0–3）：

| 分值 | 含义 | 默认 mastery delta |
|------|------|--------------------|
| 0 | 还没懂 | −0.1 |
| 1 | 看懂了讲解 | +0.05 |
| 2 | 能自己做 | +0.15 |
| 3 | 能讲给别人 | +0.25 |

结束会话时可用最后一次自评推算掌握度变化，也可由 API 显式传 `mastery_level_delta`（前端当前未传显式值）。

### 3.4.5 会话结束与空闲

| 动作 | 行为 |
|------|------|
| 正常结束 | 更新掌握度、情绪回流（EMA）、认可分、写 emotion_log |
| 取消 | 不回流掌握度 / 情绪档案 |
| 空闲超时 | 默认 30 分钟无活动自动结束（`end_reason=idle`），后台定时扫描 |

### 3.4.6 练习 → 教学手递

练习结束或单题操作可将错题 / 星标题带入教学：首条消息打包题干 + 学生作答 + 标准答案，并记录 `source_practice_session_id` / `source_question_ids`，前端展示「来自练习」卡片。

---

## 3.5 练习模块

**不再区分 Focused / General。** 统一流程：选定知识点与难度（可选题型、题量）→ 一次抽满题目 → 题间可前后切换。

### 3.5.1 会话参数

| 参数 | 说明 |
|------|------|
| `knowledge_point_ids` | 节 ID 列表（多选） |
| `difficulty_range` | `easy` / `medium` / `hard` 多选 |
| `question_types` | 可选题型过滤 |
| `total_count` | 题量 1–100，默认 10 |
| `timed` | 计时：强制统一批改；过程中不可中途转教学，只能先星标 |
| `instant_feedback` | 是否每题即时对错反馈；`timed=true` 时强制为 false |

开始前可 `POST /practice/match` 预览匹配题量。

### 3.5.2 主流程

```
选择范围 / 难度 / 题量 / 计时与反馈
        │
        ▼
   按条件随机抽满 question_ids（不足则全取）
        │
        ▼
   前端展示题目（不含答案）；学生作答 / 跳过 / 星标
        │
        ├── submit：判分；可选 frame → 面部情绪写在 item 上
        ├── skip：记一行 is_skipped，不入掌握度档案
        └── star：写入 starred_question_ids，结束后可转教学
        │
        ▼
   end：未作答自动 skip；聚合计数；情绪回流；认可分
        │
        ▼
   总结页：错题 + 星标题 → 一键 / 批量转教学
```

### 3.5.3 记录模型

**`practice_sessions`**：`timed`、`instant_feedback`、范围、`question_ids`、`starred_question_ids`、计数聚合。

**`practice_items`**：每题一行（含跳过）；`is_correct` / `is_skipped`、`user_answer`、`duration_seconds`、`emotion` / `emotion_value`。

约束：跳过不计入学生知识点档案；结束时剩余未答视为跳过。

---

## 3.6 向量检索

- 存储：`questions.embedding`（pgvector），维度与配置 `pgvector_dimension` / embedding 模型一致（默认 1024）
- 用途：**教学模式参考题** — `search_by_text`，取 top-1，相似度低于阈值（默认 0.8）则不用
- 练习出题：SQL 条件过滤 + 随机，不用向量
- 侧栏会话搜索：教学消息与练习节标题的 **ILIKE 文本检索**，非向量

---

## 3.7 情绪模块

### 3.7.1 即时识别

| 来源 | 时机 | 方式 |
|------|------|------|
| 面部 | 教学发送 / 练习提交（带 `frame_base64`） | HTTP `POST {emotion_base_url}/recognize` multipart |
| 文本 | 仅教学 | LLM 对用户文本分类 |

混合（教学）：默认 `0.6 × facial + 0.4 × text`（`emotion_facial_weight`）。失败记空 / 不影响主流程。

五档标签映射到数值 1–5（自信 → 非常受挫）。

### 3.7.2 回流档案

会话结束时，用本会话即时情绪均值对涉及知识点做指数平滑：

`新 = 旧 × (1 − α) + 会话均值 × α`（默认 α = 0.3）

并写入 `emotion_logs`（教学：按知识点；练习：按会话题目涉及知识点聚合）。

---

## 3.8 认可卡（Recognition）

隐藏积分体系，用于线性解锁七位讲师人格。**规则不下发前端**；分数只增不减；按来源幂等记账（`score_events`）。

| 人格 | 解锁条件（概要） |
|------|------------------|
| Leonard | 注册即有 |
| Penny → … → Sheldon | 累计积分达到阈值（150 / 400 / 800 / 1500 / 2600 / 4500） |

积分来源示例：练习作答（含正确翻倍、每日递减、计时加成）、教学正常结束与自评、掌握度正增量、星标后去提问、自评「能自己做」后在窗口期内练习正确率达标、连续学习天数加成。

学生可在「认可卡」页查看已获得卡片，并在设置中将已解锁人格设为当前讲师。

---

## 3.9 学生报告

`GET /students/{id}/report?mode=recent|all`

| 模式 | 行为 |
|------|------|
| `recent` | 近 7 天活跃：练习 / 教学次数、相关掌握度、情绪日序列与明细 |
| `all` | 全量已学知识点掌握度 + 历史情绪趋势 |

可选 LLM 生成一段话 `summary`。另：`GET /students/{id}/evaluation` 调外部「评价处」MCP，失败时 `source=unavailable`，不影响报告其余部分。前端「导出 PDF」为浏览器打印。

---

## 3.10 会话搜索

`GET /students/{id}/sessions/search?q=`：教学按消息内容、练习按知识点标题全文检索，供侧栏搜索。

---

## 3.11 管理端

| 页面 | 能力 |
|------|------|
| 知识结构 | 树 CRUD + JSON 批量导入（前端顺序创建） |
| 题库 | 列表筛选、表单编辑（图片为 URL 字段） |
| 学生 | 姓名 / 性别 CRUD |
| 数据库 | 只读浏览全部表（需 Admin Token） |

Admin 登录：`POST /admin/login` → token = `sha256("stem-admin:" + password)`；`ADMIN_PASSWORD` 为空则禁止登录。

---

# 4. 外部模块集成

> **对接同事请直接看总览文档** → [`docs/external-interfaces.md`](./external-interfaces.md)  
> 下表是索引；**请求/响应字段以契约文件为准**。

## 4.0 外部服务与契约文件对照

| 外部服务 | 协议 | 契约文件（规范正文） | 调用代码 | 假服务 / 联调 |
|----------|------|----------------------|----------|---------------|
| **教学策略** | MCP Streamable HTTP | [`design/mcp-strategy-contract.md`](./design/mcp-strategy-contract.md) | `backend/app/external/teaching_strategy.py` | `scripts/fake_strategy_server.py` |
| **评价处** | MCP Streamable HTTP | [`design/mcp-evaluation-contract.md`](./design/mcp-evaluation-contract.md) | `backend/app/external/evaluation.py` | `scripts/fake_evaluation_server.py` |
| **面部情绪** | HTTP multipart | [`design/emotion-http-contract.md`](./design/emotion-http-contract.md) | `backend/app/external/emotion.py` | 按契约自起服务 |

只读库表参考：[`database_schema.md`](./database_schema.md)。  
以下能力**不由外部同事实现**：OpenAI 兼容 LLM、教学路径内的**文本情绪**（本仓库 LLM）、本系统前后端 REST（见 [`api.md`](./api.md)）。

## 4.1 教学策略（MCP）

| 项目 | 说明 |
|------|------|
| 契约 | **[`design/mcp-strategy-contract.md`](./design/mcp-strategy-contract.md)** |
| 协议 | MCP Streamable HTTP（`TEACHING_STRATEGY_MCP_URL`） |
| 工具 | `get_teaching_strategy(student_id, session_id, message)` |
| 调用时机 | **每条学生消息**（含首轮与追问） |
| 返回 | `{ strategy, reason? }` 短句策略进 Prompt |
| 失败兜底 | 本地 LLM 生成 → 再失败则硬编码默认策略；不中断会话 |

策略服务可只读连库自行查画像；主系统只传三个入参。

## 4.2 面部情绪识别（HTTP）

| 项目 | 说明 |
|------|------|
| 契约 | **[`design/emotion-http-contract.md`](./design/emotion-http-contract.md)** |
| 协议 | `POST {EMOTION_BASE_URL}/recognize`，multipart `image`（JPEG） |
| 返回 | `{ emotion, confidence? }`，`emotion` 为五档英文枚举 |
| 时机 | 教学发消息 / 练习提交答案（有 `frame_base64` 时） |
| 失败 | 本帧情绪为空，主流程继续 |

## 4.3 文本情绪（LLM，非外部服务）

仅教学模式；本仓库内 LLM 对用户文本分类到同一 1–5 量表；与面部按权重混合（默认 0.6 facial + 0.4 text）。**无需外部团队开发。**

## 4.4 评价处（MCP）

| 项目 | 说明 |
|------|------|
| 契约 | **[`design/mcp-evaluation-contract.md`](./design/mcp-evaluation-contract.md)** |
| 工具 | `get_student_evaluation(student_id)` |
| 返回 | `{ evaluation, highlights? }` |
| 失败 | `source=unavailable`，报告页其余数据正常 |

---


# 5. 前端信息架构

| 路由 | 说明 |
|------|------|
| `/login` | 学生姓名登录 / 管理员口令 |
| `/teaching` · `/teaching/:sessionId` | 新会话与进行中教学（流式、自评、结束） |
| `/practice/new` · `/practice/:sessionId` | 练习设置与作答、总结、转教学 |
| `/report` | 近一周 / 全景报告 + 评价处 |
| `/cards` | 认可卡图鉴 |
| `/settings` | 切换学生、讲解风格、讲师、摄像头 |
| `/admin/knowledge` · `questions` · `students` · `db` | 管理台 |

状态：`studentStore`（当前学生）、`uiStore`（教学/练习模式、摄像头开关）、Admin Token 存 `sessionStorage`。

---

# 6. 技术选型

| 层次 | 技术 |
|------|------|
| 前端 | React 18 + TypeScript + Vite + Ant Design（管理端）+ Zustand + TanStack Query |
| 后端 | Python 3.12 + FastAPI + SQLAlchemy 2.0（async）+ Pydantic v2 |
| 数据库 | PostgreSQL 16 + pgvector |
| 迁移 | Alembic |
| LLM | OpenAI 兼容 API（chat / vision / embedding），调用写入 `llm_call_logs` |
| 容器 | Docker + Docker Compose；根目录 Makefile 统一命令 |

---

# 7. 非功能需求

| 类别 | 要求 |
|------|------|
| 可扩展性 | 知识树层级、题型、人格、外部 MCP 可独立演进 |
| 可追溯性 | LLM 请求/响应与参数完整落库；教学流水线各步以 system 消息留存 |
| 容错性 | 策略 / 情绪 / 评价处失败不阻断主路径 |
| 数据一致性 | 会话结束时的掌握度、情绪、认可分在服务层事务内更新 |
| 安全（当前） | 学生无鉴权（开发友好）；生产需强设 `ADMIN_PASSWORD` 与 `LLM_API_KEY`；敏感帧仅作识别、不作为视频流持久化（业务约定） |
| 空闲治理 | 教学会话空闲超时自动结束，避免悬挂会话占资源 |

---

# 8. 与历史设计的主要差异（备忘）

| 旧 PRD | 当前实现 |
|--------|----------|
| Focused / General 练习模式 | 已取消；改为 `timed` + `instant_feedback` |
| 独立 kp_id（六位编码） | 以 `sections.id` 为知识点 |
| 题目以图片为主、LLM 导入匹配知识点 | 文本为主 + 可选图片 URL；管理端手工挂知识点 |
| 教学策略纯 HTTP | MCP Streamable HTTP + LLM/硬编码兜底 |
| 练习由「记忆模块」独立出题服务 | 本仓库 `PracticeService` 直接抽题与记账 |
| 前端「待定」 | React + Vite，学生端 TBBT 主题，管理端 Ant Design |
| — | 新增：自评、练习手递教学、认可卡 / 人格、流式对话、评价处 MCP、Admin DB、LLM 审计 |

---

# 9. 已知缺口（实现现状，非承诺排期）

- 知识 / 题库无服务端 bulk 导入 API（知识导入靠前端顺序 POST；题库 bulk 助手未挂 UI）
- 学生无真正身份认证；管理端除 DB 外多数管理 API 未强制带 Admin Token
- 报告「导出 PDF」仅为打印；题目图片为 URL 非本地上传
- 追问轮次前端关闭图片上传（仅首轮可带图）
