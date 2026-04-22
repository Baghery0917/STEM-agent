# STEM 智能教学系统

基于 FastAPI + React 的 STEM 智能教学与练习系统，支持 AI 辅助讲解、智能刷题、知识点追踪等功能。

## 功能特性

- **知识体系管理**：册 → 章 → 节 三级结构，管理课程知识点
- **题库管理**：支持单选/多选/填空/解答题，含答案、解析、难度、知识点标签
- **学生管理**：学生档案与性别信息
- **智能练习**：支持「专项练习」（按知识点）和「综合练习」（随机抽题）两种模式
- **AI 教学**：提交题目后，系统自动分析知识点并启动 AI 讲解对话，支持流式输出
- **LLM 调用审计**：自动记录所有 LLM API 调用，便于成本分析与问题排查
- **数据库管理面板**：内置 admin 接口，可直接查看数据库表内容

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + TypeScript + Vite + Ant Design + Zustand |
| 后端 | Python 3.12 + FastAPI + SQLAlchemy 2.0 (async) |
| 数据库 | PostgreSQL 16 + pgvector 扩展 |
| 迁移 | Alembic |
| 容器 | Docker + Docker Compose |

## 环境要求

- Docker & Docker Compose（推荐，一键启动）
- 或手动安装：
  - Node.js 20+
  - Python 3.12+
  - PostgreSQL 16+（需启用 pgvector 扩展）

---

## 快速开始（Docker 一键启动）

最简单的方式，适合首次体验或部署：

```bash
# 1. 克隆项目后进入根目录
cd stem

# 2. 配置 LLM（可选，不配置则 AI 教学功能不可用）
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入你的 LLM 配置

# 3. 一键启动所有服务
make up
```

启动完成后访问：

| 服务 | 地址 |
|------|------|
| 前端页面 | http://localhost |
| 后端 API | http://localhost:8000 |
| API 文档（Swagger） | http://localhost:8000/docs |
| API 文档（ReDoc） | http://localhost:8000/redoc |

停止服务：

```bash
make down
```

删除数据（包括数据库）：

```bash
make db-reset
```

---

## 本地开发（前后端分别启动）

适合日常开发，支持热重载。

### 1. 启动数据库

```bash
make db-up
```

### 2. 后端开发

```bash
# 安装依赖
make backend-install

# 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env，至少确认数据库连接信息正确

# 运行数据库迁移
make migrate

# 启动开发服务器（热重载）
make backend-run
```

后端将在 http://localhost:8000 运行。

### 3. 前端开发

```bash
# 安装依赖
make frontend-install

# 启动开发服务器（热重载）
make frontend-dev
```

前端将在 http://localhost:5173 运行，Vite 会自动将 `/api` 代理到 http://localhost:8000。

---

## 数据库初始化

迁移完成后，数据库是空的。你可以通过以下方式填充测试数据：

### 方式一：种子脚本（推荐）

```bash
make db-seed
```

该脚本会自动创建：
- 4 个示例学生
- 完整的知识体系（力学基础 → 运动的描述 → 多个知识点）
- 多套练习题（含单选、多选、填空、解答题）
- 题目与知识点的关联

### 方式二：通过前端管理界面

启动前后端后，访问 http://localhost，在管理端页面手动录入数据。

---

## 配置 LLM（可选）

AI 教学功能需要配置 LLM 服务。支持所有 OpenAI 兼容接口（如 DashScope、OpenAI、DeepSeek 等）。

编辑 `backend/.env`：

```bash
# 以阿里云 DashScope 为例
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_API_KEY=sk-xxxxxxxxxxxxxxxx
LLM_MODEL=qwen3.6-flash
LLM_VISION_MODEL=qwen3.6-flash
LLM_EMBEDDING_MODEL=text-embedding-v4
LLM_EMBEDDING_DIMENSION=1024
```

教学策略服务（可选）：

```bash
TEACHING_STRATEGY_BASE_URL=https://your-strategy-service.com
TEACHING_STRATEGY_API_KEY=sk-xxxxxxxx
```

如未配置教学策略服务，系统会自动使用 LLM 作为 fallback。

---

## 项目结构

```
stem/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── main.py             # 应用入口
│   │   ├── config.py           # 配置管理
│   │   ├── database.py         # 数据库连接
│   │   ├── dependencies.py     # 依赖注入
│   │   ├── api/v1/routers/     # API 路由
│   │   │   ├── health.py       # 健康检查
│   │   │   ├── knowledge_structure.py  # 册/章/节 CRUD
│   │   │   ├── questions.py    # 题库管理
│   │   │   ├── student.py      # 学生管理
│   │   │   ├── teaching.py     # AI 教学会话
│   │   │   ├── practice.py     # 练习系统
│   │   │   └── admin_db.py     # 数据库管理面板
│   │   ├── models/             # SQLAlchemy 模型
│   │   ├── schemas/            # Pydantic 数据校验
│   │   ├── services/           # 业务逻辑层
│   │   ├── llm/                # LLM 客户端 + 审计
│   │   └── external/           # 外部服务调用
│   ├── tests/                  # 测试文件
│   ├── alembic/                # 数据库迁移
│   ├── seed_data.py            # 种子数据脚本
│   ├── pyproject.toml          # 后端依赖配置
│   └── Dockerfile
│
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── api/                # 后端接口封装
│   │   ├── pages/
│   │   │   ├── admin/          # 管理端页面
│   │   │   │   ├── KnowledgePage.tsx
│   │   │   │   ├── QuestionsPage.tsx
│   │   │   │   ├── StudentsPage.tsx
│   │   │   │   └── DatabasePage.tsx
│   │   │   └── student/        # 学生端页面
│   │   │       ├── Home.tsx
│   │   │       ├── PracticeSetup.tsx
│   │   │       ├── PracticeRunner.tsx
│   │   │       ├── PracticeHistory.tsx
│   │   │       ├── Teaching.tsx
│   │   │       └── Report.tsx
│   │   ├── components/         # 可复用组件
│   │   ├── layouts/            # 布局组件
│   │   ├── stores/             # Zustand 状态管理
│   │   └── hooks/              # 共享 Hook
│   ├── Dockerfile
│   └── nginx.conf
│
├── Makefile                    # 常用命令
├── docker-compose.yml          # 一键编排
└── README.md                   # 本文件
```

---

## API 概览

| 模块 | 前缀 | 说明 |
|------|------|------|
| Health | `/api/v1/health` | 服务健康检查 |
| 知识体系 | `/api/v1/volumes` `/chapters` `/sections` | 册/章/节 CRUD |
| 题库 | `/api/v1/questions` | 题目增删改查 |
| 学生 | `/api/v1/students` | 学生管理 |
| 教学 | `/api/v1/teaching/sessions` | AI 教学会话（创建、聊天、流式输出、结束）|
| 练习 | `/api/v1/practice/...` | 练习会话管理 |
| 数据库面板 | `/api/v1/admin/db/tables` | 查看表结构和数据 |

完整的 API 文档在启动后访问 http://localhost:8000/docs 查看。

---

## 测试

```bash
# 运行后端测试
make backend-test

# 或进入 backend 目录直接运行
cd backend && pytest -v
```

---

## Makefile 常用命令

根目录下统一管理：

```bash
# Docker 全栈
make up              # 启动所有服务（db + backend + frontend）
make down            # 停止所有服务
make build           # 重建所有镜像

# 后端
make backend-install # 安装后端依赖
make backend-run     # 启动后端开发服务器
make backend-test    # 运行后端测试
make backend-lint    # 后端代码检查

# 前端
make frontend-install # 安装前端依赖
make frontend-dev    # 启动前端开发服务器
make frontend-build  # 构建前端

# 数据库
make db-up           # 启动数据库容器
make db-down         # 停止数据库容器
make db-reset        # 重置数据库（删除数据卷并重建）
make migrate         # 运行数据库迁移
make migrate-create msg="描述"   # 创建新迁移
make db-seed         # 运行种子数据脚本

# 清理
make clean           # 清理所有缓存文件（含 node_modules）
```

---

## 常见问题

**Q: 数据库连接失败？**

确认 PostgreSQL 已启动且 `backend/.env` 中的 `DATABASE_URL` 正确。Docker 方式启动时，后端容器会自动等待数据库健康检查通过。

**Q: 迁移报错 "duplicate type"？**

PostgreSQL ENUM 类型在删表后不会自动删除。测试环境已通过 `conftest.py` 自动清理，生产环境如遇到可手动执行：

```sql
DROP TYPE IF EXISTS teachingsessionstatus CASCADE;
```

**Q: AI 教学没有响应？**

检查 `backend/.env` 中的 LLM 配置是否正确。如未配置 LLM，系统会返回默认提示语，不会崩溃。

**Q: 前端请求后端报 CORS 错误？**

确认后端 `CORS_ORIGINS` 包含前端地址。开发模式下默认包含 `http://localhost:5173`。

---

## 许可证

MIT
