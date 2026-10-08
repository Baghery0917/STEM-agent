# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

STEM 智能教学系统。全栈项目：FastAPI 后端 + React 前端 + PostgreSQL/pgvector 数据库。

## 技术栈

- **后端**: Python 3.12 + FastAPI 0.109+ + SQLAlchemy 2.0+ (async)
- **前端**: React 18 + TypeScript + Vite
- **数据库**: PostgreSQL 16 + pgvector extension
- **迁移**: Alembic
- **验证**: Pydantic v2
- **测试**: pytest + pytest-asyncio
- **容器**: Docker + Docker Compose
- **依赖管理**: 后端使用 `pyproject.toml`（根目录 Makefile 统一管理命令）

## 项目结构

```
stem/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── main.py          # 应用入口
│   │   ├── config.py        # 配置管理
│   │   ├── database.py      # 异步数据库连接
│   │   ├── dependencies.py  # 依赖注入
│   │   ├── api/v1/routers/  # API 路由
│   │   ├── models/          # SQLAlchemy 模型
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # 业务逻辑
│   │   ├── llm/             # LLM 客户端
│   │   └── external/        # 外部服务调用
│   ├── tests/               # 测试文件
│   ├── alembic/             # 数据库迁移
│   └── pyproject.toml       # 后端依赖配置
│
├── frontend/                # React 前端
│   └── src/
│       ├── api/             # 接口封装
│       ├── pages/           # 页面
│       ├── components/      # 组件
│       ├── layouts/         # 布局
│       ├── stores/          # Zustand 状态
│       ├── hooks/           # 共享 Hook
│       ├── styles/          # 样式
│       └── utils/           # 工具函数
│
├── docs/                    # PRD / API / 外部对接契约
│   ├── external-interfaces.md   # 发给对接同事的总览（§0 只读连库）
│   └── design/db-external-access.md
├── examples/                # 外部服务 compose 示例（join stem-net）
├── db/init/                 # Postgres 初始化（含 strategy_reader）
├── docker-compose.yml       # 全栈编排（db 挂 stem-net）
├── Makefile                 # 常用命令（根目录统一管理）
└── CLAUDE.md
```

外部对接：策略/评价用 MCP；同机读库用 `stem-net` + `strategy_reader`（见 `docs/external-interfaces.md` §0），不要把库包成 MCP。

## 常用命令

根目录 Makefile 统一管理，优先使用 `make`：

```bash
# Docker 全栈
make up              # 启动所有服务（自动 ensure stem-net）
make down            # 停止所有服务

# 后端开发
make backend-install # 安装后端依赖（pip install -e .）
make backend-run     # 启动后端开发服务器
make backend-test    # 运行后端测试

# 前端开发
make frontend-install # 安装前端依赖
make frontend-dev    # 启动前端开发服务器

# 数据库
make network         # 创建 stem-net（供同机外部服务连库）
make db-up           # 启动数据库容器
make db-reset        # 重置数据库
make db-grant-reader # 补建/刷新 strategy_reader 只读权限
make migrate         # 运行迁移
make migrate-create msg="描述"  # 生成新迁移
make db-seed         # 运行种子数据脚本

# 清理缓存
make clean
```

如需在 backend 目录直接操作：

```bash
cd backend

# 运行迁移
alembic upgrade head

# 生成新迁移
alembic revision --autogenerate -m "description"

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 运行测试
pytest
```

## 代码规范

### 注释要求

- **不写多余注释**: 代码本身应该是自解释的，良好的命名已经说明了"What"
- **只写必要的注释**: 当以下情况时才写注释：
  1. 隐藏的约束或业务规则（"Why"而非"What"）
  2. 非常规做法或workaround
  3. 复杂算法的关键逻辑说明
  4. 外部系统接口的特殊说明
- **删除无意义注释**: 如果删除注释后代码依然清晰可读，就删掉它
- **避免文档字符串**: 不写多行 docstring，单行说明即可

### 示例

```python
# Good - 解释 WHY，不是 WHAT
# 业务规则：用户昵称唯一性检查忽略大小写（历史原因保留）
username: str = ...

# Bad - 注释废话
# 获取用户
user = get_user(id)

# Bad - 过时的文档字符串
def create_user(name: str):
    """
    创建用户

    Args:
        name: 用户名

    Returns:
        User: 用户对象
    """
    ...
```

### 其他规范

- 遵循 PEP 8
- 使用 type hints
- 异步优先 (async/await)
- 优先使用 `Annotated` 进行依赖注入

## 测试规范

### 测试要求

- **必须使用 `test-writer` subagent**: 编写测试时，必须使用 Agent 工具调用 `test-writer` subagent 来生成测试代码
- **Golden Path + 边界用例**: 每个功能至少测试正常流程和边界情况
- **测试文件位置**: `backend/tests/` 目录下，按模块命名（如 `test_users.py`）
- **异步测试**: 使用 `pytest-asyncio`，测试函数加 `@pytest.mark.asyncio`
