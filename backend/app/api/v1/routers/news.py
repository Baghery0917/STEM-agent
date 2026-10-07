from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.routers.admin_auth import require_admin
from app.dependencies import DbSession
from app.schemas.news import NewsCreate, NewsResponse, NewsUpdate
from app.services.news import NewsService

router = APIRouter()
admin_router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("", response_model=list[NewsResponse])
async def list_public_news(db: DbSession, limit: int = Query(8, ge=1, le=50)) -> list[NewsResponse]:
    items = await NewsService(db).list(published_only=True, limit=limit)
    return [NewsResponse.model_validate(i) for i in items]


@admin_router.get("", response_model=list[NewsResponse])
async def list_all_news(db: DbSession, limit: int = Query(200, ge=1, le=500)) -> list[NewsResponse]:
    items = await NewsService(db).list(published_only=False, limit=limit)
    return [NewsResponse.model_validate(i) for i in items]


@admin_router.post("", response_model=NewsResponse, status_code=status.HTTP_201_CREATED)
async def create_news(data: NewsCreate, db: DbSession) -> NewsResponse:
    return NewsResponse.model_validate(await NewsService(db).create(data))


@admin_router.put("/{news_id}", response_model=NewsResponse)
async def update_news(news_id: int, data: NewsUpdate, db: DbSession) -> NewsResponse:
    item = await NewsService(db).update(news_id, data)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News not found")
    return NewsResponse.model_validate(item)


@admin_router.delete("/{news_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_news(news_id: int, db: DbSession) -> None:
    if not await NewsService(db).delete(news_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News not found")
