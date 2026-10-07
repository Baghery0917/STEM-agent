import asyncio
import logging
from contextlib import asynccontextmanager, suppress
from collections.abc import AsyncGenerator

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, get_db_context
from app.api.v1.routers import admin_auth, admin_db, health, knowledge_structure, news, questions, student, teaching, practice
from app.api.v1.routers.admin_auth import require_admin
from app.services.teaching import TeachingService

logger = logging.getLogger(__name__)


async def _idle_session_sweeper() -> None:
    interval = settings.teaching_idle_sweep_interval_seconds
    while True:
        await asyncio.sleep(interval)
        try:
            async with get_db_context() as db:
                ended = await TeachingService(db).end_idle_sessions(
                    settings.teaching_idle_timeout_minutes,
                )
            if ended:
                logger.info("Auto-ended idle teaching sessions: %s", ended)
        except Exception:
            logger.exception("Idle session sweep failed")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    sweeper = asyncio.create_task(_idle_session_sweeper())
    yield
    sweeper.cancel()
    with suppress(asyncio.CancelledError):
        await sweeper
    await engine.dispose()


app = FastAPI(
    title="STEM API",
    description="STEM Backend API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(knowledge_structure.router, prefix="/api/v1", tags=["knowledge-structure"])
app.include_router(questions.router, prefix="/api/v1/questions", tags=["questions"])
app.include_router(student.router, prefix="/api/v1/students", tags=["students"])
app.include_router(teaching.router, prefix="/api/v1/teaching", tags=["teaching"])
app.include_router(practice.router, prefix="/api/v1/practice", tags=["practice"])
app.include_router(news.router, prefix="/api/v1/news", tags=["news"])
app.include_router(news.admin_router, prefix="/api/v1/admin/news", tags=["admin-news"])
app.include_router(admin_auth.router, prefix="/api/v1/admin", tags=["admin-auth"])
app.include_router(
    admin_db.router, prefix="/api/v1/admin/db", tags=["admin-db"],
    dependencies=[Depends(require_admin)],
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "STEM API", "version": "0.1.0"}
