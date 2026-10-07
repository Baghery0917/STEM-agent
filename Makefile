.PHONY: help up down build network \
        backend-install backend-run backend-test backend-lint backend-clean \
        frontend-install frontend-dev frontend-build \
        db-up db-down db-reset db-grant-reader migrate migrate-create db-seed clean

# 外部服务共享网络（教学策略 / 评价等通过它直连 stem-db）
network:
	docker network inspect stem-net >/dev/null 2>&1 || docker network create stem-net

# 帮助信息
help:
	@echo "Available commands:"
	@echo "  make up                - 启动所有服务（docker compose，自动 ensure stem-net）"
	@echo "  make down              - 停止所有服务"
	@echo "  make build             - 重建所有镜像"
	@echo ""
	@echo "  make backend-install   - 安装后端依赖"
	@echo "  make backend-run       - 启动后端开发服务器"
	@echo "  make backend-test      - 运行后端测试"
	@echo "  make backend-lint      - 后端代码检查"
	@echo ""
	@echo "  make frontend-install  - 安装前端依赖"
	@echo "  make frontend-dev      - 启动前端开发服务器"
	@echo "  make frontend-build    - 构建前端"
	@echo ""
	@echo "  make network           - 创建 stem-net 共享网络（供同机外部服务连库）"
	@echo "  make db-up             - 启动数据库容器"
	@echo "  make db-down           - 停止数据库容器"
	@echo "  make db-reset          - 重置数据库（删除数据卷并重建）"
	@echo "  make db-grant-reader   - 补建/刷新 strategy_reader 只读权限"
	@echo "  make migrate           - 运行数据库迁移"
	@echo "  make migrate-create    - 创建新迁移（需传 msg 参数）"
	@echo "  make db-seed           - 运行种子数据脚本"
	@echo ""
	@echo "  make clean             - 清理所有缓存文件"

# Docker Compose
up: network
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

# Backend
backend-install:
	cd backend && pip install -e .

backend-run:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

backend-test:
	cd backend && pytest -v

backend-lint:
	@echo "TODO: add lint command"

# Frontend
frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

# Database
db-up: network
	docker compose up -d db

db-down:
	docker compose down db

db-reset: network
	docker compose down -v
	docker compose up -d db

# 旧数据卷或迁移后新表缺 SELECT 时重跑（幂等）
db-grant-reader:
	@docker exec -i stem-db psql -U postgres -d stem_db < db/init/01-strategy-reader.sql
	@echo "strategy_reader grants applied"

migrate:
	cd backend && alembic upgrade head

migrate-create:
	@if [ -z "$(msg)" ]; then \
		echo "Usage: make migrate-create msg='description'"; \
		exit 1; \
	fi
	cd backend && alembic revision --autogenerate -m "$(msg)"

db-seed:
	cd backend && python seed_data.py

# 导入大学物理知识树与题库（3 册 44 章 314 节，3106 题）；加 EMBED=1 同时计算题目向量（需 backend/.env 的 LLM_API_KEY）
db-import-physics:
	cd backend && python scripts/import_physics.py $(if $(EMBED),--embed,)

# Clean
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
