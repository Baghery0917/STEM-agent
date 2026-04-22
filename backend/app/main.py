from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.api.v1.routers import admin_db, health, knowledge_structure, questions, student, teaching, practice


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yield
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
app.include_router(admin_db.router, prefix="/api/v1/admin/db", tags=["admin-db"])


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "STEM API", "version": "0.1.0"}
