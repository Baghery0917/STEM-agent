-- 外部教学策略服务使用的只读角色。仅在数据卷首次初始化时执行。
-- 已有数据库补建: docker exec -i stem-db psql -U postgres -d stem_db < db/init/01-strategy-reader.sql
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'strategy_reader') THEN
    CREATE ROLE strategy_reader LOGIN PASSWORD 'strategy_reader';
  END IF;
END
$$;

GRANT CONNECT ON DATABASE stem_db TO strategy_reader;
GRANT USAGE ON SCHEMA public TO strategy_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO strategy_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO strategy_reader;
