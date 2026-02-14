"""Gallery routes."""

from uuid import UUID
from fastapi import APIRouter, HTTPException, status

from src.api.dependencies import CurrentUser, SessionDep
from src.api.schemas.common import MessageResponse
from src.api.schemas.gallery import (
    GalleryItemResponse,
    GalleryListResponse,
    GalleryToggleFavoriteResponse,
)
from src.config import settings
from src.core.exceptions import NotFoundError
from src.modules.gallery.service import GalleryService

router = APIRouter()


def _build_gallery_item_response(item, base_url: str) -> GalleryItemResponse:
    """Build gallery item response with URLs."""
    file_name = item.file_path.split("/")[-1]
    file_url = f"{base_url}/static/generations/{file_name}"
    
    thumbnail_url = None
    if item.thumbnail_path:
        thumb_name = item.thumbnail_path.split("/")[-1]
        thumbnail_url = f"{base_url}/static/generations/{thumb_name}"
    
    return GalleryItemResponse(
        id=item.id,
        file_type=item.file_type,
        file_url=file_url,
        thumbnail_url=thumbnail_url,
        is_favorite=item.is_favorite,
        created_at=item.created_at,
        generation_id=item.generation_id,
        prompt=item.generation.prompt if item.generation else None,
        model_name=item.generation.model.name if item.generation and item.generation.model else None,
    )


@router.get("", response_model=GalleryListResponse)
async def get_gallery(
    current_user: CurrentUser,
    session: SessionDep,
    offset: int = 0,
    limit: int = 50,
    file_type: str | None = None,
    favorites_only: bool = False,
) -> GalleryListResponse:
    """Get user's gallery."""
    service = GalleryService(session)
    
    items, total = await service.get_user_gallery(
        current_user.id,
        offset,
        limit,
        file_type,
        favorites_only,
    )
    
    return GalleryListResponse(
        items=[
            _build_gallery_item_response(item, settings.WEBAPP_URL)
            for item in items
        ],
        total=total,
    )


@router.post("/{item_id}/favorite", response_model=GalleryToggleFavoriteResponse)
async def toggle_favorite(
    item_id: UUID,
    current_user: CurrentUser,
    session: SessionDep,
) -> GalleryToggleFavoriteResponse:
    """Toggle gallery item favorite status."""
    service = GalleryService(session)
    
    try:
        new_status = await service.toggle_favorite(item_id, current_user.id)
        return GalleryToggleFavoriteResponse(
            id=item_id,
            is_favorite=new_status,
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )


@router.delete("/{item_id}", response_model=MessageResponse)
async def delete_gallery_item(
    item_id: UUID,
    current_user: CurrentUser,
    session: SessionDep,
) -> MessageResponse:
    """Delete gallery item."""
    service = GalleryService(session)
    
    try:
        await service.delete_item(item_id, current_user.id)
        return MessageResponse(message="Удалено")
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
