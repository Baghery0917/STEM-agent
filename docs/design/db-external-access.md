# 外部服务只读访问 STEM 数据库

同一台服务器上的外部服务（教学策略、评价处等）**直接连 PostgreSQL**，不要把数据库包成 MCP。

| 能力 | 协议 | 谁提供 |
|------|------|--------|
| 学生画像 / 会话等业务数据 | Postgres 5432（只读角色） | 本仓库 `stem-db` |
| 教学策略 / 评价点评 | MCP Streamable HTTP | 外部团队各自服务 |

主系统调外部服务用 MCP；外部服务读库用本页约定的连接串。MCP 契约见 [`../external-interfaces.md`](../external-interfaces.md)。

---

## 架构

```
本仓库 compose
  stem-frontend :80
  stem-backend  :8000  --SQL-->  stem-db :5432
                                    ^
                                    |  Docker 外部网络 stem-net
外部服务 compose（同机）            |
  strategy   MCP :8100  --SQL-------+
  evaluation MCP :8200  --SQL-------+
```

- 容器间：hostname `stem-db`，端口 `5432`
- 本机进程（不进 Docker）：`127.0.0.1:5432`（compose 已映射 host 端口）

---

## 一次性准备（部署侧）

```bash
# 创建共享网络（仅首次；make up / db-up 也会自动 ensure）
make network

# 启动库
make db-up
# 或全栈
make up

# 若数据卷是旧的、没有只读角色，补授权：
make db-grant-reader
```

验证：

```bash
docker network inspect stem-net
docker exec -it stem-db psql -U strategy_reader -d stem_db -c '\dt'
```

---

## 连接信息（发给对接同事）

| 项 | 值 |
|----|-----|
| Host（同 compose / 已 join `stem-net`） | `stem-db` |
| Host（宿主机进程） | `127.0.0.1` |
| Port | `5432` |
| Database | `stem_db` |
| User | `strategy_reader` |
| Password | `strategy_reader`（生产务必改，见下） |
| 权限 | 仅 `CONNECT` + `SELECT`（禁止写） |

连接串示例：

```text
# 外部服务容器内（推荐）
postgresql://strategy_reader:strategy_reader@stem-db:5432/stem_db

# 宿主机上跑的进程
postgresql://strategy_reader:strategy_reader@127.0.0.1:5432/stem_db
```

表含义与推荐查询面：[`../database_schema.md`](../database_schema.md)。策略 / 评价各自可读表清单见对应 MCP 契约。

---

## 外部服务 compose 片段

完整可复制文件：[`../../examples/external-service.compose.yml`](../../examples/external-service.compose.yml)

要点：

1. 声明 `stem-net` 为 `external: true`
2. 服务挂上该 network
3. 环境变量用上面的只读连接串
4. **不要**再起一个 Postgres；共用 `stem-db`

---

## 生产注意

1. **改密码**：改 `db/init/01-strategy-reader.sql` 与已有角色密码，并通过密钥注入外部服务，勿把默认口令提交到对方仓库。
2. **不要暴露 5432 到公网**：compose 的 `ports: "5432:5432"` 仅供本机联调；生产可改为只挂 `stem-net`、去掉 host publish，或绑定 `127.0.0.1:5432:5432`。
3. **新表权限**：init 脚本含 `ALTER DEFAULT PRIVILEGES`；若迁移后 `strategy_reader` 查不到新表，再跑一次 `make db-grant-reader`。
4. **只读约定**：外部服务不得用 `postgres` 超级用户连库。
