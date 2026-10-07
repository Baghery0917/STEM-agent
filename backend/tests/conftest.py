import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text

from app.main import app
from app.database import Base, get_db


TEST_DATABASE_URL = "postgresql+asyncpg://physiq@127.0.0.1:5432/stem_db_test"

# Base.metadata.create_all 不会清理 PG ENUM；跨测试残留会导致 duplicate type 错误
_ENUM_TYPES = (
    "explainstyle",
    "persona",
    "teachingsessionstatus",
    "pipelinestatus",
    "messagerole",
    "messagetype",
    "sessionendreason",
    "emotionmode",
    "questiontype",
    "difficulty",
    "gender",
    "llmcalltype",
    "llmcallstatus",
)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        for enum_name in _ENUM_TYPES:
            await conn.execute(text(f"DROP TYPE IF EXISTS {enum_name} CASCADE"))
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        for enum_name in _ENUM_TYPES:
            await conn.execute(text(f"DROP TYPE IF EXISTS {enum_name} CASCADE"))

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
