from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.volume import VolumeCreate, VolumeUpdate, VolumeResponse
from app.schemas.chapter import ChapterCreate, ChapterUpdate, ChapterResponse
from app.schemas.section import SectionCreate, SectionUpdate, SectionResponse
from app.services.volume import VolumeService
from app.services.chapter import ChapterService
from app.services.section import SectionService

router = APIRouter()

DbSession = Annotated[AsyncSession, Depends(get_db)]

# Volume endpoints


@router.post("/volumes", response_model=VolumeResponse, status_code=status.HTTP_201_CREATED)
async def create_volume(data: VolumeCreate, db: DbSession) -> VolumeResponse:
    service = VolumeService(db)
    volume = await service.create(data)
    return VolumeResponse.model_validate(volume)


@router.get("/volumes", response_model=list[VolumeResponse])
async def list_volumes(db: DbSession, skip: int = 0, limit: int = 100) -> list[VolumeResponse]:
    service = VolumeService(db)
    volumes = await service.get_all(skip=skip, limit=limit)
    return [VolumeResponse.model_validate(v) for v in volumes]


@router.get("/volumes/{volume_id}", response_model=VolumeResponse)
async def get_volume(volume_id: int, db: DbSession) -> VolumeResponse:
    service = VolumeService(db)
    volume = await service.get_by_id(volume_id)
    if not volume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Volume not found")
    return VolumeResponse.model_validate(volume)


@router.put("/volumes/{volume_id}", response_model=VolumeResponse)
async def update_volume(volume_id: int, data: VolumeUpdate, db: DbSession) -> VolumeResponse:
    service = VolumeService(db)
    volume = await service.update(volume_id, data)
    if not volume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Volume not found")
    return VolumeResponse.model_validate(volume)


@router.delete("/volumes/{volume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_volume(volume_id: int, db: DbSession) -> None:
    service = VolumeService(db)
    deleted = await service.delete(volume_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Volume not found")


@router.get("/volumes/{volume_id}/chapters", response_model=list[ChapterResponse])
async def get_volume_chapters(volume_id: int, db: DbSession) -> list[ChapterResponse]:
    service = VolumeService(db)
    volume = await service.get_by_id(volume_id)
    if not volume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Volume not found")
    chapters = await service.get_chapters(volume_id)
    return [ChapterResponse.model_validate(c) for c in chapters]


# Chapter endpoints


@router.post("/chapters", response_model=ChapterResponse, status_code=status.HTTP_201_CREATED)
async def create_chapter(data: ChapterCreate, db: DbSession) -> ChapterResponse:
    volume_service = VolumeService(db)
    volume = await volume_service.get_by_id(data.volume_id)
    if not volume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Volume not found")
    service = ChapterService(db)
    chapter = await service.create(data)
    return ChapterResponse.model_validate(chapter)


@router.get("/chapters", response_model=list[ChapterResponse])
async def list_chapters(db: DbSession, skip: int = 0, limit: int = 100) -> list[ChapterResponse]:
    service = ChapterService(db)
    chapters = await service.get_all(skip=skip, limit=limit)
    return [ChapterResponse.model_validate(c) for c in chapters]


@router.get("/chapters/{chapter_id}", response_model=ChapterResponse)
async def get_chapter(chapter_id: int, db: DbSession) -> ChapterResponse:
    service = ChapterService(db)
    chapter = await service.get_by_id(chapter_id)
    if not chapter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    return ChapterResponse.model_validate(chapter)


@router.put("/chapters/{chapter_id}", response_model=ChapterResponse)
async def update_chapter(chapter_id: int, data: ChapterUpdate, db: DbSession) -> ChapterResponse:
    if data.volume_id is not None:
        volume_service = VolumeService(db)
        volume = await volume_service.get_by_id(data.volume_id)
        if not volume:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Volume not found")
    service = ChapterService(db)
    chapter = await service.update(chapter_id, data)
    if not chapter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    return ChapterResponse.model_validate(chapter)


@router.delete("/chapters/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chapter(chapter_id: int, db: DbSession) -> None:
    service = ChapterService(db)
    deleted = await service.delete(chapter_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")


@router.get("/chapters/{chapter_id}/sections", response_model=list[SectionResponse])
async def get_chapter_sections(chapter_id: int, db: DbSession) -> list[SectionResponse]:
    service = ChapterService(db)
    chapter = await service.get_by_id(chapter_id)
    if not chapter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    sections = await service.get_sections(chapter_id)
    return [SectionResponse.model_validate(s) for s in sections]


# Section endpoints


@router.post("/sections", response_model=SectionResponse, status_code=status.HTTP_201_CREATED)
async def create_section(data: SectionCreate, db: DbSession) -> SectionResponse:
    chapter_service = ChapterService(db)
    chapter = await chapter_service.get_by_id(data.chapter_id)
    if not chapter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    service = SectionService(db)
    section = await service.create(data)
    return SectionResponse.model_validate(section)


@router.get("/sections", response_model=list[SectionResponse])
async def list_sections(db: DbSession, skip: int = 0, limit: int = 100) -> list[SectionResponse]:
    service = SectionService(db)
    sections = await service.get_all(skip=skip, limit=limit)
    return [SectionResponse.model_validate(s) for s in sections]


@router.get("/sections/{section_id}", response_model=SectionResponse)
async def get_section(section_id: int, db: DbSession) -> SectionResponse:
    service = SectionService(db)
    section = await service.get_by_id(section_id)
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
    return SectionResponse.model_validate(section)


@router.put("/sections/{section_id}", response_model=SectionResponse)
async def update_section(section_id: int, data: SectionUpdate, db: DbSession) -> SectionResponse:
    if data.chapter_id is not None:
        chapter_service = ChapterService(db)
        chapter = await chapter_service.get_by_id(data.chapter_id)
        if not chapter:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    service = SectionService(db)
    section = await service.update(section_id, data)
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
    return SectionResponse.model_validate(section)


@router.delete("/sections/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_section(section_id: int, db: DbSession) -> None:
    service = SectionService(db)
    deleted = await service.delete(section_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
