"""Gallery schemas."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class GalleryItemResponse(BaseModel):
    """Gallery item response."""
    id: UUID
    file_type: str
    file_url: str
    thumbnail_url: str | None
    is_favorite: bool
    created_at: datetime
    generation_id: UUID
    prompt: str | None = None
    model_name: str | None = None

    class Config:
        from_attributes = True


class GalleryListResponse(BaseModel):
    """Gallery list response."""
    items: list[GalleryItemResponse]
    total: int


class GalleryToggleFavoriteResponse(BaseModel):
    """Toggle favorite response."""
    id: UUID
    is_favorite: bool
